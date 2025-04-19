# /Users/nickfiddes/Code/projects/blog_ssg/app.py

from flask import Flask, render_template, jsonify, request, url_for, send_from_directory
import os
import json
import shutil
from pathlib import Path
import frontmatter
import logging
import subprocess
import sys
from datetime import datetime, timezone
import re 
import yaml
from werkzeug.utils import secure_filename

# Import LLM modules
from scripts.llm import MetadataGenerator
from scripts.llm.config import load_config, save_config
from scripts.llm.base import LLMConfig
from scripts.llm.factory import LLMFactory

# --- Configuration Constants ---
BASE_DIR = Path(__file__).resolve().parent
POSTS_DIR_NAME = "posts"
DATA_DIR_NAME = "_data"
DATA_DIR = BASE_DIR / DATA_DIR_NAME
WORKFLOW_STATUS_FILE = "workflow_status.json" # Main file for post status tracking
IMAGE_LIBRARY_FILE = "image_library.json"
UPLOAD_FOLDER = BASE_DIR / 'tmp'  # Add upload folder configuration
IMAGES_DIR = BASE_DIR / 'images'  # Define images directory

# Define workflow stages
WORKFLOW_STAGES = [
    'conceptualisation',
    'authoring',
    'metadata',
    'images',
    'validation',
    'publishing_clancom',
    'syndication'
]

# Create upload folder if it doesn't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['BASE_DIR_STR'] = str(BASE_DIR) # Make base dir accessible in templates
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['POSTS_DIR'] = str(BASE_DIR / POSTS_DIR_NAME)
app.config['IMAGES_DIR'] = str(IMAGES_DIR)
app.config['DATA_DIR'] = str(DATA_DIR)  # Add DATA_DIR to app config

# --- Add Static Route for Images (Development Only) ---
@app.route('/images/<path:filename>')
def serve_images(filename):
    """Serve images from the images directory."""
    logging.debug(f"Serving image: {filename} from {IMAGES_DIR}")
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

def parse_post_markdown(content: str) -> dict:
    """Parse a post's markdown content and return a dictionary of its data."""
    try:
        post = frontmatter.loads(content)
        metadata = post.metadata
        
        # Ensure required fields exist
        metadata.setdefault('title', '')
        metadata.setdefault('concept', '')
        metadata.setdefault('author', '')
        metadata.setdefault('date', '')
        metadata.setdefault('summary', '')
        metadata.setdefault('sections', [])
        metadata.setdefault('conclusion', {})
        metadata.setdefault('headerImage', {})
        metadata.setdefault('categories', [])
        metadata.setdefault('tags', [])
        
        # Get list of all images referenced in the post
        images = []
        
        # Add header image if it exists
        if metadata['headerImage'].get('src'):
            images.append({
                'src': metadata['headerImage']['src'],
                'alt': metadata['headerImage'].get('alt', ''),
                'caption': metadata['headerImage'].get('caption', ''),
                'imagePrompt': metadata['headerImage'].get('imagePrompt', ''),
                'notes': metadata['headerImage'].get('notes', '')
            })
        
        # Add section images
        for section in metadata['sections']:
            if section.get('image', {}).get('src'):
                images.append({
                    'src': section['image']['src'],
                    'alt': section['image'].get('alt', ''),
                    'caption': section['image'].get('caption', ''),
                    'imagePrompt': section['image'].get('imagePrompt', ''),
                    'notes': section['image'].get('notes', '')
                })
        
        # Add conclusion image if it exists
        if metadata['conclusion'].get('image', {}).get('src'):
            images.append({
                'src': metadata['conclusion']['image']['src'],
                'alt': metadata['conclusion']['image'].get('alt', ''),
                'caption': metadata['conclusion']['image'].get('caption', ''),
                'imagePrompt': metadata['conclusion']['image'].get('imagePrompt', ''),
                'notes': metadata['conclusion']['image'].get('notes', '')
            })
        
        metadata['images'] = images
        return metadata
        
    except Exception as e:
        logging.error(f"Error parsing markdown content: {e}")
        return {}

def get_detailed_image_info(images: list) -> list:
    """Get detailed information about each image in the list."""
    detailed_images = []
    for img in images:
        if not img.get('src'):
            continue
            
        image_info = {
            'src': img['src'],
            'alt': img.get('alt', ''),
            'caption': img.get('caption', ''),
            'imagePrompt': img.get('imagePrompt', ''),
            'notes': img.get('notes', ''),
            'exists': False,
            'dimensions': None,
            'size': None
        }
        
        # Check if image file exists and get its details
        try:
            img_path = BASE_DIR / img['src'].lstrip('/')
            if img_path.exists():
                image_info['exists'] = True
                # Could add image dimensions and size here if needed
                image_info['size'] = img_path.stat().st_size
        except Exception as e:
            logging.error(f"Error getting image details for {img['src']}: {e}")
            
        detailed_images.append(image_info)
        
    return detailed_images

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main admin interface page, loading post data."""
    logging.info("Processing index route '/'...")
    posts_list = []
    posts_dir_path = BASE_DIR / POSTS_DIR_NAME
    workflow_status_path = DATA_DIR / WORKFLOW_STATUS_FILE

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

        for filename in sorted(os.listdir(posts_dir_path), reverse=True): # Sort in reverse for newest first
            if filename.endswith(".md"):
                file_path = posts_dir_path / filename
                logging.debug(f"Processing file: {filename}")
                try:
                    post_fm = frontmatter.load(file_path)
                    metadata = post_fm.metadata
                    slug = Path(filename).stem
                    title = metadata.get('title', f"Untitled ({slug})")
                    deleted = metadata.get('deleted', False)

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

                    # Add post data to list
                    posts_list.append({
                        'slug': slug,
                        'title': title,
                        'concept': metadata.get('concept', ''),
                        'clan_com_status': clan_com_status_display,
                        'headerImageId': metadata.get('headerImageId', slug),
                        'deleted': deleted,
                        'date': metadata.get('date', '')
                    })
                except Exception as e:
                    logging.error(f"Error processing markdown file {filename}: {e}", exc_info=True)

        # Sort by date, newest first
        posts_list.sort(key=lambda x: x['date'] if x['date'] else '', reverse=True)
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

@app.route('/api/create_post', methods=['POST'])
def create_post():
    """Creates a new blog post with the given core idea."""
    logging.info("Received request to create new post")
    data = request.get_json()
    if not data or 'core_idea' not in data:
        logging.error("Missing 'core_idea' in request body")
        return jsonify({"success": False, "error": "Missing 'core_idea' in request body"}), 400

    core_idea = data['core_idea'].strip()
    if not core_idea:
        logging.error("Empty 'core_idea' provided")
        return jsonify({"success": False, "error": "Empty 'core_idea' provided"}), 400

    # Generate a temporary slug with timestamp
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    slug = f"new-{timestamp}"

    # Create the markdown file
    posts_dir = BASE_DIR / POSTS_DIR_NAME
    md_file_path = posts_dir / f"{slug}.md"

    if md_file_path.exists():
        logging.error(f"Post with slug '{slug}' already exists")
        return jsonify({"success": False, "error": f"Post with slug '{slug}' already exists"}), 409

    # Create the markdown file with initial front matter
    try:
        with open(md_file_path, 'w') as f:
            f.write(f"""---
title: "New post"
concept: "{core_idea}"
layout: post.njk
date: {datetime.now().strftime('%Y-%m-%d')}
author: "default"
tags:
  - post
  - draft
headerImage:
  src: "/images/{slug}/header.jpg"
  alt: ""
  caption: ""
  imagePrompt: ""
  notes: ""
summary: |
  <p>Summary of the post will go here.</p>
sections:
  - heading: "Introduction"
    text: |
      <p>Introduction text will go here.</p>
    image:
      src: "/images/{slug}/intro.jpg"
      alt: ""
      caption: ""
      imagePrompt: ""
      notes: ""
conclusion:
  heading: "Conclusion"
  text: |
    <p>Conclusion text will go here.</p>
---

""")
        logging.info(f"Created new post file: {md_file_path}")

        # Create the images directory for this post
        images_dir = BASE_DIR / 'images' / slug
        images_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created images directory: {images_dir}")

        # Update workflow status with proper initialization
        workflow_status_path = DATA_DIR / WORKFLOW_STATUS_FILE
        workflow_data = load_json_data(workflow_status_path) or {}
        if slug not in workflow_data:
            workflow_data[slug] = {
                "stages": {
                    "conceptualisation": {
                        "status": "complete",
                        "last_updated": datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z',
                        "concept": core_idea
                    },
                    "authoring": {
                        "status": "pending",
                        "text_format_status": "pending"
                    },
                    "metadata": {
                        "status": "pending",
                        "front_matter_status": "pending",
                        "tags_status": "pending",
                        "author_status": "pending"
                    },
                    "images": {
                        "status": "pending",
                        "prompts_defined_status": "pending",
                        "generation_status": "pending",
                        "assets_prepared_status": "pending",
                        "metadata_integrated_status": "pending",
                        "watermarking_status": "pending",
                        "watermarking_used_in_publish": False,
                        "watermarks": {}
                    },
                    "validation": {
                        "status": "pending",
                        "last_preview_ok": False
                    },
                    "publishing_clancom": {
                        "status": "pending"
                    },
                    "syndication": {
                        "status": "pending",
                        "instagram": {
                            "overall_status": "pending"
                        },
                        "facebook": {
                            "overall_status": "pending"
                        }
                    }
                },
                "last_updated": datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z'
            }
        save_json_data(workflow_status_path, workflow_data)

        return jsonify({
            "success": True,
            "slug": slug,
            "message": f"Created new post with slug: {slug}"
        })

    except Exception as e:
        logging.error(f"Error creating new post: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/post/<slug>')
def view_post_detail(slug):
    """View and edit details for a specific post."""
    try:
        # Load the markdown file
        md_file_path = os.path.join(app.config['POSTS_DIR'], f"{slug}.md")
        if not os.path.exists(md_file_path):
            flash(f"Post file not found: {md_file_path}", "error")
            return redirect(url_for('index'))

        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Initialize workflow status for this post if needed
        workflow_status_path = Path(app.config['DATA_DIR']) / 'workflow_status.json'
        workflow_status = load_json_data(workflow_status_path) or {}
        if slug not in workflow_status:
            workflow_status[slug] = {'stages': {}}
        
        post_status = workflow_status[slug]
        
        # Initialize missing stages with default values
        for stage in WORKFLOW_STAGES:
            if stage not in post_status['stages']:
                post_status['stages'][stage] = {'status': 'pending'}
                if stage == 'images':
                    post_status['stages'][stage].update({
                        'prompts_defined_status': 'pending',
                        'generation_status': 'pending',
                        'assets_prepared_status': 'pending',
                        'metadata_integrated_status': 'pending',
                        'watermarking_status': 'pending',
                        'watermarking_used_in_publish': False,
                        'watermarks': {}
                    })
                elif stage == 'validation':
                    post_status['stages'][stage]['last_preview_ok'] = False
                elif stage == 'syndication':
                    post_status['stages'][stage].update({
                        'instagram': {'overall_status': 'pending'},
                        'facebook': {'overall_status': 'pending'}
                    })
        
        # Save the updated workflow status
        save_json_data(workflow_status_path, workflow_status)

        # Load authors data
        try:
            authors_file = os.path.join(app.config['DATA_DIR'], 'authors.json')
            app.logger.info(f"Loading authors from: {authors_file}")
            with open(authors_file, 'r', encoding='utf-8') as f:
                authors = json.load(f)
            app.logger.info(f"Loaded authors data: {authors}")
            app.logger.info(f"Authors type: {type(authors)}")
            app.logger.info(f"Authors has items() method: {hasattr(authors, 'items')}")
        except Exception as e:
            app.logger.error(f"Error loading authors: {e}")
            authors = {}

        # Load categories data
        try:
            categories_file = os.path.join(app.config['DATA_DIR'], 'categories.json')
            with open(categories_file, 'r', encoding='utf-8') as f:
                categories = json.load(f)
        except Exception as e:
            app.logger.error(f"Error loading categories: {e}")
            categories = {}

        # Parse the markdown content
        post_data = parse_post_markdown(content)
        
        # Get image details if available
        images_detailed = get_detailed_image_info(post_data.get('images', []))

        return render_template('admin_post_detail.html',
                            post=post_data,
                            slug=slug,
                            status=post_status,
                            authors=authors,
                            categories=categories,
                            images_detailed=images_detailed,
                            config=app.config)

    except Exception as e:
        logging.error(f"Error loading post details: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


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

            update_time = datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z'
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

        post_entry['last_updated'] = datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z'

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

@app.route('/api/delete_post/<string:slug>', methods=['POST'])
def delete_post(slug):
    """Marks a post as deleted by adding a deleted flag to its front matter."""
    try:
        md_file_path = BASE_DIR / POSTS_DIR_NAME / f"{slug}.md"
        if not md_file_path.exists():
            return jsonify({"success": False, "error": f"Post not found: {slug}"}), 404

        # Load the current front matter
        post = frontmatter.load(md_file_path)
        post.metadata['deleted'] = True

        # Save the updated front matter
        with open(md_file_path, 'w') as f:
            f.write(frontmatter.dumps(post))

        return jsonify({"success": True, "message": f"Post {slug} marked as deleted"})

    except Exception as e:
        logging.error(f"Error deleting post {slug}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/restore_post/<string:slug>', methods=['POST'])
def restore_post(slug):
    """Removes the deleted flag from a post's front matter."""
    try:
        md_file_path = BASE_DIR / POSTS_DIR_NAME / f"{slug}.md"
        if not md_file_path.exists():
            return jsonify({"success": False, "error": f"Post not found: {slug}"}), 404

        # Load the current front matter
        post = frontmatter.load(md_file_path)
        post.metadata['deleted'] = False

        # Save the updated front matter
        with open(md_file_path, 'w') as f:
            f.write(frontmatter.dumps(post))

        return jsonify({"success": True, "message": f"Post {slug} restored"})

    except Exception as e:
        logging.error(f"Error restoring post {slug}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update_metadata/<slug>', methods=['POST'])
def update_metadata(slug):
    """Update post metadata."""
    try:
        data = request.get_json()
        
        # Load the current post content
        post_path = os.path.join(app.config['POSTS_DIR'], f"{slug}.md")
        if not os.path.exists(post_path):
            return jsonify({"success": False, "error": "Post not found"}), 404
            
        post = frontmatter.load(post_path)
        
        # Update fields if they exist in the request
        fields_to_update = ['concept', 'title', 'subtitle', 'author', 'categories']
        for field in fields_to_update:
            if field in data:
                if field == 'categories':
                    # Convert category IDs to list if they're not already
                    categories = data[field] if isinstance(data[field], list) else [data[field]]
                    post.metadata[field] = categories
                else:
                    post.metadata[field] = data[field]
        
        # Save the updated content
        with open(post_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        # Update workflow status
        workflow_status = load_json_data(DATA_DIR / WORKFLOW_STATUS_FILE)
        if slug not in workflow_status:
            workflow_status[slug] = {'stages': {}}
        
        # Update the last_updated timestamp
        workflow_status[slug]['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00Z')
        
        # If this is a concept update, update the conceptualisation stage
        if 'concept' in data:
            if 'conceptualisation' not in workflow_status[slug]['stages']:
                workflow_status[slug]['stages']['conceptualisation'] = {}
            
            workflow_status[slug]['stages']['conceptualisation'].update({
                'status': 'complete',
                'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00Z'),
                'concept': data['concept']
            })
        
        # Update metadata stage if title, subtitle, or categories are updated
        if any(field in data for field in ['title', 'subtitle', 'categories']):
            if 'metadata' not in workflow_status[slug]['stages']:
                workflow_status[slug]['stages']['metadata'] = {}
            
            workflow_status[slug]['stages']['metadata'].update({
                'status': 'complete',
                'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00Z')
            })
        
        save_json_data(DATA_DIR / WORKFLOW_STATUS_FILE, workflow_status)
        
        return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Error updating metadata: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update_content/<string:slug>', methods=['POST'])
def update_content(slug):
    try:
        # Get the markdown file path
        markdown_file = os.path.join('posts', f'{slug}.md')
        
        if not os.path.exists(markdown_file):
            return jsonify({'success': False, 'error': 'Post not found'}), 404

        # Load the current content using frontmatter library
        post = frontmatter.load(markdown_file)
        
        # Update the content from the request
        data = request.get_json()
        
        # Update summary
        post.metadata['summary'] = data.get('summary', '')
        
        # Update sections
        post.metadata['sections'] = data.get('sections', [])
        
        # Update conclusion
        post.metadata['conclusion'] = data.get('conclusion', {
            'heading': '',
            'text': ''
        })

        # Write the updated content back to the file
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        # Update workflow status if all required fields are filled
        workflow_file = '_data/workflow_status.json'
        if os.path.exists(workflow_file):
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            if slug in workflow_data:
                # Check if all required fields are filled
                has_summary = bool(post.metadata.get('summary'))
                has_sections = bool(post.metadata.get('sections'))
                has_conclusion = bool(post.metadata.get('conclusion', {}).get('text'))
                
                if has_summary and has_sections and has_conclusion:
                    workflow_data[slug]['stages']['authoring']['status'] = 'complete'
                    workflow_data[slug]['stages']['authoring']['text_format_status'] = 'complete'
                else:
                    workflow_data[slug]['stages']['authoring']['status'] = 'pending'
                    workflow_data[slug]['stages']['authoring']['text_format_status'] = 'pending'
                
                with open(workflow_file, 'w', encoding='utf-8') as f:
                    json.dump(workflow_data, f, indent=2)

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error updating content for {slug}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/import_content/<string:slug>', methods=['POST'])
def import_content(slug):
    """Import content from an uploaded file."""
    try:
        if 'file' not in request.files:
            logging.error("No file provided in request")
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logging.error("No file selected")
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Secure the filename and save it
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        try:
            # Parse the content file
            from scripts.parse_content import parse_file
            parsed_content = parse_file(temp_path)
            
            # Get the post path
            post_path = os.path.join(app.config['POSTS_DIR'], f"{slug}.md")
            if not os.path.exists(post_path):
                logging.error(f"Post not found: {post_path}")
                return jsonify({'success': False, 'error': 'Post not found'}), 404
            
            # Load the existing post
            post = frontmatter.load(post_path)
            
            # Update the metadata with the new content
            if parsed_content.get('summary'):
                post.metadata['summary'] = parsed_content['summary']
            if parsed_content.get('sections'):
                post.metadata['sections'] = parsed_content['sections']
            if parsed_content.get('conclusion'):
                post.metadata['conclusion'] = parsed_content['conclusion']
            
            # Write the updated content back to the file
            with open(post_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            # Update workflow status
            workflow_data = load_json_data(DATA_DIR / WORKFLOW_STATUS_FILE)
            if workflow_data is None:
                workflow_data = {}
            
            if slug not in workflow_data:
                workflow_data[slug] = {'stages': {}}
            
            workflow_data[slug]['stages']['authoring'] = {
                'status': 'complete',
                'text_format_status': 'complete',
                'last_updated': datetime.utcnow().isoformat()
            }
            
            save_json_data(DATA_DIR / WORKFLOW_STATUS_FILE, workflow_data)
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            logging.info(f"Successfully imported content for post '{slug}'")
            return jsonify({
                'success': True,
                'summary': parsed_content.get('summary', ''),
                'sections': parsed_content.get('sections', []),
                'conclusion': parsed_content.get('conclusion', {})
            })
            
        except Exception as e:
            logging.error(f"Error processing file for post '{slug}': {str(e)}", exc_info=True)
            # Clean up the temporary file in case of error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return jsonify({'success': False, 'error': str(e)}), 500
            
    except Exception as e:
        logging.error(f"Error importing content for post '{slug}': {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug/authors')
def debug_authors():
    """Debug route to check authors data."""
    authors_path = os.path.join('_data', 'authors.json')
    if os.path.exists(authors_path):
        with open(authors_path, 'r') as f:
            try:
                authors = json.load(f)
                return jsonify({
                    'authors': authors,
                    'type': str(type(authors)),
                    'has_items': hasattr(authors, 'items'),
                    'keys': list(authors.keys()) if isinstance(authors, dict) else None
                })
            except json.JSONDecodeError as e:
                return jsonify({'error': f"Error decoding authors.json: {e}"})
    return jsonify({'error': f"Authors file not found at: {os.path.abspath(authors_path)}"})

# --- LLM Management Routes ---
@app.route('/admin/llm')
def llm_management():
    """LLM management interface."""
    try:
        # Load current LLM configuration
        configs = load_config()
        default_config = configs.get("default", LLMConfig(
            provider_type="ollama",
            model_name="mistral",
            api_base="http://localhost:11434",
            api_key=None
        ))

        # Create a metadata generator instance
        generator = MetadataGenerator()
        
        # Extract prompt templates from the generator methods
        example_content = "Example blog post content about Scottish heritage."
        example_title = "Example Current Title"
        
        # Get the prompts by calling the methods but extracting just the prompt part
        title_response = generator.generate_title(example_content, example_title)
        meta_desc_response = generator.generate_meta_description(example_content)
        keywords_response = generator.generate_keywords(example_content)

        prompts = {
            "title_generation": title_response.prompt if hasattr(title_response, 'prompt') else "Title generation prompt not available",
            "meta_description": meta_desc_response.prompt if hasattr(meta_desc_response, 'prompt') else "Meta description prompt not available",
            "keywords": keywords_response.prompt if hasattr(keywords_response, 'prompt') else "Keywords prompt not available"
        }

        return render_template('llm/admin_llm.html',
                            config=default_config,
                            prompts=prompts)
    except Exception as e:
        logging.error(f"Error loading LLM management interface: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/llm/config', methods=['POST'])
def update_llm_config():
    """Update LLM configuration."""
    try:
        data = request.get_json()
        
        # Create new config
        new_config = LLMConfig(
            provider_type=data.get('provider_type', 'ollama'),
            model_name=data.get('model_name', 'mistral'),
            api_base=data.get('api_base'),
            api_key=data.get('api_key')  # None if not provided
        )
        
        # Save configuration
        configs = {"default": new_config}
        save_config(configs, os.path.join(app.config['DATA_DIR'], 'llm_config.json'))
        
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error updating LLM config: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/llm/test', methods=['POST'])
def test_llm():
    """Test LLM with a prompt."""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({"success": False, "error": "No prompt provided"}), 400
            
        # Create a provider instance
        configs = load_config()
        provider = LLMFactory.create_provider(configs["default"])
        
        # Generate response
        response = provider.generate_text(prompt)
        if response.error:
            return jsonify({"success": False, "error": response.error}), 500
            
        return jsonify({
            "success": True,
            "response": response.text
        })
    except Exception as e:
        logging.error(f"Error testing LLM: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

# --- Run the App ---
if __name__ == '__main__':
    # Use port 5001 as specified
    app.run(debug=True, port=5001)