#!/usr/bin/env python3

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
import datetime
from dotenv import load_dotenv # Import dotenv

# --- Define Base Directory ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
logging.info(f"Calculated BASE_DIR: {BASE_DIR}")

# --- Configuration Loading ---
def load_config():
    """Load configuration from environment variables."""
    dotenv_path_proj_root = BASE_DIR / '.env'
    load_dotenv(dotenv_path=dotenv_path_proj_root)
    load_dotenv() # Also try current dir

    config = {
        "api_base_url": os.getenv("CLAN_API_BASE_URL", "https://clan.com/clan/blog_api/"),
        "api_user": os.getenv("CLAN_API_USER", "blog"),
        "api_key": os.getenv("CLAN_API_KEY"), # MUST be in .env
        "image_library_file": BASE_DIR / os.getenv("IMAGE_LIBRARY_FILENAME", "_data/image_library.json"),
        "workflow_status_file": BASE_DIR / os.getenv("WORKFLOW_STATUS_FILENAME", "_data/workflow_status.json"),
        "posts_dir_name": os.getenv("POSTS_DIR_NAME", "posts"), # e.g., "posts"
        "html_content_selector": os.getenv("HTML_CONTENT_SELECTOR", "article.blog-post"), # CSS selector for main content
        "html_back_link_selector": os.getenv("HTML_BACK_LINK_SELECTOR", "nav.post-navigation-top"), # ** CORRECTED SELECTOR **
        "image_public_base_url": os.getenv("IMAGE_PUBLIC_BASE_URL", "https://static.clan.com/media/blog/"), # URL prefix for rewritten img src
        "media_url_prefix_expected": os.getenv("MEDIA_URL_PREFIX_EXPECTED", "/media/blog/"), # Expected path prefix in uploaded image URLs
        "media_url_submit_prefix": os.getenv("MEDIA_URL_SUBMIT_PREFIX", "/blog/"), # Path prefix to use when submitting thumbnail URLs to API
        "default_category_ids": [int(x) for x in os.getenv("DEFAULT_CATEGORY_IDS", "14,15").split(',') if x], # Comma-separated IDs in .env
        "base_dir": BASE_DIR
    }

    # Ensure trailing slash for base url
    if config["api_base_url"] and not config["api_base_url"].endswith('/'):
        config["api_base_url"] += '/'

    # API key is essential
    if not config["api_key"]:
        logging.error("CRITICAL: Missing CLAN_API_KEY in environment/.env file")
        sys.exit(1)

    logging.info(f"Configuration loaded. API Base: {config['api_base_url']}, User: {config['api_user']}")
    return config
# --- End Configuration ---


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - SCRIPT - %(message)s', stream=sys.stderr)
# --- End Logging Setup ---

# --- Global Config Variable ---
# Load config once at the start
CONFIG = load_config()
# --- End Global Config ---

# --- Helper Functions ---

def run_eleventy_build():
    """Runs 'npm run build' and checks for errors."""
    logging.info("Running 'npm run build'...")
    try:
        result = subprocess.run(
            ['npm', 'run', 'build'],
            capture_output=True, text=True, check=True,
            shell=sys.platform == 'win32',
            cwd=CONFIG["base_dir"] # Use loaded base_dir
        )
        logging.info("Eleventy build completed successfully.")
        # Optionally log stdout/stderr from build if needed for debugging
        # logging.debug("Build STDOUT:\n" + result.stdout)
        # logging.debug("Build STDERR:\n" + result.stderr)
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
        logging.error(f"An unexpected error occurred during build: {e}", exc_info=True)
        return False

# --- Add header_image_filename argument ---
def extract_html_content(built_html_path, header_image_filename=None):
    """
    Extracts inner HTML content using BeautifulSoup, removes HTML comments,
    removes the specified 'Back' link element, removes the header image figure,
    and rewrites relative image paths. Uses config for selector and image base URL.

    Args:
        built_html_path (Path): Path to the built HTML file.
        header_image_filename (str, optional): The filename (e.g., "kilt-evolution_header.webp")
                                                of the header image to find and remove its figure.
                                                Defaults to None.
    """
    # Get selectors and config from global CONFIG dictionary
    selector = CONFIG["html_content_selector"] # e.g., "article.blog-post"
    back_link_selector = CONFIG["html_back_link_selector"] # e.g., "nav.post-navigation-top"
    image_public_base_url = CONFIG["image_public_base_url"]

    logging.info(f"Extracting content from {built_html_path} using selector '{selector}'...")
    try:
        with open(built_html_path, 'r', encoding='utf-8') as f:
            try:
                soup = BeautifulSoup(f, 'lxml')
            except ImportError:
                logging.warning("lxml not found, using html.parser.")
                soup = BeautifulSoup(f, 'html.parser')

        # --- Find the main content container element first ---
        content_element = soup.select_one(selector)
        if not content_element:
            logging.error(f"Error: Could not find main content element matching selector '{selector}' in {built_html_path}")
            return None
        logging.info(f"Found main content element: <{content_element.name} class='{content_element.get('class', '')}'>")

        # --- Perform removals ON THE FULL SOUP or WITHIN CONTENT ELEMENT as appropriate ---

        # 1. Remove "Back" link element (might be outside the main content element)
        if back_link_selector:
             back_link_element = soup.select_one(back_link_selector) # Search whole document
             if back_link_element:
                 logging.info(f"Removing element matching back link selector '{back_link_selector}'.")
                 back_link_element.decompose()
             else:
                 logging.warning(f"Could not find element matching back link selector '{back_link_selector}'.")
        else:
             logging.debug("No back link selector configured, skipping removal.")

        # --- ADDED: Remove Header Image Figure ---
        if header_image_filename:
            logging.info(f"Attempting to find and remove figure containing image: '{header_image_filename}'")
            # Find the specific img tag using a lambda to check if src ENDS with the filename
            # This assumes the src in the built HTML might have prefixes but ends consistently
            img_tag_to_remove = content_element.find('img', src=lambda s: s and s.endswith(header_image_filename))

            if img_tag_to_remove:
                # Find the parent figure tag
                figure_to_remove = img_tag_to_remove.find_parent('figure', class_='section-image') # Be specific if possible
                if figure_to_remove:
                    logging.info(f"Found and removing parent <figure class='section-image'> for header image.")
                    figure_to_remove.decompose()
                else:
                    # Fallback or stricter error? Maybe just warn if figure isn't found.
                    logging.warning(f"Found header img tag, but couldn't find its parent <figure class='section-image'> to remove.")
                    # Optionally, remove just the img tag as a less ideal fallback:
                    # logging.info("Removing only the header img tag as figure not found.")
                    # img_tag_to_remove.decompose()
            else:
                logging.warning(f"Could not find header img tag with src ending in '{header_image_filename}' within the content element.")
        else:
            logging.info("No header_image_filename provided, skipping header image figure removal.")
        # --- END: Remove Header Image Figure ---


        # --- Process the main content element ---
        # Remove HTML comments within the content element
        comments_found = 0
        for comment in content_element.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
            comments_found += 1
        if comments_found > 0:
            logging.info(f"Removed {comments_found} HTML comment(s) from content.")

        # Rewrite other image paths within the content element
        logging.info("Rewriting remaining image paths within content to full URLs...")
        images_found = 0
        images_rewritten = 0
        for img_tag in content_element.find_all('img'): # Re-find all remaining images
            images_found += 1
            original_src = img_tag.get('src')
            if original_src and original_src.startswith(('/images/', 'images/')):
                filename = os.path.basename(original_src)
                # Construct full URL, avoid double slashes
                new_src = image_public_base_url.rstrip('/') + '/' + filename
                img_tag['src'] = new_src
                images_rewritten += 1
                logging.debug(f"  Rewrote img src: '{original_src}' -> '{new_src}'")
            elif original_src:
                 logging.debug(f"  Skipping img src (doesn't appear relative or already processed?): '{original_src}'")
        logging.info(f"Image path rewrite complete. Found remaining: {images_found}, Rewritten: {images_rewritten}.")

        # Extract the final processed inner HTML (without header figure)
        inner_html = ''.join(str(child) for child in content_element.contents)
        return inner_html

    except FileNotFoundError:
        logging.error(f"Error: Built HTML file not found: {built_html_path}")
        return None
    except Exception as e:
        logging.error(f"Error parsing, modifying, or extracting HTML from file {built_html_path}: {e}", exc_info=True)
        return None

def load_json_data(file_path):
    """Loads JSON data from the given Path object."""
    logging.info(f"Attempting to load JSON data from: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"Successfully loaded JSON data from {file_path.name}.")
            return data
    except FileNotFoundError:
        logging.warning(f"Data file not found: {file_path}. Returning empty data.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}. Please check its format.")
        return None # Indicate critical error
    except Exception as e:
        logging.error(f"Error loading data from {file_path}: {e}", exc_info=True)
        return None

def save_json_data(file_path, data):
    """Saves JSON data to the given Path object."""
    logging.info(f"Attempting to save JSON data to: {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2) # Use indent=2 for consistency
        logging.info(f"Data saved successfully to {file_path.name}")
        return True
    except Exception as e:
        logging.error(f"Error saving data to {file_path}: {e}", exc_info=True)
        return False

def upload_image_to_clan(image_id, image_library_data):
    """
    Uploads a single image identified by its ID using data from image_library.
    Updates image_library_data IN MEMORY with public URL and relative path.
    Returns the relative path needed for thumbnail fields (e.g., /blog/image.jpg) or None on failure.
    """
    api_function = "uploadImage"
    url = CONFIG["api_base_url"] + api_function
    api_user = CONFIG["api_user"]
    api_key = CONFIG["api_key"]
    media_url_prefix_expected = CONFIG["media_url_prefix_expected"]
    media_url_submit_prefix = CONFIG["media_url_submit_prefix"]
    base_dir = CONFIG["base_dir"]

    logging.info(f"Attempting upload for Image ID: {image_id}...")

    img_entry = image_library_data.get(image_id)
    if not img_entry: logging.error(f"  Image ID '{image_id}' not found in image_library data."); return None
    source_details = img_entry.get("source_details", {})
    local_dir = source_details.get("local_dir")
    filename_local = source_details.get("filename_local")
    if not local_dir or not filename_local: logging.error(f"  Missing 'local_dir' or 'filename_local' for Image ID '{image_id}'."); return None

    full_local_path = base_dir / local_dir.strip('/') / filename_local
    logging.info(f"  Checking local path: {full_local_path}")
    if not os.path.exists(full_local_path): logging.error(f"  Image file not found at calculated path: {full_local_path}"); return None

    payload = {'api_user': api_user, 'api_key': api_key}
    thumbnail_submit_path = None # Variable to store the result

    try:
        with open(full_local_path, 'rb') as f:
            # Key for file upload likely 'image_file' based on PHP example structure? Confirm needed.
            files = {'image_file': (filename_local, f)}
            logging.info(f"  Uploading '{filename_local}'...")
            # Consider adding timeout (e.g., timeout=60)
            response = requests.post(url, data=payload, files=files, timeout=60, verify=True) # Keep verify=True unless specific reason otherwise
            response.raise_for_status()

        # Process response
        try:
             response_data = response.json()
             logging.debug(f"  Upload API JSON Response: {response_data}")
             success_message = response_data.get("message", "")
             # Check for specific success message pattern
             if "File uploaded successfully:" in success_message:
                 url_match = re.search(r"File uploaded successfully:\s*(https://\S+)", success_message)
                 if url_match:
                     full_public_url = url_match.group(1).strip()
                     logging.info(f"  Extracted public URL: {full_public_url}")
                     path_part = urlparse(full_public_url).path
                     # Verify extracted path starts with expected prefix
                     if path_part.startswith(media_url_prefix_expected):
                          image_filename_part = path_part[len(media_url_prefix_expected):]
                          # Construct the path needed for thumbnail API fields
                          thumbnail_submit_path = media_url_submit_prefix.rstrip('/') + '/' + image_filename_part.lstrip('/')
                          logging.info(f"  SUCCESS: Upload complete. Relative path for API: {thumbnail_submit_path}")
                          # Update data IN MEMORY
                          if "source_details" not in image_library_data[image_id]: image_library_data[image_id]["source_details"] = {}
                          image_library_data[image_id]["source_details"]["public_url"] = full_public_url
                          image_library_data[image_id]["source_details"]["uploaded_path_relative"] = thumbnail_submit_path
                     else: logging.error(f"  Upload success message URL path '{path_part}' does not start with expected '{media_url_prefix_expected}'")
                 else: logging.error("  Upload successful message received, but could not parse URL from message text.")
             else: logging.error(f"  Upload API response indicates failure or unexpected message format: {response_data}")
        except json.JSONDecodeError: logging.error(f"  Failed to decode JSON response after upload: Status {response.status_code}. Body: {response.text[:500]}...")

    except requests.exceptions.HTTPError as e: logging.error(f"  HTTP error during image upload for '{image_id}': {e.response.status_code} - {e.response.text[:200]}...")
    except requests.exceptions.RequestException as e: logging.error(f"  Network error during image upload for '{image_id}': {e}")
    except Exception as e: logging.error(f"  Unexpected error during image upload for '{image_id}': {e}", exc_info=True)

    return thumbnail_submit_path # Return the path needed for thumbnails or None


def _prepare_api_args(post_metadata, image_library_data):
    """Helper function to prepare the common args dictionary. Uses image_library for thumbnails."""
    args = {}
    # --- Required fields ---
    args['title'] = post_metadata.get('title')
    # Use front matter 'url_key' if present, otherwise derive slug from input path stored earlier
    args['url_key'] = post_metadata.get('url_key', Path(post_metadata['_input_path']).stem)

    if not args['title']: raise ValueError("Metadata missing 'title'")
    if not args['url_key']: raise ValueError("Metadata missing 'url_key' and could not derive slug")

    # --- Optional fields based on PHP example & front matter ---
    # Use description or summary from front matter if short_content isn't explicitly set
    args['short_content'] = post_metadata.get('short_content', post_metadata.get('description', post_metadata.get('summary', '')))
    args['status'] = post_metadata.get('status', 2) # Default to enabled=2
    args['categories'] = post_metadata.get('categories', CONFIG["default_category_ids"]) # Use front matter list or default from config

    # Meta fields - default reasonably if not present
    args['meta_title'] = post_metadata.get('metaTitle', post_metadata.get('meta_title', args['title']))
    args['meta_tags'] = post_metadata.get('metaTags', post_metadata.get('meta_tags', ','.join([t for t in post_metadata.get('tags', []) if t and t.lower() != 'post']))) # Join tags, skip empty/ 'post'
    args['meta_description'] = post_metadata.get('metaDescription', post_metadata.get('meta_description', post_metadata.get('description', args['short_content'])))

    # --- Thumbnail Handling ---
    # Get paths from image_library_data (updated in memory by upload function)
    list_thumb_path, post_thumb_path = None, None
    header_image_id = post_metadata.get('headerImageId')

    if header_image_id:
        img_entry = image_library_data.get(header_image_id)
        if img_entry:
            uploaded_path = img_entry.get("source_details", {}).get("uploaded_path_relative")
            if uploaded_path:
                list_thumb_path = uploaded_path
                post_thumb_path = uploaded_path # Use same for both unless specified otherwise
                logging.info(f"Using uploaded path '{uploaded_path}' for list and post thumbnails.")
            else:
                logging.warning(f"Header image ID '{header_image_id}' found, but no 'uploaded_path_relative' present after upload attempt. Thumbnails will be missing.")
        else:
            logging.warning(f"Header image ID '{header_image_id}' specified but not found in image library data. Thumbnails will be missing.")
    else:
        # Allow explicit override from front matter
        list_thumb_path = post_metadata.get('list_thumbnail')
        post_thumb_path = post_metadata.get('post_thumbnail')
        if list_thumb_path or post_thumb_path:
             logging.info("Using explicit list/post_thumbnail paths from front matter.")
        else:
             logging.warning("No headerImageId or explicit thumbnail paths found in front matter. Thumbnails will be missing.")

    args['list_thumbnail'] = list_thumb_path
    args['post_thumbnail'] = post_thumb_path

    # Add publish date if available
    publish_date = post_metadata.get('date')
    if isinstance(publish_date, (datetime.date, datetime.datetime)):
        args['publish_date_iso'] = publish_date.isoformat()

    # Filter out None values before returning if API requires it
    args_filtered = {k: v for k, v in args.items() if v is not None}
    return args_filtered


def _call_api(api_function, args, temp_html_file_path=None):
    """Generic function to call createPost or editPost API."""
    url = CONFIG["api_base_url"] + api_function
    api_user = CONFIG["api_user"]
    api_key = CONFIG["api_key"]

    payload = {
        'api_user': (None, api_user),
        'api_key': (None, api_key),
        'json_args': (None, json.dumps(args))
    }

    files_payload = None
    file_handle = None
    if temp_html_file_path:
        if not Path(temp_html_file_path).is_file():
            raise FileNotFoundError(f"Temporary HTML file not found: {temp_html_file_path}")
        try:
            # Open file handle here, pass it to requests, close in finally
            file_handle = open(temp_html_file_path, 'rb')
            files_payload = {'html_file': (os.path.basename(temp_html_file_path), file_handle, 'text/html')}
        except Exception as e:
             logging.error(f"Error opening temporary HTML file {temp_html_file_path}: {e}")
             if file_handle: file_handle.close() # Ensure close on error
             raise # Re-raise

    logging.info(f"Calling API function '{api_function}' at {url} for post '{args.get('url_key', args.get('post_id'))}'")
    logging.debug(f"API Args (JSON encoded): {payload['json_args']}")

    response_data = None
    error_detail = None
    status_code = None
    try:
        response = requests.post(url, data=payload, files=files_payload, timeout=120, verify=True)
        status_code = response.status_code
        response.raise_for_status() # Check for HTTP errors

        response_data = response.json() # Try to parse JSON
        logging.info(f"--- {api_function} API Response ---")
        logging.info(json.dumps(response_data, indent=2))
        return True, response_data, None # Success

    except requests.exceptions.HTTPError as e:
        error_detail = f"HTTP error calling {api_function}: {e}"
        if e.response is not None:
            error_detail += f"\nStatus: {e.response.status_code}\nResponse body: {e.response.text[:500]}..."
            try: response_data = e.response.json() # Try parsing error response
            except json.JSONDecodeError: pass
        logging.error(error_detail)
        return False, response_data, error_detail # Return parsed error if possible

    except requests.exceptions.RequestException as e:
        error_detail = f"Network error calling {api_function}: {e}"
        logging.error(error_detail)
        return False, None, error_detail

    except json.JSONDecodeError:
        error_detail = f"Failed to decode JSON response from {api_function} API. Status: {status_code}. Response: {response.text[:500]}..."
        logging.error(error_detail)
        return False, None, error_detail

    except Exception as e:
        error_detail = f"Unexpected error during {api_function}: {e}"
        logging.error(error_detail, exc_info=True)
        return False, None, error_detail

    finally:
        if file_handle:
            file_handle.close() # Ensure file handle is closed

def create_blog_post(post_metadata, post_content_html_path, image_library_data):
    """Calls the createPost API endpoint using the generic helper."""
    try:
        args = _prepare_api_args(post_metadata, image_library_data)
    except ValueError as e:
         logging.error(f"Failed to prepare API args for createPost: {e}")
         return False, None, str(e)

    success, response_data, error_detail = _call_api("createPost", args, post_content_html_path)

    if success and response_data and response_data.get("status") == "success":
        message = response_data.get("message", "")
        post_id = None
        id_match = re.search(r'(\d+)$', message) # Extract ID from success message
        if id_match: post_id = int(id_match.group(1))
        logging.info(f"Blog post created successfully! Message: {message}. Extracted ID: {post_id}")
        return True, post_id, None
    else:
        error_msg = error_detail or (response_data.get("message", "Unknown error") if response_data else "Unknown API error")
        logging.error(f"API Error: Failed to create blog post: {error_msg}")
        return False, None, error_msg


def edit_blog_post(post_id, post_metadata, post_content_html_path, image_library_data):
    """Calls the editPost API endpoint using the generic helper."""
    try:
        args = _prepare_api_args(post_metadata, image_library_data)
        args['post_id'] = post_id # Add post_id required for editing
    except ValueError as e:
         logging.error(f"Failed to prepare API args for editPost: {e}")
         return False, str(e) # Only need success/error for edit

    success, response_data, error_detail = _call_api("editPost", args, post_content_html_path)

    if success and response_data and response_data.get("status") == "success":
        message = response_data.get("message", f"Post ID {post_id} updated.")
        logging.info(f"Blog post edited successfully! Message: {message}")
        return True, None
    else:
        error_msg = error_detail or (response_data.get("message", "Unknown error") if response_data else "Unknown API error")
        # Check for specific "not found" errors
        if "invalid post id" in error_msg.lower() or "post not found" in error_msg.lower():
            logging.error(f"API Error: Post ID {post_id} not found on server.")
            return False, "PostNotFound" # Special error code
        else:
            logging.error(f"API Error: Failed to edit blog post ID {post_id}: {error_msg}")
            return False, error_msg

# --- Main Execution Logic ---
# ... (Keep all imports, helper functions, config loading etc. from the previous "Old Script Logic" version) ...

# --- Main Execution Logic ---
def main(md_relative_path_from_root, force_create=False):
    logging.info(f"--- Starting Blog Post Upload Script ---")
    logging.info(f"Target Markdown: {md_relative_path_from_root}, Force Create: {force_create}")

    base_dir = CONFIG["base_dir"]
    posts_dir_name = CONFIG["posts_dir_name"] # Needed for input path validation
    image_library_path = CONFIG["image_library_file"]
    workflow_status_path = CONFIG["workflow_status_file"]

    md_file_abs_path = base_dir / md_relative_path_from_root

    # 1. Verify Input MD File
    if not md_file_abs_path.is_file():
        logging.error(f"Markdown file not found: {md_file_abs_path}")
        print(f"ERROR: Markdown file not found: {md_file_abs_path}", file=sys.stderr)
        sys.exit(1)

    # 2. Parse Front Matter
    logging.info(f"Parsing front matter from: {md_file_abs_path}")
    try:
        post_fm = frontmatter.load(md_file_abs_path)
        metadata = post_fm.metadata
        metadata['_input_path'] = str(md_file_abs_path)
        post_slug = Path(md_file_abs_path).stem
        logging.info(f"Loaded metadata for title: '{metadata.get('title')}' (Slug: {post_slug})")
    except Exception as e:
        logging.error(f"Error parsing front matter: {e}", exc_info=True)
        print(f"ERROR: Failed parsing front matter for {md_file_abs_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Load Workflow Status Data
    workflow_data = load_json_data(workflow_status_path)
    if workflow_data is None:
        print(f"ERROR: Could not load workflow status file: {workflow_status_path}", file=sys.stderr)
        sys.exit(1)
    if post_slug not in workflow_data:
        workflow_data[post_slug] = {"stages": {}}

    # 4. Load Image Library Data
    image_library_data = load_json_data(image_library_path)
    if image_library_data is None:
        print(f"ERROR: Could not load image library file: {image_library_path}", file=sys.stderr)
        sys.exit(1)

    # 5. Run Eleventy Build
    if not run_eleventy_build():
        print(f"ERROR: Eleventy build failed. See log for details.", file=sys.stderr)
        sys.exit(1)

    # 6. Define Built HTML Path & Extract Content
    # --- CORRECTED BUILT HTML PATH CALCULATION ---
    # Assumes Eleventy config now produces output at _site/<slug>/index.html
    # based on corrected permalink: "/{{ page.fileSlug }}/index.html" in posts data file.
    built_html_relative_path = Path("_site") / post_slug / "index.html"
    # --- END PATH CALCULATION ---

    built_html_path = base_dir / built_html_relative_path


    if not built_html_path.is_file():
        logging.error(f"Built HTML file not found after build at expected path: {built_html_path}")
        print(f"ERROR: Expected HTML file not found after build: {built_html_path}", file=sys.stderr)
        site_dir_path = base_dir / '_site'
        if site_dir_path.is_dir():
             logging.error(f"Contents of {site_dir_path}: {list(site_dir_path.iterdir())}") # Log contents to help if it still fails
        sys.exit(1)

    html_content = extract_html_content(built_html_path) # Uses config for selector
    if html_content is None:
        print(f"ERROR: Failed to extract HTML content from {built_html_path}. See log.", file=sys.stderr)
        sys.exit(1)

    temp_html_file = None
    script_success = False
    api_error_msg = None
    image_library_modified = False

    try:
        # 7. Create Temporary HTML File (Keep existing logic)
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".html", encoding='utf-8') as temp_f:
                temp_f.write(html_content)
                temp_html_file = temp_f.name
            logging.info(f"Saved extracted HTML content to temporary file: {temp_html_file}")
        except Exception as e:
             logging.error(f"Failed to create or write temporary HTML file: {e}", exc_info=True)
             temp_html_file = None
             raise

           # 8. Gather and Upload Images <-- *** APPLY FIX HERE ***
        image_ids_to_upload = []
        logging.info("Gathering image IDs from front matter...")
        # Get header image ID
        header_id = metadata.get('headerImageId')
        if header_id:
            image_ids_to_upload.append(header_id)
            logging.debug(f"  Found headerImageId: {header_id}")

        # Get image IDs from sections
        for i, section in enumerate(metadata.get('sections', [])):
            section_id = section.get('imageId')
            if section_id:
                image_ids_to_upload.append(section_id)
                logging.debug(f"  Found imageId in sections[{i}]: {section_id}")

        # Get image ID from conclusion
        conclusion_id = metadata.get('conclusion', {}).get('imageId')
        if conclusion_id:
            image_ids_to_upload.append(conclusion_id)
            logging.debug(f"  Found imageId in conclusion: {conclusion_id}")

        # Ensure IDs are unique
        image_ids_to_upload = list(dict.fromkeys(image_ids_to_upload))
        logging.info(f"Found {len(image_ids_to_upload)} unique image IDs to process: {image_ids_to_upload}")

        # --- The rest of the image upload loop remains the same ---
        image_library_modified = False
        if image_ids_to_upload:
             logging.info(f"--- Starting Image Uploads for {len(image_ids_to_upload)} image(s) ---")
             current_image_library_state = image_library_data.copy()
             any_upload_succeeded = False
             for image_id in image_ids_to_upload:
                 relative_path = upload_image_to_clan(image_id, current_image_library_state)
                 if relative_path:
                      image_library_modified = True
                      any_upload_succeeded = True
                 else:
                      logging.warning(f"Failed to upload image ID: {image_id}. Post might have missing images/thumbnails.")

             if image_library_modified:
                  image_library_data = current_image_library_state # Update main dict with changes
             logging.info("--- Finished Image Uploads ---")
        else:
             logging.info("No image IDs found in front matter to upload.")


        # 9. Save updated image library data IF changes were made (Keep existing logic)
        if image_library_modified:
             logging.info("Saving updated image library data...")
             if not save_json_data(image_library_path, image_library_data):
                  logging.error("CRITICAL: Failed to save updated image library data after uploads!")

        # 10. Decide: Create or Edit? (Keep existing logic)
        existing_post_id = None
        if not force_create:
             existing_post_id = workflow_data.get(post_slug, {}).get("stages", {}).get("publishing_clancom", {}).get("post_id")

        if existing_post_id:
            logging.info(f"Found existing Post ID {existing_post_id}. Attempting to edit.")
            success, error_msg = edit_blog_post(existing_post_id, metadata, temp_html_file, image_library_data)
            if success: script_success = True
            else: api_error_msg = error_msg

        else:
            if force_create: logging.warning(f"Option --force-create used. Attempting creation.")
            else: logging.info(f"No existing Post ID found for slug '{post_slug}'. Attempting to create.")
            success, new_post_id, error_msg = create_blog_post(metadata, temp_html_file, image_library_data)
            if success:
                script_success = True
                if new_post_id:
                     # Ensure structure exists
                     if 'stages' not in workflow_data[post_slug]: workflow_data[post_slug]['stages'] = {}
                     if 'publishing_clancom' not in workflow_data[post_slug]['stages']: workflow_data[post_slug]['stages']['publishing_clancom'] = {}
                     workflow_data[post_slug]['stages']['publishing_clancom']['post_id'] = new_post_id
                     logging.info(f"Storing new Post ID {new_post_id} for slug '{post_slug}'.")
                else: logging.warning("Post creation succeeded but no Post ID was returned/extracted.")
            else:
                 api_error_msg = error_msg

        # 11. Update Workflow Status File (Keep existing logic)
        logging.info("Updating workflow status file...")
        update_time = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + 'Z'
        # Ensure structure exists
        if 'stages' not in workflow_data[post_slug]: workflow_data[post_slug]['stages'] = {}
        if 'publishing_clancom' not in workflow_data[post_slug]['stages']: workflow_data[post_slug]['stages']['publishing_clancom'] = {}

        workflow_data[post_slug]['last_updated'] = update_time
        workflow_data[post_slug]['stages']['publishing_clancom']['last_publish_attempt'] = update_time

        if script_success:
             workflow_data[post_slug]['stages']['publishing_clancom']['status'] = 'complete'
             workflow_data[post_slug]['stages']['publishing_clancom']['last_error'] = None
             logging.info(f"Workflow status updated to 'complete' for '{post_slug}'.")
        else:
             workflow_data[post_slug]['stages']['publishing_clancom']['status'] = 'error'
             final_error_message = api_error_msg or "Unknown error during publish step (check logs)."
             workflow_data[post_slug]['stages']['publishing_clancom']['last_error'] = final_error_message
             logging.info(f"Workflow status updated to 'error' for '{post_slug}'. Error: {final_error_message}")
             if api_error_msg == "PostNotFound" and existing_post_id:
                 logging.error(f"Edit failed: Post ID {existing_post_id} not found on server.")
                 logging.warning(f"Clearing stale post ID for '{post_slug}' in workflow status.")
                 workflow_data[post_slug]['stages']['publishing_clancom'].pop("post_id", None)

        if not save_json_data(workflow_status_path, workflow_data):
             logging.error("CRITICAL: Failed to save updated workflow status data!")
             print(f"ERROR: Failed to save updated workflow status data to {workflow_status_path}", file=sys.stderr)

    finally:
        # 12. Clean up temporary file
        if temp_html_file and os.path.exists(temp_html_file):
            try:
                logging.info(f"Deleting temporary HTML file: {temp_html_file}")
                os.remove(temp_html_file)
            except OSError as e:
                 logging.error(f"Error deleting temporary file {temp_html_file}: {e}")

    if script_success:
         logging.info("--- Script finished successfully! ---")
         print(f"SUCCESS: Post '{post_slug}' processed and submitted successfully.")
    else:
         logging.error("--- Script finished with errors. ---")
         sys.exit(1)

# --- Argument Parser and Main Call ---
# (Keep the __main__ block with argparse setup and validation as before)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build, process, and upload Eleventy blog post to clan.com API.")
    parser.add_argument(
        "markdown_file",
        help="Relative path (from project root) to the post's Markdown file (e.g., posts/kilt-evolution.md)."
    )
    parser.add_argument(
        "--force-create",
        action="store_true",
        help="Force creation attempt even if an existing post ID is found locally."
    )
    args = parser.parse_args()

    # Use CONFIG directly now as it's loaded globally
    posts_dir_name_config = CONFIG["posts_dir_name"]
    # Basic validation of input path format
    if not Path(args.markdown_file).parts or '..' in Path(args.markdown_file).parts:
         print(f"ERROR: Invalid markdown file path specified: {args.markdown_file}", file=sys.stderr)
         sys.exit(1)
    if not args.markdown_file.startswith(posts_dir_name_config + os.sep):
         print(f"ERROR: Markdown file path must be relative from project root and start with '{posts_dir_name_config}/'. Provided: {args.markdown_file}", file=sys.stderr)
         sys.exit(1)

    main(args.markdown_file, args.force_create)