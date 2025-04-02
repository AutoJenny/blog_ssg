# /Users/nickfiddes/Code/projects/blog_ssg/app.py

from flask import Flask, render_template, jsonify, request, url_for # Added request, url_for
import os
import json
from pathlib import Path
import frontmatter
import logging
import subprocess
import sys

# --- Configuration ---
POSTS_DIR = "posts"
SYNDICATION_DATA_FILE = "_data/workflow_status.json" # Updated filename

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent

# --- Helper Function (Same as before) ---
def load_syndication_data(file_path):
    """Loads the JSON data file."""
    try:
        abs_file_path = BASE_DIR / file_path
        logging.info(f"Attempting to load workflow data from: {abs_file_path}")
        with open(abs_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"Successfully loaded data for {len(data)} post slugs.")
            return data
    except FileNotFoundError:
        logging.warning(f"Workflow data file not found: {abs_file_path}. Returning empty data.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {abs_file_path}.")
        return None
    except Exception as e:
        logging.error(f"Error loading workflow data: {e}")
        return None

# --- Flask Routes ---
@app.route('/')
def index():
    """Renders the main admin interface page, loading post data."""
    logging.info("Processing index route '/'...")
    posts_list = []
    posts_dir_path = BASE_DIR / POSTS_DIR
    syndication_data_path = BASE_DIR / SYNDICATION_DATA_FILE # Use updated filename
    workflow_data = load_syndication_data(syndication_data_path)
    if workflow_data is None:
        logging.error("Failed to load workflow data, post status will be unavailable.")
        workflow_data = {}

    try:
        logging.info(f"Scanning directory: {posts_dir_path}")
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
                    post_workflow_data = workflow_data.get(slug, {})
                    clan_com_post_id = post_workflow_data.get('stages', {}).get('publishing_clancom', {}).get('post_id')
                    clan_com_status_val = post_workflow_data.get('stages', {}).get('publishing_clancom', {}).get('status', 'pending')

                    if clan_com_post_id and clan_com_status_val == 'complete':
                        clan_com_status_display = f"Published (ID: {clan_com_post_id})"
                    elif clan_com_status_val == 'error':
                         clan_com_status_display = "Error Publishing"
                    else:
                        clan_com_status_display = "Not Published / Pending"

                    posts_list.append({'slug': slug, 'title': title, 'clan_com_status': clan_com_status_display})
                except Exception as e: logging.error(f"Error processing markdown file {filename}: {e}")
        posts_list.sort(key=lambda p: p['slug'])
        logging.info(f"Found and processed {len(posts_list)} posts.")
    except FileNotFoundError: logging.error(f"Posts directory not found: {posts_dir_path}")
    except Exception as e: logging.error(f"Error listing or processing posts directory: {e}")

    # Pass BASE_DIR for vscode:// links
    return render_template(
            'admin_index.html',
            posts=posts_list,
            config={'BASE_DIR': str(BASE_DIR)}
           )


# Add near top imports if missing
# from pathlib import Path
# import os
# import json
# import frontmatter
# import logging
# from flask import ...

@app.route('/admin/post/<string:slug>')
def view_post_detail(slug):
    """Displays the detailed workflow management page for a single post."""
    logging.info(f"Processing detail route '/admin/post/{slug}'...")
    md_file_path = BASE_DIR / POSTS_DIR_NAME / f"{slug}.md" # Use constant
    workflow_status_path = WORKFLOW_STATUS_FILE # Path object
    image_library_path = IMAGE_LIBRARY_FILE # Path object

    metadata = {}
    status_data = {} # Default empty status
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

    # 2. Load Workflow Status Data
    workflow_data = load_json_data(workflow_status_path)
    if workflow_data is None:
        logging.error("Failed to load workflow data for detail page.")
        workflow_data = {} # Prevent downstream errors
    status_data = workflow_data.get(slug, {"stages": {}}) # Get status or provide default structure

    # 3. Load Image Library Data
    image_library_data = load_json_data(image_library_path)
    if image_library_data is None:
        logging.error("Failed to load image library data.")
        image_library_data = {} # Prevent downstream errors

    # 4. Get Referenced Image IDs from Post Metadata
    referenced_image_ids = []
    if metadata.get('headerImageId'):
        referenced_image_ids.append(metadata['headerImageId'])
    for section in metadata.get('sections', []):
        if section.get('imageId'):
            referenced_image_ids.append(section['imageId'])
    if metadata.get('conclusion', {}).get('imageId'):
         referenced_image_ids.append(metadata['conclusion']['imageId'])
    logging.info(f"Found {len(referenced_image_ids)} image IDs referenced by post '{slug}'.")

    # 5. Process Referenced Images - Calculate Statuses
    all_image_prompts_defined = True
    all_image_assets_prepared = True
    all_image_metadata_integrated = True # Check if essential metadata exists
    # Watermarking status is tracked separately

    for img_id in referenced_image_ids:
        img_details = image_library_data.get(img_id)
        if not img_details:
            logging.warning(f"Image ID '{img_id}' referenced in post '{slug}' not found in image library.")
            images_detailed.append({"id": img_id, "error": "Not found in image library"})
            all_image_prompts_defined = False
            all_image_assets_prepared = False
            all_image_metadata_integrated = False
            continue

        calculated_status = {
            "id": img_id,
            "description": img_details.get("description", ""),
            "prompt": img_details.get("prompt", ""),
            "notes": img_details.get("notes", ""),
            "filename_local": img_details.get("source_details", {}).get("filename_local", ""),
            "local_dir": img_details.get("source_details", {}).get("local_dir", ""),
            "alt": img_details.get("metadata", {}).get("alt", ""),
            "blog_caption": img_details.get("metadata", {}).get("blog_caption", ""),
            # Add syndication details if needed later
        }

        # Calculate 'prompt_status'
        if calculated_status["prompt"]:
            calculated_status["prompt_status"] = "complete"
        else:
            calculated_status["prompt_status"] = "pending"
            all_image_prompts_defined = False

        # Calculate 'assets_prepared_status' (filename exists AND file exists)
        local_file_path = None
        if calculated_status["local_dir"] and calculated_status["filename_local"]:
             local_file_path = BASE_DIR / calculated_status["local_dir"].strip('/') / calculated_status["filename_local"]
             if local_file_path.is_file():
                 calculated_status["assets_prepared_status"] = "complete"
             else:
                 calculated_status["assets_prepared_status"] = "pending" # File missing
                 all_image_assets_prepared = False
        else:
             calculated_status["assets_prepared_status"] = "pending" # Path info missing
             all_image_assets_prepared = False

        # Calculate 'metadata_integrated_status' (Check alt and caption)
        if calculated_status["alt"] and calculated_status["blog_caption"]:
             calculated_status["metadata_integrated_status"] = "complete"
        else:
             calculated_status["metadata_integrated_status"] = "pending"
             all_image_metadata_integrated = False

        # Get watermarking status directly from stored data
        calculated_status["watermarking_status"] = img_details.get("watermark_status", "pending")

        images_detailed.append(calculated_status)

    # 6. Determine Overall Image Stage Status (can be refined)
    # Update the status_data IN MEMORY before passing to template
    # This uses the calculated statuses based on image_library checks
    if 'stages' not in status_data: status_data['stages'] = {} # Ensure stages exists
    if 'images' not in status_data['stages']: status_data['stages']['images'] = {} # Ensure images stage exists

    # Update sub-statuses based on checks
    status_data['stages']['images']['prompts_defined_status'] = 'complete' if all_image_prompts_defined and referenced_image_ids else 'pending'
    status_data['stages']['images']['assets_prepared_status'] = 'complete' if all_image_assets_prepared and referenced_image_ids else 'pending'
    status_data['stages']['images']['metadata_integrated_status'] = 'complete' if all_image_metadata_integrated and referenced_image_ids else 'pending'
    # Keep stored watermarking status
    if 'watermarking_status' not in status_data['stages']['images']:
         status_data['stages']['images']['watermarking_status'] = 'pending' # Default if missing

    # Determine overall image stage status (example logic)
    if all_image_prompts_defined and all_image_assets_prepared and all_image_metadata_integrated:
         status_data['stages']['images']['status'] = 'complete' # Only complete if all sub-steps done
    elif any(s != 'pending' for s in [status_data['stages']['images']['prompts_defined_status'],
                                      status_data['stages']['images']['assets_prepared_status'],
                                      status_data['stages']['images']['metadata_integrated_status']]):
         status_data['stages']['images']['status'] = 'partial'
    else:
         status_data['stages']['images']['status'] = 'pending'

    # Note: This doesn't save the calculated statuses back to workflow_status.json yet.
    # It just calculates them for display on this page load. Saving happens via API calls.

    return render_template(
        'admin_post_detail.html',
        slug=slug,
        metadata=metadata,
        status=status_data,
        images_detailed=images_detailed, # Pass the detailed image list
        config={'BASE_DIR': str(BASE_DIR)}
    )

@app.route('/api/publish_clan/<string:slug>', methods=['POST'])
def publish_to_clan_api(slug):
    """Triggers the post_to_clan.py script for the given slug."""
    # ... (Function remains the same as previous version) ...
    logging.info(f"Received request to publish/update slug: {slug}")
    script_path = str(BASE_DIR / 'scripts' / 'post_to_clan.py')
    markdown_file_relative_path = f"{POSTS_DIR}/{slug}.md"
    markdown_file_abs_path = str(BASE_DIR / markdown_file_relative_path)
    if not os.path.exists(markdown_file_abs_path):
        logging.error(f"Markdown file not found for slug '{slug}': {markdown_file_abs_path}")
        return jsonify({"success": False, "output": f"Error: Markdown file not found at {markdown_file_relative_path}", "slug": slug}), 404
    command = [ sys.executable, script_path, markdown_file_relative_path ]
    logging.info(f"Executing command: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=BASE_DIR)
        output_log = f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"
        success = result.returncode == 0
        if success: logging.info(f"Script for slug '{slug}' completed successfully.")
        else: logging.error(f"Script for slug '{slug}' failed with return code {result.returncode}.")
        return jsonify({"success": success, "output": output_log, "slug": slug})
    except FileNotFoundError: error_msg = f"Error: '{sys.executable}' or script '{script_path}' not found."; logging.error(error_msg); return jsonify({"success": False, "output": error_msg, "slug": slug}), 500
    except Exception as e: error_msg = f"An unexpected error occurred while running the script: {e}"; logging.error(error_msg); return jsonify({"success": False, "output": error_msg, "slug": slug}), 500

# --- NEW API Endpoint for Status Updates ---
@app.route('/api/update_status/<string:slug>/<string:stage_key>', methods=['POST'])
def update_status_api(slug, stage_key):
    """Updates the status for a specific stage of a post."""
    logging.info(f"Received request to update status for slug: {slug}, stage: {stage_key}")

    # Get the new status from the incoming JSON request body
    data = request.get_json()
    if not data or 'status' not in data:
        logging.error("Missing 'status' in request body.")
        return jsonify({"success": False, "message": "Missing 'status' in request body"}), 400
    new_status = data['status']
    # TODO: Validate new_status against allowed values ('pending', 'partial', 'complete', 'error')?

    data_file_abs_path = BASE_DIR / SYNDICATION_DATA_FILE
    workflow_data = load_syndication_data(data_file_abs_path)

    if workflow_data is None:
        return jsonify({"success": False, "message": f"Error loading data file {SYNDICATION_DATA_FILE}"}), 500
    if slug not in workflow_data:
         return jsonify({"success": False, "message": f"Slug '{slug}' not found in workflow data."}), 404
    if 'stages' not in workflow_data[slug] or stage_key not in workflow_data[slug]['stages']:
         # Initialize if missing (optional, depends on desired strictness)
         if 'stages' not in workflow_data[slug]: workflow_data[slug]['stages'] = {}
         if stage_key not in workflow_data[slug]['stages']: workflow_data[slug]['stages'][stage_key] = {}
         logging.warning(f"Initialized missing stage '{stage_key}' for slug '{slug}'.")
         # return jsonify({"success": False, "message": f"Stage '{stage_key}' not found for slug '{slug}'."}), 404

    # Update the status
    workflow_data[slug]['stages'][stage_key]['status'] = new_status
    workflow_data[slug]['last_updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat() # Update timestamp
    logging.info(f"Updating status for '{slug}/{stage_key}' to '{new_status}'.")

    # Save the updated data
    if save_syndication_data(data_file_abs_path, workflow_data):
        return jsonify({
            "success": True,
            "slug": slug,
            "stage": stage_key,
            "new_status": new_status
        })
    else:
        return jsonify({"success": False, "message": "Failed to save updated workflow data."}), 500

# Make sure to import datetime at the top of app.py
import datetime

# --- Run the App --- (remains the same)
if __name__ == '__main__':
    app.run(debug=True, port=5001)
    
# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)