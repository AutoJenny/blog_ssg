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


# --- NEW: Post Detail Route ---
@app.route('/admin/post/<string:slug>')
def view_post_detail(slug):
    """Displays the detailed workflow management page for a single post."""
    logging.info(f"Processing detail route '/admin/post/{slug}'...")
    md_file_path = BASE_DIR / POSTS_DIR / f"{slug}.md"
    syndication_data_path = BASE_DIR / SYNDICATION_DATA_FILE # Use updated filename

    metadata = {}
    status_data = {} # Default empty status

    # Load Markdown Front Matter
    if md_file_path.exists():
        try:
            post_fm = frontmatter.load(md_file_path)
            metadata = post_fm.metadata
            logging.info(f"Loaded metadata for '{slug}'.")
        except Exception as e:
            logging.error(f"Error loading front matter for '{slug}': {e}")
            metadata = {'title': f"Error Loading Post: {slug}"} # Provide error title
    else:
        logging.warning(f"Markdown file not found for slug '{slug}': {md_file_path}")
        metadata = {'title': f"Post Not Found: {slug}"} # Provide error title

    # Load Workflow Status Data
    workflow_data = load_syndication_data(syndication_data_path)
    if workflow_data is None:
        logging.error("Failed to load workflow data for detail page.")
        # Potentially pass an error flag to the template
    elif slug in workflow_data:
        status_data = workflow_data[slug]
        logging.info(f"Loaded workflow status for '{slug}'.")
    else:
        logging.warning(f"No workflow status found for slug '{slug}' in {SYNDICATION_DATA_FILE}.")
        # Template will use default filters if status_data is empty

    # Pass BASE_DIR needed for vscode:// links in the detail page too if needed later
    return render_template(
        'admin_post_detail.html',
        slug=slug,
        metadata=metadata,
        status=status_data,
        config={'BASE_DIR': str(BASE_DIR)}
    )
# --- End Post Detail Route ---


@app.route('/api/publish_clan/<string:slug>', methods=['POST'])
def publish_to_clan_api(slug):
    """Triggers the post_to_clan.py script for the given slug."""
    # ... (Function remains the same as previous version) ...
    logging.info(f"Received request to publish/update slug: {slug}")
    script_path = str(BASE_DIR / 'post_to_clan.py')
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