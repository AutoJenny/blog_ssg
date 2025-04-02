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
import datetime # Import datetime for timestamp

# --- Define Base Directory ---
# Assumes this script is in a 'scripts' subdirectory of the project root
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
# --- End Base Directory Definition ---

# --- Configuration ---
API_BASE_URL = "https://clan.com/clan/blog_api/"
API_USER = "blog"
API_KEY = "AC%7ef2a5A!24bd*E844a83f9F$49a02" # Consider moving to .env
# Use BASE_DIR to define paths relative to project root
IMAGE_LIBRARY_FILE = BASE_DIR / "_data/image_library.json"
WORKFLOW_STATUS_FILE = BASE_DIR / "_data/workflow_status.json" # Also need this for post ID
POSTS_DIR_NAME = "posts" # Relative name of posts dir
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
        # Run from BASE_DIR
        result = subprocess.run(
            ['npm', 'run', 'build'],
            capture_output=True, text=True, check=True,
            shell=sys.platform == 'win32', # Use shell=True on Windows if needed
            cwd=BASE_DIR # Ensure npm runs in the project root
        )
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

            # Remove HTML comments
            comments_found = 0
            for comment in content_element.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
                comments_found += 1
            if comments_found > 0:
                logging.info(f"Removed {comments_found} HTML comment(s).")

            # Rewrite image paths
            logging.info("Rewriting image paths to full URLs...")
            images_found = 0
            images_rewritten = 0
            for img_tag in content_element.find_all('img'):
                images_found += 1
                original_src = img_tag.get('src')
                if original_src and original_src.startswith(('/images/', 'images/')): # Allow for optional leading /
                    # Extract the unique filename
                    filename = os.path.basename(original_src)
                    new_src = IMAGE_PUBLIC_BASE_URL + filename
                    img_tag['src'] = new_src
                    images_rewritten += 1
                    logging.debug(f"  Rewrote img src: '{original_src}' -> '{new_src}'")
                elif original_src:
                     logging.debug(f"  Skipping img src (doesn't start with /images/): '{original_src}'")
            logging.info(f"Image path rewrite complete. Found: {images_found}, Rewritten: {images_rewritten}.")

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


def load_json_data(file_path):
    """Loads JSON data from a file path relative to BASE_DIR."""
    abs_file_path = BASE_DIR / file_path
    logging.info(f"Attempting to load JSON data from: {abs_file_path}")
    try:
        with open(abs_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"Successfully loaded JSON data from {abs_file_path}.")
            return data
    except FileNotFoundError:
        logging.warning(f"Data file not found: {abs_file_path}. Returning empty data.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {abs_file_path}. Please check its format.")
        return None
    except Exception as e:
        logging.error(f"Error loading data from {abs_file_path}: {e}")
        return None

def save_json_data(file_path, data):
    """Saves JSON data to a file path relative to BASE_DIR."""
    abs_file_path = BASE_DIR / file_path
    try:
        with open(abs_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Data saved to {abs_file_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving data to {abs_file_path}: {e}")
        return False

def upload_image_to_clan(image_id, image_library_data):
    """
    Uploads a single image identified by its ID using data from image_library.
    Parses URL from response message.
    Returns the relative path needed for thumbnail fields (e.g., /blog/image.jpg)
    or None on failure. Updates image_library_data IN MEMORY.
    """
    api_function = "uploadImage"
    url = f"{API_BASE_URL}{api_function}"
    logging.info(f"Attempting upload for Image ID: {image_id}...")

    img_entry = image_library_data.get(image_id)
    if not img_entry: logging.error(f"  Image ID '{image_id}' not found in image_library data."); return None
    source_details = img_entry.get("source_details", {})
    local_dir = source_details.get("local_dir")
    filename_local = source_details.get("filename_local")
    if not local_dir or not filename_local: logging.error(f"  Missing 'local_dir' or 'filename_local' for Image ID '{image_id}'."); return None

    full_local_path = BASE_DIR / local_dir.strip('/') / filename_local
    logging.info(f"  Found local path: {full_local_path}")
    if not os.path.exists(full_local_path): logging.error(f"  Image file not found at calculated path: {full_local_path}"); return None

    payload = {'api_user': API_USER, 'api_key': API_KEY}
    thumbnail_submit_path = None

    try:
        with open(full_local_path, 'rb') as f:
            files = {'image_file': (filename_local, f)} # Confirm 'image_file' key
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
                          # Update data in memory
                          image_library_data[image_id]["source_details"]["public_url"] = full_public_url
                          image_library_data[image_id]["source_details"]["uploaded_path_relative"] = thumbnail_submit_path
                     else: logging.error(f"  Extracted URL path '{path_part}' does not start with '{MEDIA_URL_PREFIX_EXPECTED}'")
                 else: logging.error("  Upload successful but could not parse URL from message.")
             else: logging.error(f"  Upload API response indicates failure or unexpected format: {response_data}")
        except json.JSONDecodeError: logging.error(f"  Failed to decode JSON: Status {response.status_code}. Body: {response.text[:500]}...")
    except requests.exceptions.HTTPError as e: logging.error(f"  HTTP error during image upload: {e}")
    except requests.exceptions.RequestException as e: logging.error(f"  Network error during image upload: {e}")
    except Exception as e: logging.error(f"  Unexpected error during image upload: {e}")

    return thumbnail_submit_path

def _prepare_api_args(post_metadata, image_library_data):
    """Helper function to prepare the common args dictionary. Uses image_library for thumbnails."""
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

    # Add Thumbnails using image_library data
    header_image_id = post_metadata.get('headerImageId')
    if header_image_id and header_image_id in image_library_data:
        thumbnail_server_path = image_library_data[header_image_id].get("source_details", {}).get("uploaded_path_relative")
        if thumbnail_server_path:
            args['list_thumbnail'] = thumbnail_server_path
            args['post_thumbnail'] = thumbnail_server_path
            logging.info(f"Set thumbnails to: {thumbnail_server_path}")
        else:
            logging.warning(f"No uploaded_path_relative found for header image ID: {header_image_id}. Thumbnails missing.")
            args['list_thumbnail'], args['post_thumbnail'] = None, None
    else:
        logging.warning(f"No headerImageId found in front matter or invalid ID. Thumbnails missing.")
        args['list_thumbnail'], args['post_thumbnail'] = None, None

    return args

def create_blog_post(post_metadata, post_content_html_path, image_library_data):
    """Calls the createPost API endpoint."""
    api_function = "createPost"
    url = f"{API_BASE_URL}{api_function}"
    logging.info("Preparing data for createPost API...")
    args = _prepare_api_args(post_metadata, image_library_data) # Pass image_library
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
    # ... (Error handling remains the same) ...
    except FileNotFoundError: logging.error(f"Error: HTML content file not found: {post_content_html_path}"); return False, None, "HTML content file not found"
    except requests.exceptions.RequestException as e:
        error_detail = f"Network error during createPost: {e}"
        if hasattr(e, 'response') and e.response is not None: error_detail += f"\nResponse status: {e.response.status_code}\nResponse body: {e.response.text[:500]}..."
        logging.error(error_detail); return False, None, error_detail
    except json.JSONDecodeError: error_msg = f"Failed to decode JSON response from createPost API: {response.text[:500]}..."; logging.error(error_msg); return False, None, error_msg
    except Exception as e: error_msg = f"Unexpected error during createPost: {e}"; logging.error(error_msg); return False, None, error_msg


def edit_blog_post(post_id, post_metadata, post_content_html_path, image_library_data):
    """Calls the editPost API endpoint."""
    api_function = "editPost"
    url = f"{API_BASE_URL}{api_function}"
    logging.info(f"Preparing data for editPost API (ID: {post_id})...")
    args = _prepare_api_args(post_metadata, image_library_data) # Pass image_library
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
    # ... (Error handling remains the same) ...
    except FileNotFoundError: logging.error(f"Error: HTML content file not found: {post_content_html_path}"); return False, "HTML content file not found"
    except requests.exceptions.RequestException as e:
        error_detail = f"Network error during editPost: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_detail += f"\nResponse status: {e.response.status_code}\nResponse body: {e.response.text[:500]}..."
            if e.response.status_code == 404 or (e.response.text and ("not found" in e.response.text.lower() or "invalid post id" in e.response.text.lower())): return False, "PostNotFound"
        logging.error(error_detail); return False, error_detail
    except json.JSONDecodeError: error_msg = f"Failed to decode JSON response from editPost API: {response.text[:500]}..."; logging.error(error_msg); return False, error_msg
    except Exception as e: error_msg = f"Unexpected error during editPost: {e}"; logging.error(error_msg); return False, error_msg

# load_json_data and save_json_data are now generic helpers
# main function needs adjusting to use them for both files

def main(md_relative_path_from_root, force_create):
    logging.info("--- Starting Blog Post Upload Script ---")
    md_file_abs_path = BASE_DIR / md_relative_path_from_root
    image_library_path = IMAGE_LIBRARY_FILE # Already absolute Path object
    workflow_status_path = WORKFLOW_STATUS_FILE # Already absolute Path object

    # 1. Verify Input MD File
    if not os.path.exists(md_file_abs_path): logging.error(f"Markdown file not found: {md_file_abs_path}"); sys.exit(1)

    # 2. Parse Front Matter
    logging.info(f"Parsing front matter from: {md_file_abs_path}")
    try:
        post = frontmatter.load(md_file_abs_path)
        metadata = post.metadata
        metadata['_input_path'] = md_file_abs_path # Store absolute path
        post_slug = Path(md_file_abs_path).stem
        logging.info(f"Loaded metadata for title: {metadata.get('title')} (Slug: {post_slug})")
    except Exception as e: logging.error(f"Error parsing front matter: {e}"); sys.exit(1)

    # 3. Load Workflow Status Data
    workflow_data = load_json_data(workflow_status_path)
    if workflow_data is None: sys.exit(1)
    if post_slug not in workflow_data: workflow_data[post_slug] = {"stages": {}} # Init if needed

    # 4. Load Image Library Data
    image_library_data = load_json_data(image_library_path)
    if image_library_data is None: sys.exit(1)

    # 5. Run Eleventy Build
    if not run_eleventy_build(): sys.exit(1)

    # 6. Define Built HTML Path & Extract Content
    built_html_path = BASE_DIR / '_site' / post_slug / 'index.html'
    if not os.path.exists(built_html_path): logging.error(f"Built HTML file not found after build: {built_html_path}"); sys.exit(1)
    html_content = extract_html_content(built_html_path, HTML_CONTENT_SELECTOR)
    if html_content is None: sys.exit(1)

    temp_html_file = None; script_success = False
    images_uploaded = False # Flag to track if uploads were attempted
    try:
        # 7. Create Temporary HTML File
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".html", encoding='utf-8') as temp_f:
            temp_f.write(html_content); temp_html_file = temp_f.name
            logging.info(f"Saved extracted HTML content to temporary file: {temp_html_file}")

        # 8. Gather and Upload Images
        image_ids_to_upload = []
        if metadata.get('headerImageId'): image_ids_to_upload.append(metadata['headerImageId'])
        for section in metadata.get('sections', []):
            if section.get('imageId'): image_ids_to_upload.append(section['imageId'])
        if metadata.get('conclusion', {}).get('imageId'): image_ids_to_upload.append(metadata['conclusion']['imageId'])

        logging.info(f"Found {len(image_ids_to_upload)} image IDs referenced in post.")
        image_library_modified = False # Track if image library needs saving
        if image_ids_to_upload:
             images_uploaded = True # Mark that we are processing uploads
             logging.info("--- Starting Image Uploads ---")
             for image_id in image_ids_to_upload:
                 # Pass the current state of image_library_data to the upload function
                 # It will update this dictionary in memory if upload succeeds
                 relative_path = upload_image_to_clan(image_id, image_library_data)
                 if relative_path:
                      image_library_modified = True # Mark that data changed
                 else:
                      logging.warning(f"Failed to upload image ID: {image_id}. Post might have missing images/thumbnails.")
             logging.info("--- Finished Image Uploads ---")

        # 9. Save updated image library data IF changes were made during upload
        if image_library_modified:
             if not save_json_data(image_library_path, image_library_data):
                  logging.error("CRITICAL: Failed to save updated image library data after uploads!")
                  # Decide whether to proceed without saving - risky
                  # sys.exit(1)

        # 10. Decide: Create or Edit?
        existing_post_id = workflow_data.get(post_slug, {}).get("stages", {}).get("publishing_clancom", {}).get("post_id") if not force_create else None

        api_error_msg = None # Store potential API error message

        if existing_post_id:
            logging.info(f"Found existing Post ID {existing_post_id} for slug '{post_slug}'. Attempting to edit.")
            # Pass the current (potentially updated by uploads) image_library_data
            success, error_msg = edit_blog_post(existing_post_id, metadata, temp_html_file, image_library_data)
            if success: script_success = True
            else: api_error_msg = error_msg # Store error for status update

        else:
            if force_create: logging.warning(f"Forcing creation for slug '{post_slug}'.")
            logging.info(f"No existing Post ID found for slug '{post_slug}'. Attempting to create.")
            # Pass the current (potentially updated by uploads) image_library_data
            success, new_post_id, error_msg = create_blog_post(metadata, temp_html_file, image_library_data)
            if success:
                script_success = True
                if new_post_id:
                     # Ensure structure exists before assigning
                     if 'stages' not in workflow_data[post_slug]: workflow_data[post_slug]['stages'] = {}
                     if 'publishing_clancom' not in workflow_data[post_slug]['stages']: workflow_data[post_slug]['stages']['publishing_clancom'] = {}
                     workflow_data[post_slug]['stages']['publishing_clancom']['post_id'] = new_post_id
                     logging.info(f"Storing new Post ID {new_post_id} for slug '{post_slug}'.")
                else: logging.warning("Post creation succeeded but no Post ID was returned/extracted.")
            else:
                 api_error_msg = error_msg # Store error for status update

        # 11. Update Workflow Status File (After create/edit attempt)
        update_time = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + 'Z'
        if 'stages' not in workflow_data[post_slug]: workflow_data[post_slug]['stages'] = {}
        if 'publishing_clancom' not in workflow_data[post_slug]['stages']: workflow_data[post_slug]['stages']['publishing_clancom'] = {}

        workflow_data[post_slug]['last_updated'] = update_time
        workflow_data[post_slug]['stages']['publishing_clancom']['last_publish_attempt'] = update_time

        if script_success:
             workflow_data[post_slug]['stages']['publishing_clancom']['status'] = 'complete'
             workflow_data[post_slug]['stages']['publishing_clancom']['last_error'] = None
        else:
             workflow_data[post_slug]['stages']['publishing_clancom']['status'] = 'error'
             workflow_data[post_slug]['stages']['publishing_clancom']['last_error'] = api_error_msg or "Unknown error during publish step."
             # Handle PostNotFound specifically if editing failed because it was deleted
             if api_error_msg == "PostNotFound" and existing_post_id:
                 logging.error(f"Edit failed: Post ID {existing_post_id} not found on server.");
                 logging.warning(f"Clearing stale post ID for '{post_slug}'.")
                 workflow_data[post_slug]['stages']['publishing_clancom'].pop("post_id", None) # Remove bad ID

        if not save_json_data(workflow_status_path, workflow_data):
             logging.error("Failed to save updated workflow status data!")


    finally:
        # 12. Clean up temporary file
        if temp_html_file and os.path.exists(temp_html_file):
            logging.info(f"Deleting temporary HTML file: {temp_html_file}")
            os.remove(temp_html_file)

    if script_success:
         logging.info("--- Script finished successfully! ---")
    else:
         logging.error("--- Script finished with errors. ---")
         sys.exit(1) # Exit with error code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Eleventy blog post to clan.com API.")
    parser.add_argument(
        "markdown_file",
        help="Relative path (from project root) to the post's Markdown file (e.g., posts/kilt-evolution.md)."
    )
    parser.add_argument(
        "--force-create",
        action="store_true",
        help="Force creation attempt even if ID exists locally."
    )
    args = parser.parse_args()
    main(args.markdown_file, args.force_create)