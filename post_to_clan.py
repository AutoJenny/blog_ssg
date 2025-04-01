import os
import sys
import subprocess
import json
import requests
import frontmatter
from bs4 import BeautifulSoup, Comment # Import Comment
import tempfile
import logging
from pathlib import Path
import re
import argparse
from urllib.parse import urlparse, urlunparse

# --- Configuration ---
API_BASE_URL = "https://clan.com/clan/blog_api/"
API_USER = "blog"
API_KEY = "AC%7ef2a5A!24bd*E844a83f9F$49a02" # Consider moving to .env
SYNDICATION_DATA_FILE = "_data/syndication.json"
DEFAULT_POST_MD_RELATIVE_PATH = "posts/kilt-evolution.md"
HTML_CONTENT_SELECTOR = "article.blog-post"
# --- UPDATED Category IDs ---
DEFAULT_CATEGORY_IDS = [14, 15] # !!! STILL PLACEHOLDER - NEEDS FINAL MAPPING LOGIC !!!
IMAGE_PUBLIC_BASE_URL = "https://static.clan.com/media/blog/"
MEDIA_URL_PREFIX_EXPECTED = "/media/blog/"
MEDIA_URL_SUBMIT_PREFIX = "/blog/"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---

def run_eleventy_build():
    """Runs 'npm run build' and checks for errors."""
    logging.info("Running 'npm run build'...")
    try:
        result = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True, check=True, shell=sys.platform == 'win32')
        logging.info("Eleventy build completed successfully.")
        return True
    except FileNotFoundError:
        logging.error("Error: 'npm' command not found. Is Node.js installed and in PATH?")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during Eleventy build (Return Code: {e.returncode}):")
        logging.error("STDOUT:\n" + e.stdout)
        logging.error("STDERR:\n" + e.stderr)
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during build: {e}")
        return False

def extract_html_content(built_html_path, selector):
    """
    Extracts inner HTML content using BeautifulSoup, removes HTML comments,
    and rewrites relative image paths to full static.clan.com URLs.
    """
    logging.info(f"Extracting content from {built_html_path} using selector '{selector}'...")
    try:
        with open(built_html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')

        content_element = soup.select_one(selector)
        if content_element:
            logging.info("Found content element.")

            # --- Remove HTML comments ---
            comments_found = 0
            for comment in content_element.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract() # Remove the comment from the soup
                comments_found += 1
            if comments_found > 0:
                logging.info(f"Removed {comments_found} HTML comment(s).")
            # --- End Remove Comments ---

            # Rewrite image paths
            logging.info("Rewriting image paths to full URLs...")
            images_found = 0
            images_rewritten = 0
            for img_tag in content_element.find_all('img'):
                images_found += 1
                original_src = img_tag.get('src')
                if original_src and original_src.startswith('/images/'):
                    filename = os.path.basename(original_src)
                    new_src = IMAGE_PUBLIC_BASE_URL + filename
                    img_tag['src'] = new_src
                    images_rewritten += 1
                    logging.debug(f"  Rewrote img src: '{original_src}' -> '{new_src}'")
                elif original_src:
                     logging.debug(f"  Skipping img src (doesn't start with /images/ or isn't relative): '{original_src}'")
            logging.info(f"Image path rewrite complete. Found: {images_found}, Rewritten: {images_rewritten}.")

            # Extract the modified inner HTML
            inner_html = ''.join(str(child) for child in content_element.contents)
            return inner_html
        else:
            logging.error(f"Error: Could not find element matching selector '{selector}' in {built_html_path}")
            return None
    except FileNotFoundError:
        logging.error(f"Error: Built HTML file not found: {built_html_path}")
        return None
    except Exception as e:
        logging.error(f"Error parsing, modifying, or extracting HTML from file {built_html_path}: {e}")
        return None

def upload_image_to_clan(local_image_path):
    """
    Uploads a single image. Handles URL in response message.
    Returns the relative path needed for thumbnail fields (e.g., /blog/image.jpg)
    or None on failure.
    """
    api_function = "uploadImage"
    url = f"{API_BASE_URL}{api_function}"
    logging.info(f"Uploading image: {local_image_path}...")
    if not os.path.exists(local_image_path): logging.error(f"  Image file not found: {local_image_path}"); return None
    payload = {'api_user': API_USER, 'api_key': API_KEY}
    thumbnail_submit_path = None
    try:
        with open(local_image_path, 'rb') as f:
            upload_filename = os.path.basename(local_image_path)
            files = {'image_file': (upload_filename, f)} # Confirm key
            verify_ssl = True
            if not verify_ssl: import urllib3; urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning); logging.warning("  SSL verification disabled!")
            response = requests.post(url, data=payload, files=files, timeout=60, verify=verify_ssl)
            response.raise_for_status()
        try:
             response_data = response.json()
             logging.debug(f"  Upload API JSON Response: {response_data}")
             success_message = response_data.get("message", "")
             if "File uploaded successfully:" in success_message:
                 url_match = re.search(r"File uploaded successfully:\s*(https://\S+)", success_message)
                 if url_match:
                     full_public_url = url_match.group(1).strip()
                     logging.info(f"  Raw success message URL: {full_public_url}")
                     path_part = urlparse(full_public_url).path
                     if path_part.startswith(MEDIA_URL_PREFIX_EXPECTED):
                          image_filename_part = path_part[len(MEDIA_URL_PREFIX_EXPECTED):]
                          thumbnail_submit_path = MEDIA_URL_SUBMIT_PREFIX + image_filename_part.lstrip('/')
                          logging.info(f"  Upload successful. Relative path for API thumbnails: {thumbnail_submit_path}")
                     else:
                          logging.error(f"  Extracted URL path '{path_part}' does not start with expected prefix '{MEDIA_URL_PREFIX_EXPECTED}'")
                 else: logging.error("  Upload successful but could not parse URL from message.")
             else: logging.error(f"  Upload API response indicates failure or unexpected format: {response_data}")
        except json.JSONDecodeError: logging.error(f"  Failed to decode JSON response from image upload API. Status: {response.status_code}. Body: {response.text[:500]}...")
    except requests.exceptions.HTTPError as e: logging.error(f"  HTTP error during image upload: {e}")
    except requests.exceptions.RequestException as e: logging.error(f"  Network error during image upload: {e}")
    except Exception as e: logging.error(f"  Unexpected error during image upload: {e}")
    return thumbnail_submit_path

def _prepare_api_args(post_metadata):
    """Helper function to prepare the common args dictionary for create/edit. Excludes post_id."""
    args = {}
    args['title'] = post_metadata.get('title', 'Untitled Post')
    slug = Path(post_metadata['_input_path']).stem
    args['url_key'] = slug
    args['short_content'] = post_metadata.get('summary', '')
    logging.info(f"Using raw summary for short_content.")
    args['status'] = 2
    args['meta_title'] = post_metadata.get('metaTitle', args['title'])
    args['meta_description'] = post_metadata.get('description', '')

    # TODO: Implement actual mapping from post_metadata['tags'] to Category IDs
    logging.warning(f"Using Hardcoded Category IDs: {DEFAULT_CATEGORY_IDS}. Update is needed!")
    args['categories'] = DEFAULT_CATEGORY_IDS

    tags = post_metadata.get('tags', [])
    api_tags = ",".join([tag for tag in tags if tag.lower() != 'post'])
    args['meta_tags'] = api_tags
    return args

def _add_thumbnails_to_args(args, post_metadata, uploaded_image_map):
     """Helper to add thumbnail paths to the args dict."""
     header_image_local_src = post_metadata.get('headerImage', {}).get('src')
     thumbnail_server_path = uploaded_image_map.get(header_image_local_src)
     if thumbnail_server_path:
        args['list_thumbnail'] = thumbnail_server_path
        args['post_thumbnail'] = thumbnail_server_path
        logging.info(f"Set thumbnails to: {thumbnail_server_path}")
     else:
        logging.warning(f"Could not find uploaded server path for header image: {header_image_local_src}. Thumbnails will be missing.")
        args['list_thumbnail'] = None
        args['post_thumbnail'] = None
     return args

def create_blog_post(post_metadata, post_content_html_path, uploaded_image_paths):
    """Calls the createPost API endpoint."""
    api_function = "createPost"
    url = f"{API_BASE_URL}{api_function}"
    logging.info("Preparing data for createPost API...")
    args = _prepare_api_args(post_metadata)
    args = _add_thumbnails_to_args(args, post_metadata, uploaded_image_paths)
    payload = {'api_user': API_USER, 'api_key': API_KEY, 'json_args': json.dumps(args)}
    logging.debug(f"API Args (JSON encoded): {payload['json_args']}")
    try:
        with open(post_content_html_path, 'rb') as f:
            files = {'html_file': (os.path.basename(post_content_html_path), f)}
            verify_ssl = True
            if not verify_ssl: logging.warning("  SSL verification disabled!")
            logging.info(f"Calling createPost API: {url}")
            response = requests.post(url, data=payload, files=files, timeout=120, verify=verify_ssl)
            response.raise_for_status()
        response_data = response.json()
        logging.info("--- createPost API Response ---"); logging.info(json.dumps(response_data, indent=2))
        if response_data.get("status") == "success":
             message = response_data.get("message", ""); post_id = None
             id_match = re.search(r'(\d+)$', message);
             if id_match: post_id = int(id_match.group(1))
             logging.info(f"Blog post created successfully! Message: {message}. Extracted ID: {post_id}")
             return True, post_id, None
        else:
             error_msg = response_data.get("message", "Unknown error"); logging.error(f"API Error: Failed to create blog post: {error_msg}")
             return False, None, error_msg
    except FileNotFoundError: logging.error(f"Error: HTML content file not found: {post_content_html_path}"); return False, None, "HTML content file not found"
    except requests.exceptions.RequestException as e:
        error_detail = f"Network error during createPost: {e}"
        if hasattr(e, 'response') and e.response is not None: error_detail += f"\nResponse status: {e.response.status_code}\nResponse body: {e.response.text[:500]}..."
        logging.error(error_detail); return False, None, error_detail
    except json.JSONDecodeError: error_msg = f"Failed to decode JSON response from createPost API: {response.text[:500]}..."; logging.error(error_msg); return False, None, error_msg
    except Exception as e: error_msg = f"Unexpected error during createPost: {e}"; logging.error(error_msg); return False, None, error_msg

def edit_blog_post(post_id, post_metadata, post_content_html_path, uploaded_image_paths):
    """Calls the editPost API endpoint."""
    api_function = "editPost"
    url = f"{API_BASE_URL}{api_function}"
    logging.info(f"Preparing data for editPost API (ID: {post_id})...")
    args = _prepare_api_args(post_metadata)
    args = _add_thumbnails_to_args(args, post_metadata, uploaded_image_paths)
    args['post_id'] = post_id
    payload = {'api_user': API_USER, 'api_key': API_KEY, 'json_args': json.dumps(args)}
    logging.debug(f"API Args (JSON encoded): {payload['json_args']}")
    try:
        with open(post_content_html_path, 'rb') as f:
            files = {'html_file': (os.path.basename(post_content_html_path), f)}
            verify_ssl = True
            if not verify_ssl: logging.warning("  SSL verification disabled!")
            logging.info(f"Calling editPost API: {url}")
            response = requests.post(url, data=payload, files=files, timeout=120, verify=verify_ssl)
            response.raise_for_status()
        response_data = response.json()
        logging.info("--- editPost API Response ---"); logging.info(json.dumps(response_data, indent=2))
        if response_data.get("status") == "success":
             message = response_data.get("message", f"Post ID {post_id} updated."); logging.info(f"Blog post edited successfully! Message: {message}")
             return True, None
        else:
             error_msg = response_data.get("message", "Unknown error")
             if "invalid post id" in error_msg.lower() or "post not found" in error_msg.lower(): logging.error(f"API Error: Post ID {post_id} not found on server."); return False, "PostNotFound"
             else: logging.error(f"API Error: Failed to edit blog post: {error_msg}"); return False, error_msg
    except FileNotFoundError: logging.error(f"Error: HTML content file not found: {post_content_html_path}"); return False, "HTML content file not found"
    except requests.exceptions.RequestException as e:
        error_detail = f"Network error during editPost: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_detail += f"\nResponse status: {e.response.status_code}\nResponse body: {e.response.text[:500]}..."
            if e.response.status_code == 404 or (e.response.text and ("not found" in e.response.text.lower() or "invalid post id" in e.response.text.lower())): return False, "PostNotFound"
        logging.error(error_detail); return False, error_detail
    except json.JSONDecodeError: error_msg = f"Failed to decode JSON response from editPost API: {response.text[:500]}..."; logging.error(error_msg); return False, error_msg
    except Exception as e: error_msg = f"Unexpected error during editPost: {e}"; logging.error(error_msg); return False, error_msg

def load_syndication_data(file_path):
    """Loads the JSON data file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError: logging.warning(f"Syndication data file not found: {file_path}."); return {}
    except json.JSONDecodeError: logging.error(f"Error decoding JSON from {file_path}."); return None
    except Exception as e: logging.error(f"Error loading syndication data: {e}"); return None

def save_syndication_data(file_path, data):
    """Saves the JSON data file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2); logging.info(f"Syndication data saved to {file_path}"); return True
    except Exception as e: logging.error(f"Error saving syndication data: {e}"); return False

def main(md_relative_path, force_create):
    logging.info("--- Starting Blog Post Upload Script ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_file_abs_path = os.path.join(script_dir, md_relative_path)
    data_file_abs_path = os.path.join(script_dir, SYNDICATION_DATA_FILE)
    # Load Metadata
    logging.info(f"Parsing front matter from: {md_file_abs_path}")
    try: post = frontmatter.load(md_file_abs_path); metadata = post.metadata; metadata['_input_path'] = md_file_abs_path; post_slug = Path(md_file_abs_path).stem; logging.info(f"Loaded metadata for title: {metadata.get('title')} (Slug: {post_slug})")
    except Exception as e: logging.error(f"Error parsing front matter: {e}"); sys.exit(1)
    # Load Syndication Data
    syndication_data = load_syndication_data(data_file_abs_path)
    if syndication_data is None: sys.exit(1)
    if post_slug not in syndication_data: syndication_data[post_slug] = {}
    # Build Site
    if not run_eleventy_build(): sys.exit(1)
    # Get HTML path and extract content
    built_html_path = os.path.join(script_dir, '_site', post_slug, 'index.html')
    if not os.path.exists(built_html_path): logging.error(f"Built HTML file not found: {built_html_path}"); sys.exit(1)
    html_content = extract_html_content(built_html_path, HTML_CONTENT_SELECTOR)
    if html_content is None: sys.exit(1)

    temp_html_file = None; script_success = False
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".html", encoding='utf-8') as temp_f:
            temp_f.write(html_content); temp_html_file = temp_f.name; logging.info(f"Saved extracted HTML content to temporary file: {temp_html_file}")
        # Upload Images
        image_local_paths = []
        if metadata.get('headerImage', {}).get('src'): image_local_paths.append(metadata['headerImage']['src'])
        for section in metadata.get('sections', []):
            if section.get('image', {}).get('src'): image_local_paths.append(section['image']['src'])
        uploaded_image_map = {}
        logging.info("--- Starting Image Uploads ---")
        for local_src in image_local_paths:
            full_local_path = os.path.normpath(os.path.join(script_dir, local_src.lstrip('/')))
            server_path = upload_image_to_clan(full_local_path)
            if server_path: uploaded_image_map[local_src] = server_path
            else: logging.warning(f"Failed to upload image: {full_local_path}.")
        logging.info("--- Finished Image Uploads ---"); logging.debug(f"Uploaded Image Map: {uploaded_image_map}")
        # Create or Edit
        existing_post_id = syndication_data[post_slug].get("clan_com_post_id") if not force_create else None
        if existing_post_id:
            logging.info(f"Found existing Post ID {existing_post_id} for slug '{post_slug}'. Attempting to edit.")
            success, error_msg = edit_blog_post(existing_post_id, metadata, temp_html_file, uploaded_image_map)
            if success: script_success = True
            elif error_msg == "PostNotFound":
                 logging.error(f"Edit failed: Post ID {existing_post_id} not found on server."); logging.warning(f"Clearing stale post ID for '{post_slug}'.")
                 syndication_data[post_slug].pop("clan_com_post_id", None)
                 if save_syndication_data(data_file_abs_path, syndication_data): logging.info("Stale ID removed. Re-run script to create.")
                 else: logging.error("Failed to save data after removing stale ID.")
                 script_success = False
            else: logging.error(f"Edit post failed: {error_msg}")
        else:
            if force_create: logging.warning(f"Forcing creation for slug '{post_slug}'.")
            logging.info(f"No existing Post ID found for slug '{post_slug}'. Attempting to create.")
            success, new_post_id, error_msg = create_blog_post(metadata, temp_html_file, uploaded_image_map)
            if success:
                script_success = True
                if new_post_id:
                     syndication_data[post_slug]["clan_com_post_id"] = new_post_id; logging.info(f"Storing new Post ID {new_post_id} for slug '{post_slug}'.")
                     if not save_syndication_data(data_file_abs_path, syndication_data): logging.error("Failed to save data with new post ID!")
                else: logging.warning("Post creation succeeded but no Post ID was returned/extracted.")
            else:
                 if error_msg and "same Url Key" in error_msg: logging.error(f"Create failed: URL Key '{post_slug}' already exists, but no local ID stored."); logging.error(f"Suggestion: Find ID in admin, add to {SYNDICATION_DATA_FILE}, rerun.")
                 else: logging.error(f"Create post failed: {error_msg}")
    finally:
        if temp_html_file and os.path.exists(temp_html_file): logging.info(f"Deleting temporary HTML file: {temp_html_file}"); os.remove(temp_html_file)

    if script_success: logging.info("--- Script finished successfully! ---")
    else: logging.error("--- Script finished with errors. ---"); sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Eleventy blog post to clan.com API.")
    parser.add_argument("markdown_file", nargs='?', default=DEFAULT_POST_MD_RELATIVE_PATH, help=f"Relative path to the post's Markdown file (default: {DEFAULT_POST_MD_RELATIVE_PATH}).")
    parser.add_argument("--force-create", action="store_true", help="Force creation attempt even if ID exists locally.")
    args = parser.parse_args()
    main(args.markdown_file, args.force_create)