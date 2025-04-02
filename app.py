# /Users/nickfiddes/Code/projects/blog_ssg/app.py

from flask import Flask, render_template, jsonify, request, url_for
import os
import json
from pathlib import Path
import frontmatter
import logging
import subprocess
import sys
import datetime # Added missing import

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
app.config['BASE_DIR_STR'] = str(BASE_DIR) # Make base dir accessible in templates if needed via config

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
        # Render an error page or return limited data? For now, return empty.
        workflow_data = {}
    elif not workflow_data: # File not found case from load_json_data
        logging.warning(f"Workflow data file '{WORKFLOW_STATUS_FILE}' not found. Statuses unavailable.")
        # Continue with empty data

    try:
        logging.info(f"Scanning directory: {posts_dir_path}")
        if not posts_dir_path.is_dir():
             logging.error(f"Posts directory not found: {posts_dir_path}")
             raise FileNotFoundError # Handle below

        for filename in os.listdir(posts_dir_path):
            if filename.endswith(".md"):
                file_path = posts_dir_path / filename
                logging.debug(f"Processing file: {filename}")
                try:
                    post_fm = frontmatter.load(file_path)
                    metadata = post_fm.metadata
                    slug = Path(filename).stem
                    title = metadata.get('title', f"Untitled ({slug})")

                    # Get clan.com status from workflow data
                    post_workflow_data = workflow_data.get(slug, {}) # Safely get data for slug
                    clan_com_stage = post_workflow_data.get('stages', {}).get('publishing_clancom', {})
                    clan_com_post_id = clan_com_stage.get('post_id')
                    clan_com_status_val = clan_com_stage.get('status', 'pending')

                    # Determine display status
                    if clan_com_post_id and clan_com_status_val == 'complete':
                        clan_com_status_display = f"Published (ID: {clan_com_post_id})"
                    elif clan_com_status_val == 'error':
                         clan_com_status_display = "Error Publishing"
                    else: # includes 'pending', 'partial', or unknown statuses
                        clan_com_status_display = "Not Published / Pending"

                    posts_list.append({'slug': slug, 'title': title, 'clan_com_status': clan_com_status_display})
                except Exception as e:
                    logging.error(f"Error processing markdown file {filename}: {e}")
                    # Optionally add a post entry indicating the error for this file

        posts_list.sort(key=lambda p: p['slug'])
        logging.info(f"Found and processed {len(posts_list)} posts.")

    except FileNotFoundError:
        logging.error(f"Posts directory not found: {posts_dir_path}")
        # Optionally display an error message in the template
    except Exception as e:
        logging.error(f"Error listing or processing posts directory: {e}")
        # Optionally display an error message in the template

    return render_template(
            'admin_index.html',
            posts=posts_list,
            config=app.config # Pass Flask config which includes BASE_DIR_STR
           )


@app.route('/admin/post/<string:slug>')
def view_post_detail(slug):
    """Displays the detailed workflow management page for a single post."""
    logging.info(f"Processing detail route '/admin/post/{slug}'...")
    md_file_path = BASE_DIR / POSTS_DIR_NAME / f"{slug}.md" # Use constant
    workflow_status_path = DATA_DIR / WORKFLOW_STATUS_FILE # Use constants
    image_library_path = DATA_DIR / IMAGE_LIBRARY_FILE # Use constants

    metadata = {}
    status_data = {"stages": {}} # Default empty status structure
    images_detailed = [] # To hold detailed info for template

    # 1. Load Markdown Front Matter
    if md_file_path.exists():
        try:
            post_fm = frontmatter.load(md_file_path)
            metadata = post_fm.metadata
            logging.info(f"Loaded metadata for '{slug}'.")
        except Exception as e:
            logging.error(f"Error loading front matter for '{slug}': {e}")
            metadata = {'title': f"Error Loading Post: {slug}"}
    else:
        logging.warning(f"Markdown file not found for slug '{slug}': {md_file_path}")
        metadata = {'title': f"Post Not Found: {slug}"}

    # 2. Load Workflow Status Data (Handles None/empty dict)
    workflow_data_full = load_json_data(workflow_status_path)
    if workflow_data_full is None: # Critical load error
         logging.error("Critical error loading workflow data file.")
         # status_data remains default empty structure
    elif workflow_data_full: # Loaded successfully (or empty file found)
        status_data = workflow_data_full.get(slug, {"stages": {}}) # Get status or provide default structure
    # If workflow_data_full was {}, status_data remains default

    # 3. Load Image Library Data (Handles None/empty dict)
    image_library_data = load_json_data(image_library_path)
    if image_library_data is None: # Critical load error
        logging.error("Critical error loading image library data file.")
        image_library_data = {} # Prevent downstream errors
    elif not image_library_data: # File not found case
        logging.warning(f"Image library file '{IMAGE_LIBRARY_FILE}' not found.")
        # Continue with empty library data

    # 4. Get Referenced Image IDs from Post Metadata
    referenced_image_ids = []
    if 'headerImageId' in metadata:
        referenced_image_ids.append(metadata['headerImageId'])
    for section in metadata.get('sections', []):
        if section.get('imageId'):
            referenced_image_ids.append(section['imageId'])
    if metadata.get('conclusion', {}).get('imageId'):
         referenced_image_ids.append(metadata['conclusion']['imageId'])
    # Remove duplicates if necessary
    referenced_image_ids = list(dict.fromkeys(referenced_image_ids))
    logging.info(f"Found {len(referenced_image_ids)} unique image IDs referenced by post '{slug}'.")

    # 5. Process Referenced Images - Calculate Statuses
    all_image_prompts_defined = True if referenced_image_ids else False # Start true only if list is empty
    all_image_assets_prepared = True if referenced_image_ids else False
    all_image_metadata_integrated = True if referenced_image_ids else False

    for img_id in referenced_image_ids:
        img_details = image_library_data.get(img_id)
        if not img_details:
            logging.warning(f"Image ID '{img_id}' referenced in post '{slug}' not found in image library.")
            images_detailed.append({"id": img_id, "error": "Not found in image library"})
            # Mark all as false if *any* image is missing
            all_image_prompts_defined = False
            all_image_assets_prepared = False
            all_image_metadata_integrated = False
            continue # Skip further processing for this missing image

        calculated_status = {
            "id": img_id,
            "description": img_details.get("description", ""),
            "prompt": img_details.get("prompt", ""),
            "notes": img_details.get("notes", ""),
            "filename_local": img_details.get("source_details", {}).get("filename_local", ""),
            "local_dir": img_details.get("source_details", {}).get("local_dir", "images/posts"), # Default dir
            "alt": img_details.get("metadata", {}).get("alt", ""),
            "blog_caption": img_details.get("metadata", {}).get("blog_caption", ""),
        }

        # Calculate 'prompt_status'
        if calculated_status["prompt"]:
            calculated_status["prompt_status"] = "complete"
        else:
            calculated_status["prompt_status"] = "pending"
            all_image_prompts_defined = False # Mark overall as false if any prompt missing

        # Calculate 'assets_prepared_status' (filename exists AND file exists on disk)
        local_file_path = None
        if calculated_status["local_dir"] and calculated_status["filename_local"]:
             # Construct path relative to BASE_DIR
             local_file_path = BASE_DIR / calculated_status["local_dir"].strip('/') / calculated_status["filename_local"]
             if local_file_path.is_file():
                 calculated_status["assets_prepared_status"] = "complete"
             else:
                 logging.warning(f"Image asset file not found: {local_file_path}")
                 calculated_status["assets_prepared_status"] = "pending" # File missing
                 all_image_assets_prepared = False
        else:
             calculated_status["assets_prepared_status"] = "pending" # Path info missing in library
             all_image_assets_prepared = False

        # Calculate 'metadata_integrated_status' (Check alt and caption)
        if calculated_status["alt"] and calculated_status["blog_caption"]:
             calculated_status["metadata_integrated_status"] = "complete"
        else:
             calculated_status["metadata_integrated_status"] = "pending"
             all_image_metadata_integrated = False

        # Get watermarking status directly from stored data (in workflow_status.json)
        # Watermarking is post-specific, so check status_data
        img_watermark_status = status_data.get('stages', {}).get('images', {}).get('watermarks', {}).get(img_id, 'pending')
        calculated_status["watermarking_status"] = img_watermark_status

        images_detailed.append(calculated_status)

    # 6. Determine Overall Image Stage Status (in memory for display)
    if 'stages' not in status_data: status_data['stages'] = {}
    if 'images' not in status_data['stages']: status_data['stages']['images'] = {}

    # Update sub-statuses based on the checks across *all* referenced images
    # Only complete if list wasn't empty AND all items passed
    status_data['stages']['images']['prompts_defined_status'] = 'complete' if referenced_image_ids and all_image_prompts_defined else 'pending'
    status_data['stages']['images']['assets_prepared_status'] = 'complete' if referenced_image_ids and all_image_assets_prepared else 'pending'
    status_data['stages']['images']['metadata_integrated_status'] = 'complete' if referenced_image_ids and all_image_metadata_integrated else 'pending'

    # Determine overall image stage status based on sub-steps (excluding watermarking for main status)
    if status_data['stages']['images']['prompts_defined_status'] == 'complete' and \
       status_data['stages']['images']['assets_prepared_status'] == 'complete' and \
       status_data['stages']['images']['metadata_integrated_status'] == 'complete':
           status_data['stages']['images']['status'] = 'complete'
    elif status_data['stages']['images']['prompts_defined_status'] == 'pending' and \
         status_data['stages']['images']['assets_prepared_status'] == 'pending' and \
         status_data['stages']['images']['metadata_integrated_status'] == 'pending':
           status_data['stages']['images']['status'] = 'pending'
    else: # Some done, some not
           status_data['stages']['images']['status'] = 'partial'

    # Note: Watermarking status is handled separately and doesn't affect the main 'images' stage status here.

    return render_template(
        'admin_post_detail.html',
        slug=slug,
        metadata=metadata,
        status=status_data, # Pass potentially updated status_data
        images_detailed=images_detailed,
        config=app.config
    )


@app.route('/api/publish_clan/<string:slug>', methods=['POST'])
def publish_to_clan_api(slug):
    """Triggers the post_to_clan.py script for the given slug."""
    logging.info(f"Received request to publish/update slug: {slug}")
    script_path = str(BASE_DIR / 'scripts' / 'post_to_clan.py')
    # Provide the *relative* path from BASE_DIR to the script if needed by script logic
    markdown_file_relative_path = f"{POSTS_DIR_NAME}/{slug}.md" # Use constant
    markdown_file_abs_path = str(BASE_DIR / POSTS_DIR_NAME / f"{slug}.md")

    if not Path(markdown_file_abs_path).is_file():
        logging.error(f"Markdown file not found for slug '{slug}': {markdown_file_abs_path}")
        return jsonify({"success": False, "output": f"Error: Markdown file not found at {markdown_file_relative_path}", "slug": slug}), 404

    # Pass the relative path as an argument to the script
    command = [ sys.executable, script_path, markdown_file_relative_path ]
    logging.info(f"Executing command: {' '.join(command)}")
    try:
        # Run script from BASE_DIR so its relative paths work
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=BASE_DIR)
        output_log = f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"
        success = result.returncode == 0
        if success:
            logging.info(f"Script for slug '{slug}' completed successfully.")
        else:
            logging.error(f"Script for slug '{slug}' failed with return code {result.returncode}.")
        # TODO: Update workflow_status.json based on success/failure here?
        return jsonify({"success": success, "output": output_log, "slug": slug})

    except FileNotFoundError:
        error_msg = f"Error: '{sys.executable}' or script '{script_path}' not found."
        logging.error(error_msg)
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 500
    except Exception as e:
        error_msg = f"An unexpected error occurred while running the script: {e}"
        logging.error(error_msg)
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 500


@app.route('/api/update_status/<string:slug>/<string:stage_key>', methods=['POST'])
def update_status_api(slug, stage_key):
    """Updates the status for a specific stage of a post in workflow_status.json."""
    logging.info(f"Received request to update status for slug: {slug}, stage: {stage_key}")

    data = request.get_json()
    if not data or 'status' not in data:
        logging.error("Missing 'status' in request body.")
        return jsonify({"success": False, "message": "Missing 'status' in request body"}), 400
    new_status = data['status']
    # TODO: Add validation for new_status value

    workflow_status_path = DATA_DIR / WORKFLOW_STATUS_FILE
    workflow_data = load_json_data(workflow_status_path)

    if workflow_data is None: # Critical load error
        return jsonify({"success": False, "message": f"Error loading data file {WORKFLOW_STATUS_FILE}"}), 500
    # Allow creating entry for slug if it doesn't exist
    if slug not in workflow_data:
        workflow_data[slug] = {"stages": {}}
        logging.info(f"Initialized entry for new slug '{slug}' in workflow data.")

    # Ensure stages dictionary exists
    if 'stages' not in workflow_data[slug]:
        workflow_data[slug]['stages'] = {}

    # Ensure the specific stage dictionary exists
    if stage_key not in workflow_data[slug]['stages']:
        workflow_data[slug]['stages'][stage_key] = {}
        logging.info(f"Initialized stage '{stage_key}' for slug '{slug}'.")

    # Update the status
    workflow_data[slug]['stages'][stage_key]['status'] = new_status
    workflow_data[slug]['last_updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat() # Use UTC
    logging.info(f"Updating status for '{slug}/{stage_key}' to '{new_status}'.")

    # Save the updated data
    if save_json_data(workflow_status_path, workflow_data):
        return jsonify({
            "success": True,
            "slug": slug,
            "stage": stage_key,
            "new_status": new_status
        })
    else:
        return jsonify({"success": False, "message": "Failed to save updated workflow data."}), 500

# --- Run the App ---
if __name__ == '__main__':
    # Use port 5001 as specified in original code
    app.run(debug=True, port=5001)