# /Users/nickfiddes/Code/projects/blog_ssg/app.py

from flask import Flask, render_template, jsonify # Added jsonify
import os
import json
from pathlib import Path
import frontmatter
import logging
import subprocess # Added subprocess
import sys

# --- Configuration ---
POSTS_DIR = "posts"
SYNDICATION_DATA_FILE = "_data/syndication.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent

# --- Helper Function ---
def load_syndication_data(file_path):
    """Loads the JSON data file."""
    try:
        abs_file_path = BASE_DIR / file_path
        logging.info(f"Attempting to load syndication data from: {abs_file_path}")
        with open(abs_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"Successfully loaded data for {len(data)} post slugs.")
            return data
    except FileNotFoundError:
        logging.warning(f"Syndication data file not found: {abs_file_path}. Returning empty data.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {abs_file_path}. Please check its format.")
        return None
    except Exception as e:
        logging.error(f"Error loading syndication data: {e}")
        return None

# --- Flask Routes ---
@app.route('/')
def index():
    """Renders the main admin interface page, loading post data."""
    # ... (logic from Phase 2 remains the same) ...
    logging.info("Processing index route '/'...")
    posts_list = []
    posts_dir_path = BASE_DIR / POSTS_DIR
    syndication_data_path = BASE_DIR / SYNDICATION_DATA_FILE
    syndication_data = load_syndication_data(syndication_data_path)
    if syndication_data is None:
        logging.error("Failed to load syndication data, post status will be unavailable.")
        syndication_data = {}

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
                    clan_com_post_id = syndication_data.get(slug, {}).get('clan_com_post_id')
                    clan_com_status = f"Published (ID: {clan_com_post_id})" if clan_com_post_id else "Not Published"
                    posts_list.append({'slug': slug, 'title': title, 'clan_com_status': clan_com_status})
                except Exception as e: logging.error(f"Error processing markdown file {filename}: {e}")
        posts_list.sort(key=lambda p: p['slug'])
        logging.info(f"Found and processed {len(posts_list)} posts.")
    except FileNotFoundError: logging.error(f"Posts directory not found: {posts_dir_path}")
    except Exception as e: logging.error(f"Error listing or processing posts directory: {e}")

    return render_template(
        'admin_index.html',
        posts=posts_list,
        config={'BASE_DIR': str(BASE_DIR)} # Pass BASE_DIR as a string
    )

# --- NEW API Endpoint ---
@app.route('/api/publish_clan/<string:slug>', methods=['POST'])
def publish_to_clan_api(slug):
    """Triggers the post_to_clan.py script for the given slug."""
    logging.info(f"Received request to publish/update slug: {slug}")

    script_path = str(BASE_DIR / 'post_to_clan.py')
    markdown_file_relative_path = f"{POSTS_DIR}/{slug}.md"
    markdown_file_abs_path = str(BASE_DIR / markdown_file_relative_path)

    if not os.path.exists(markdown_file_abs_path):
        logging.error(f"Markdown file not found for slug '{slug}': {markdown_file_abs_path}")
        return jsonify({"success": False, "output": f"Error: Markdown file not found at {markdown_file_relative_path}", "slug": slug}), 404

    # Construct command
    command = [
        sys.executable, # Use the same python interpreter running Flask
        script_path,
        markdown_file_relative_path # Pass relative path to the script
    ]
    logging.info(f"Executing command: {' '.join(command)}")

    try:
        # Execute the script
        # Use check=False so we capture output even if the script exits with an error code
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=BASE_DIR)

        # Combine stdout and stderr for the log
        output_log = f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"
        success = result.returncode == 0

        if success:
            logging.info(f"Script for slug '{slug}' completed successfully.")
        else:
            logging.error(f"Script for slug '{slug}' failed with return code {result.returncode}.")

        # Note: We are not reloading syndication data here to update status in *this* response.
        # The JavaScript could potentially trigger a page reload or a separate status update call if needed.
        return jsonify({"success": success, "output": output_log, "slug": slug})

    except FileNotFoundError:
        error_msg = f"Error: '{sys.executable}' or script '{script_path}' not found."
        logging.error(error_msg)
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 500
    except Exception as e:
        error_msg = f"An unexpected error occurred while running the script: {e}"
        logging.error(error_msg)
        return jsonify({"success": False, "output": error_msg, "slug": slug}), 500


# --- Run the App ---
if __name__ == '__main__':
    # Changed port to 5001
    app.run(debug=True, port=5001)