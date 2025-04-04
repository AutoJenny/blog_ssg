# /Users/nickfiddes/Code/projects/blog_ssg/app.py

from flask import Flask, render_template, jsonify, request, url_for, send_from_directory
import os
import json
from pathlib import Path
import frontmatter
import logging
import subprocess
import sys
import datetime # Already imported, good.
import re 

# --- Configuration Constants ---
BASE_DIR = Path(__file__).resolve().parent
POSTS_DIR_NAME = "posts"
DATA_DIR_NAME = "_data"
DATA_DIR = BASE_DIR / DATA_DIR_NAME
WORKFLOW_STATUS_FILE = "workflow_status.json" # Main file for post status tracking
IMAGE_LIBRARY_FILE = "image_library.json"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['BASE_DIR_STR'] = str(BASE_DIR) # Make base dir accessible in templates

# --- Add Static Route for Images (Development Only) ---
# Serve files from the 'images' directory at the '/images' URL path
IMAGES_DIR = BASE_DIR / 'images' # Define the images directory path
@app.route('/images/<path:filename>')
def serve_images(filename):
    logging.debug(f"Serving image: {filename} from {IMAGES_DIR}")
    # Ensure the path requested is safe and within the intended directory
    # send_from_directory handles this reasonably well
    return send_from_directory(IMAGES_DIR, filename)

# --- Helper Functions ---

def load_json_data(file_path: Path):
    """Loads JSON data from the given absolute file path."""
    logging.info(f"Attempting to load JSON data from: {file_path}")
    if not file_path.is_file():
        logging.warning(f"JSON data file not found: {file_path}. Returning empty data.")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"Successfully loaded JSON data from {file_path.name}.")
            return data
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}.")
        return None # Indicate critical error
    except Exception as e:
        logging.error(f"Unexpected error loading JSON data from {file_path}: {e}")
        return None # Indicate critical error

def save_json_data(file_path: Path, data: dict):
    """Saves the given dictionary as JSON to the specified absolute file path."""
    logging.info(f"Attempting to save JSON data to: {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4) # Use indent for readability
        logging.info(f"Successfully saved JSON data to {file_path.name}.")
        return True
    except IOError as e:
        logging.error(f"IOError saving JSON data to {file_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error saving JSON data to {file_path}: {e}")
        return False

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main admin interface page, loading post data."""
    logging.info("Processing index route '/'...")
    posts_list = []
    posts_dir_path = BASE_DIR / POSTS_DIR_NAME # Correct path construction
    workflow_status_path = DATA_DIR / WORKFLOW_STATUS_FILE # Correct path construction

    workflow_data = load_json_data(workflow_status_path)
    if workflow_data is None:
        logging.error("Critical error loading workflow data, post status will be unavailable.")
        workflow_data = {}
    elif not workflow_data:
        logging.warning(f"Workflow data file '{WORKFLOW_STATUS_FILE}' not found. Statuses unavailable.")

    try:
        logging.info(f"Scanning directory: {posts_dir_path}")
        if not posts_dir_path.is_dir():
             logging.error(f"Posts directory not found: {posts_dir_path}")
             raise FileNotFoundError

        for filename in sorted(os.listdir(posts_dir_path)): # Sort for consistent order
            if filename.endswith(".md"):
                file_path = posts_dir_path / filename
                logging.debug(f"Processing file: {filename}")
                try:
                    post_fm = frontmatter.load(file_path)
                    metadata = post_fm.metadata
                    slug = Path(filename).stem
                    title = metadata.get('title', f"Untitled ({slug})")

                    # Get clan.com status from workflow data
                    post_workflow_data = workflow_data.get(slug, {})
                    clan_com_stage = post_workflow_data.get('stages', {}).get('publishing_clancom', {})
                    clan_com_post_id = clan_com_stage.get('post_id')
                    clan_com_status_val = clan_com_stage.get('status', 'pending')

                    # Determine display status
                    if clan_com_post_id and clan_com_status_val == 'complete':
                        clan_com_status_display = f"Published (ID: {clan_com_post_id})"
                    elif clan_com_status_val == 'error':
                         error_msg = clan_com_stage.get('last_error', 'Unknown Error')
                         clan_com_status_display = f"Error: {error_msg[:50]}" # Show snippet of error
                         if len(error_msg) > 50: clan_com_status_display += "..."
                    else:
                        clan_com_status_display = "Not Published / Pending"

                    posts_list.append({'slug': slug, 'title': title, 'clan_com_status': clan_com_status_display})
                except Exception as e:
                    logging.error(f"Error processing markdown file {filename}: {e}", exc_info=True) # Add traceback info

        # Optionally sort by title or other criteria if needed, slug sort already done by sorted(os.listdir(...))
        # posts_list.sort(key=lambda p: p['title'])
        logging.info(f"Found and processed {len(posts_list)} posts.")

    except FileNotFoundError:
        logging.error(f"Posts directory not found: {posts_dir_path}")
    except Exception as e:
        logging.error(f"Error listing or processing posts directory: {e}", exc_info=True)

    return render_template(
            'admin_index.html',
            posts=posts_list,
            config=app.config
           )


@app.route('/admin/post/<string:slug>')
def view_post_detail(slug):
    """Displays the detailed workflow management page for a single post."""
    logging.info(f"Processing detail route '/admin/post/{slug}'...")
    md_file_path = BASE_DIR / POSTS_DIR_NAME / f"{slug}.md"
    workflow_status_path = DATA_DIR / WORKFLOW_STATUS_FILE
    image_library_path = DATA_DIR / IMAGE_LIBRARY_FILE

    metadata = {}
    status_data = {"stages": {}}
    images_detailed = []

    # 1. Load Markdown Front Matter
    if md_file_path.exists():
        try:
            post_fm = frontmatter.load(md_file_path)
            metadata = post_fm.metadata
            logging.info(f"Loaded metadata for '{slug}'.")
        except Exception as e:
            logging.error(f"Error loading front matter for '{slug}': {e}", exc_info=True)
            metadata = {'title': f"Error Loading Post: {slug}"}
    else:
        logging.warning(f"Markdown file not found for slug '{slug}': {md_file_path}")
        metadata = {'title': f"Post Not Found: {slug}"}

    # 2. Load Workflow Status Data
    workflow_data_full = load_json_data(workflow_status_path)
    if workflow_data_full is None:
         logging.error("Critical error loading workflow data file.")
    elif workflow_data_full:
        status_data = workflow_data_full.get(slug, {"stages": {}})

    # 3. Load Image Library Data
    image_library_data = load_json_data(image_library_path)
    if image_library_data is None:
        logging.error("Critical error loading image library data file.")
        image_library_data = {}
    elif not image_library_data:
        logging.warning(f"Image library file '{IMAGE_LIBRARY_FILE}' not found.")

    # 4. Get Referenced Image IDs from Post Metadata
    referenced_image_ids = []
    if 'headerImageId' in metadata: referenced_image_ids.append(metadata['headerImageId'])
    for section in metadata.get('sections', []):
        if section.get('imageId'): referenced_image_ids.append(section['imageId'])
    if metadata.get('conclusion', {}).get('imageId'): referenced_image_ids.append(metadata['conclusion']['imageId'])
    referenced_image_ids = list(dict.fromkeys(referenced_image_ids)) # Unique IDs
    logging.info(f"Found {len(referenced_image_ids)} unique image IDs referenced by post '{slug}'.")

    # 5. Process Referenced Images - Calculate Statuses
    all_img_prompts_ok = True if referenced_image_ids else False
    all_img_assets_ok = True if referenced_image_ids else False
    all_img_meta_ok = True if referenced_image_ids else False

    for img_id in referenced_image_ids:
        img_details = image_library_data.get(img_id)
        if not img_details:
            logging.warning(f"Image ID '{img_id}' referenced in post '{slug}' not found in image library.")
            images_detailed.append({"id": img_id, "error": "Not found in image library"})
            all_img_prompts_ok = all_img_assets_ok = all_img_meta_ok = False
            continue

        calc_status = {
            "id": img_id,
            "description": img_details.get("description", ""),
            "prompt": img_details.get("prompt", ""),
            "notes": img_details.get("notes", ""),
            "filename_local": img_details.get("source_details", {}).get("filename_local", ""),
            "local_dir": img_details.get("source_details", {}).get("local_dir", "images/posts"), # Default
            "alt": img_details.get("metadata", {}).get("alt", ""),
            "blog_caption": img_details.get("metadata", {}).get("blog_caption", ""),
            # Construct URL for display in admin UI
            "display_url": url_for('serve_images', filename=f"{img_details.get('source_details', {}).get('local_dir', 'images/posts').strip('/')}/{img_details.get('source_details', {}).get('filename_local', '')}") if img_details.get("source_details", {}).get("filename_local") else None
        }

        # Prompt Status
        if calc_status["prompt"]: calc_status["prompt_status"] = "complete"
        else: calc_status["prompt_status"] = "pending"; all_img_prompts_ok = False

        # Asset Prepared Status
        local_file_path = None
        if calc_status["local_dir"] and calc_status["filename_local"]:
             local_file_path = BASE_DIR / calc_status["local_dir"].strip('/') / calc_status["filename_local"]
             if local_file_path.is_file(): calc_status["assets_prepared_status"] = "complete"
             else:
                 logging.warning(f"Image asset file not found: {local_file_path}")
                 calc_status["assets_prepared_status"] = "pending"; all_img_assets_ok = False
        else: calc_status["assets_prepared_status"] = "pending"; all_img_assets_ok = False

        # Metadata Status
        if calc_status["alt"] and calc_status["blog_caption"]: calc_status["metadata_integrated_status"] = "complete"
        else: calc_status["metadata_integrated_status"] = "pending"; all_img_meta_ok = False

        # Watermarking Status (from workflow)
        img_watermark_status = status_data.get('stages', {}).get('images', {}).get('watermarks', {}).get(img_id, 'pending')
        calc_status["watermarking_status"] = img_watermark_status

        images_detailed.append(calc_status)

    # 6. Determine Overall Image Stage Status (in memory for display)
    if 'stages' not in status_data: status_data['stages'] = {}
    if 'images' not in status_data['stages']: status_data['stages']['images'] = {}

    status_data['stages']['images']['prompts_defined_status'] = 'complete' if referenced_image_ids and all_img_prompts_ok else 'pending'
    status_data['stages']['images']['assets_prepared_status'] = 'complete' if referenced_image_ids and all_img_assets_ok else 'pending'
    status_data['stages']['images']['metadata_integrated_status'] = 'complete' if referenced_image_ids and all_img_meta_ok else 'pending'

    # Determine overall status based on sub-steps
    if status_data['stages']['images']['prompts_defined_status'] == 'complete' and \
       status_data['stages']['images']['assets_prepared_status'] == 'complete' and \
       status_data['stages']['images']['metadata_integrated_status'] == 'complete':
           status_data['stages']['images']['status'] = 'complete'
    elif status_data['stages']['images']['prompts_defined_status'] == 'pending' and \
         status_data['stages']['images']['assets_prepared_status'] == 'pending' and \
         status_data['stages']['images']['metadata_integrated_status'] == 'pending':
           status_data['stages']['images']['status'] = 'pending'
    else:
           status_data['stages']['images']['status'] = 'partial'

    return render_template(
        'admin_post_detail.html',
        slug=slug,
        metadata=metadata,
        status=status_data,
        images_detailed=images_detailed,
        config=app.config
    )


# --- NEW API Endpoint for Watermarking All Images ---
@app.route('/api/watermark_all/<string:slug>', methods=['POST'])
def watermark_all_api(slug):
    """
    Triggers the watermark_images.py script for all referenced images in a post.
    """
    logging.info(f"Received request to watermark all images for slug: {slug}")

    # 1. Find referenced image IDs (similar logic to view_post_detail)
    md_file_path = BASE_DIR / POSTS_DIR_NAME / f"{slug}.md"
    referenced_image_ids = []
    if md_file_path.exists():
        try:
            post_fm = frontmatter.load(md_file_path)
            metadata = post_fm.metadata
            if 'headerImageId' in metadata: referenced_image_ids.append(metadata['headerImageId'])
            for section in metadata.get('sections', []):
                if section.get('imageId'): referenced_image_ids.append(section['imageId'])
            if metadata.get('conclusion', {}).get('imageId'): referenced_image_ids.append(metadata['conclusion']['imageId'])
            referenced_image_ids = list(dict.fromkeys(referenced_image_ids)) # Unique IDs
            logging.info(f"Found {len(referenced_image_ids)} unique image IDs to watermark for '{slug}'.")
        except Exception as e:
            error_msg = f"Error loading front matter to get image IDs for '{slug}': {e}"
            logging.error(error_msg)
            return jsonify({"success": False, "output": error_msg, "slug": slug}), 500
    else:
        error_msg = f"Markdown file not found for slug '{slug}': {md_file_path}"
        logging.error(error_msg)
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 404

    if not referenced_image_ids:
        return jsonify({"success": True, "output": "No images referenced in post, nothing to watermark.", "slug": slug})

    # 2. Construct command for the script
    script_path = str(BASE_DIR / 'scripts' / 'watermark_images.py')
    # Pass slug and image IDs as arguments
    command = [ sys.executable, script_path, '--slug', slug ]
    for img_id in referenced_image_ids:
        command.extend(['--image-id', img_id])

    logging.info(f"Executing command: {' '.join(command)}")

    # 3. Run the script
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=BASE_DIR)
        output_log = f"--- Watermark Script STDOUT ---\n{result.stdout}\n--- Watermark Script STDERR ---\n{result.stderr}"
        success = result.returncode == 0
        if success:
            logging.info(f"Watermark script for slug '{slug}' completed successfully.")
        else:
            logging.error(f"Watermark script for slug '{slug}' failed with return code {result.returncode}.")

        return jsonify({"success": success, "output": output_log, "slug": slug})

    except FileNotFoundError:
        error_msg = f"Error: '{sys.executable}' or script '{script_path}' not found."
        logging.error(error_msg)
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 500
    except Exception as e:
        error_msg = f"An unexpected error occurred while running the watermark script: {e}"
        logging.error(error_msg)
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 500


@app.route('/api/publish_clan/<string:slug>', methods=['POST'])
def publish_to_clan_api(slug):
    """
    Triggers the post_to_clan.py script and updates workflow status.
    """
    logging.info(f"Received request to publish/update slug: {slug}")
    script_path = str(BASE_DIR / 'scripts' / 'post_to_clan.py')
    markdown_file_relative_path = f"{POSTS_DIR_NAME}/{slug}.md"
    markdown_file_abs_path = str(BASE_DIR / POSTS_DIR_NAME / f"{slug}.md")

    if not Path(markdown_file_abs_path).is_file():
        logging.error(f"Markdown file not found for slug '{slug}': {markdown_file_abs_path}")
        return jsonify({"success": False, "output": f"Error: Markdown file not found at {markdown_file_relative_path}", "slug": slug}), 404

    command = [sys.executable, script_path, markdown_file_relative_path]
    logging.info(f"Executing command: {' '.join(command)}")

    output_log = ""
    script_success = False
    api_error_msg_for_status = None # For storing error in workflow

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=BASE_DIR)
        # Combine stdout and stderr for logging/display, prioritizing stderr for error messages
        output_log = f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"
        script_success = result.returncode == 0

        if script_success:
            logging.info(f"Publish script for slug '{slug}' completed successfully.")
        else:
            logging.error(f"Publish script for slug '{slug}' failed with return code {result.returncode}.")
            # Try to get a concise error from stderr for the status update
            error_lines = result.stderr.strip().split('\n')
            last_error_line = error_lines[-1] if error_lines else f"Script failed with exit code {result.returncode}."
            api_error_msg_for_status = (last_error_line[:250] + '...') if len(last_error_line) > 250 else last_error_line

        # --- BEGIN STATUS UPDATE LOGIC ---
        workflow_status_path = DATA_DIR / WORKFLOW_STATUS_FILE
        workflow_data = load_json_data(workflow_status_path)

        if workflow_data is not None: # Only proceed if load was successful
            if slug not in workflow_data: workflow_data[slug] = {"stages": {}}
            if 'stages' not in workflow_data[slug]: workflow_data[slug]['stages'] = {}
            if 'publishing_clancom' not in workflow_data[slug]['stages']: workflow_data[slug]['stages']['publishing_clancom'] = {}

            update_time = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + 'Z'
            workflow_data[slug]['last_updated'] = update_time
            workflow_data[slug]['stages']['publishing_clancom']['last_publish_attempt'] = update_time

            if script_success:
                workflow_data[slug]['stages']['publishing_clancom']['status'] = 'complete'
                workflow_data[slug]['stages']['publishing_clancom']['last_error'] = None # Clear previous errors
                logging.info(f"Updating workflow status to 'complete' for {slug}")
                # --- Try to get Post ID from script output (if script prints it reliably) ---
                # Example: Assuming script prints "SUCCESS: ... ID: 123"
                match = re.search(r"SUCCESS:.*?ID:\s*(\d+)", result.stdout, re.IGNORECASE)
                if match:
                    extracted_id = int(match.group(1))
                    workflow_data[slug]['stages']['publishing_clancom']['post_id'] = extracted_id
                    logging.info(f"Extracted and stored Post ID {extracted_id} for {slug}")
                # --- End Post ID extraction ---
            else:
                workflow_data[slug]['stages']['publishing_clancom']['status'] = 'error'
                # Use the error captured earlier, or default
                final_error = api_error_msg_for_status or "Script failed, check logs/output."
                workflow_data[slug]['stages']['publishing_clancom']['last_error'] = final_error
                logging.info(f"Updating workflow status to 'error' for {slug}. Error: {final_error}")
                # Handle specific case where edit failed because post was deleted remotely
                # (Need post_to_clan.py to reliably indicate this, e.g., via stderr message or specific exit code)
                # Example: if "PostNotFound" in (api_error_msg_for_status or ""):
                #    workflow_data[slug]['stages']['publishing_clancom'].pop("post_id", None)

            if not save_json_data(workflow_status_path, workflow_data):
                logging.error(f"Failed to save updated workflow status for {slug} after script run!")
                # Optionally add a warning to the output log returned to the user
                output_log += "\n\nWARNING: Failed to save updated workflow status to JSON file."
        else:
            logging.error(f"Could not load workflow status file {workflow_status_path} to update status after script run.")
            output_log += f"\n\nERROR: Could not load {WORKFLOW_STATUS_FILE} to update status."
        # --- END STATUS UPDATE LOGIC ---

        # Return script success status and its combined output
        return jsonify({"success": script_success, "output": output_log, "slug": slug})

    except FileNotFoundError:
        error_msg = f"Error: '{sys.executable}' or script '{script_path}' not found."
        logging.error(error_msg)
        # Also update status to error here? Risky if workflow file itself is missing.
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 500
    except Exception as e:
        error_msg = f"An unexpected error occurred while preparing/running the script: {e}"
        logging.error(error_msg, exc_info=True)
        # Update status to error here?
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 500


@app.route('/api/update_status/<string:slug>/<string:stage_key>', methods=['POST'])
def update_status_api(slug, stage_key):
    """
    Updates the status for a specific stage or nested sub-stage of a post.
    Handles nested keys like 'images.watermarks.image_id'.
    """
    logging.info(f"Received request to update status for slug: {slug}, stage_key: {stage_key}")

    data = request.get_json()
    if not data or 'status' not in data:
        logging.error("Missing 'status' in request body.")
        return jsonify({"success": False, "message": "Missing 'status' in request body"}), 400
    new_status = data['status']
    # TODO: Add validation for allowed new_status values ('pending', 'partial', 'complete', 'error')?

    workflow_status_path = DATA_DIR / WORKFLOW_STATUS_FILE
    workflow_data = load_json_data(workflow_status_path)

    if workflow_data is None:
        return jsonify({"success": False, "message": f"Error loading data file {WORKFLOW_STATUS_FILE}"}), 500

    # --- Navigate and Update Nested Structure ---
    try:
        # Get or initialize the entry for the slug
        post_entry = workflow_data.setdefault(slug, {"stages": {}})
        post_entry.setdefault("stages", {}) # Ensure stages dict exists

        # Navigate through potentially nested keys (e.g., "images.watermarks.some_image_id")
        keys = stage_key.split('.')
        current_level = post_entry["stages"]
        # Iterate through keys up to the second-to-last one to ensure parent dicts exist
        for i, key in enumerate(keys[:-1]):
            # If it's the 'watermarks' level and it doesn't exist, initialize it
            # (Could be generalized further if more nested dicts are expected)
            if key == 'watermarks' and key not in current_level:
                 current_level[key] = {}
                 logging.info(f"Initialized nested dict '{key}' for {slug}/{'/'.join(keys[:i+1])}")
            # Otherwise, use setdefault to get or create the next level dictionary
            elif isinstance(current_level.get(key), dict):
                 current_level = current_level[key]
            elif key not in current_level:
                 current_level[key] = {} # Initialize parent dict if missing
                 logging.info(f"Initialized nested dict '{key}' for {slug}/{'/'.join(keys[:i+1])}")
                 current_level = current_level[key]
            else:
                 # Found a non-dictionary where a dictionary was expected
                 raise ValueError(f"Path collision: '{key}' in '{stage_key}' is not a dictionary.")

        # Now set the status on the final key
        final_key = keys[-1]
        # Check if the target level is actually a dictionary (it should be after setdefault)
        if isinstance(current_level, dict):
            # If the final key represents a stage (like 'images' or 'publishing_clancom'),
            # update its 'status'. If it's a specific item (like an image ID under watermarks),
            # set the status directly. This assumes simple status strings for now.
            if final_key in current_level and isinstance(current_level[final_key], dict):
                 current_level[final_key]['status'] = new_status # Update status within a stage object
            else:
                 current_level[final_key] = new_status # Set status directly (e.g., for watermark ID)
            logging.info(f"Updating status for '{slug}/{stage_key}' to '{new_status}'.")
        else:
             raise ValueError(f"Cannot set status: '{'/'.join(keys[:-1])}' is not a dictionary.")

        post_entry['last_updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + 'Z'

    except (ValueError, KeyError, TypeError) as e:
         logging.error(f"Error navigating/updating status structure for key '{stage_key}': {e}")
         return jsonify({"success": False, "message": f"Invalid stage key or structure: {stage_key}"}), 400
    # --- End Nested Update ---


    # Save the updated data
    if save_json_data(workflow_status_path, workflow_data):
        return jsonify({
            "success": True,
            "slug": slug,
            "stage_key": stage_key, # Return the key that was updated
            "new_status": new_status
        })
    else:
        return jsonify({"success": False, "message": "Failed to save updated workflow data."}), 500

# --- Run the App ---
if __name__ == '__main__':
    # Use port 5001 as specified
    app.run(debug=True, port=5001)