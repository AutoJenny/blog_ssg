#!/usr/bin/env python3

import os
import json
import logging
import argparse
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
# Find project base directory (assuming script is in BASE_DIR/scripts)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "_data"
IMAGE_LIBRARY_PATH = DATA_DIR / "image_library.json"
WORKFLOW_STATUS_PATH = DATA_DIR / "workflow_status.json" # To update individual status
DEFAULT_IMAGE_DIR = BASE_DIR / "images" / "posts" # Default if not specified in library

# Watermark settings
WATERMARK_TEXT = "© Clan.com"
FONT_SIZE_RATIO = 0.04 # Adjust font size relative to image width
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf" # Adjust path as needed for your system
TEXT_COLOR = (255, 255, 255, 100) # White with transparency
BACKGROUND_COLOR = (0, 0, 0, 100) # Semi-transparent black background
PADDING = 10 # Padding around text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions (from app.py, slightly adapted) ---
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
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading JSON data from {file_path}: {e}")
        return None

def save_json_data(file_path: Path, data: dict):
    """Saves the given dictionary as JSON to the specified absolute file path."""
    logging.info(f"Attempting to save JSON data to: {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Successfully saved JSON data to {file_path.name}.")
        return True
    except IOError as e:
        logging.error(f"IOError saving JSON data to {file_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error saving JSON data to {file_path}: {e}")
        return False

def add_watermark(image_path, output_path):
    """Adds a text watermark to an image and saves it."""
    try:
        img = Image.open(image_path).convert("RGBA") # Convert to RGBA for transparency
        width, height = img.size

        # Calculate font size
        font_size = max(12, int(width * FONT_SIZE_RATIO)) # Min size 12
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except IOError:
            logging.warning(f"Font not found at {FONT_PATH}. Using default font.")
            font = ImageFont.load_default() # Fallback font

        # Create drawing context
        draw = ImageDraw.Draw(img)

        # Calculate text size and position
        # Use textbbox for more accurate sizing
        bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position with padding (bottom right)
        x = width - text_width - PADDING * 2
        y = height - text_height - PADDING * 2

        # Draw semi-transparent background rectangle
        bg_rect_coords = [
            (x - PADDING, y - PADDING),
            (x + text_width + PADDING, y + text_height + PADDING)
        ]
        draw.rectangle(bg_rect_coords, fill=BACKGROUND_COLOR)

        # Draw the text
        draw.text((x, y), WATERMARK_TEXT, fill=TEXT_COLOR, font=font)

        # Save as JPG (handle transparency by converting back to RGB with white background)
        # Create a white background image
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3]) # Paste using alpha channel as mask

        bg.save(output_path, "JPEG", quality=90) # Save as JPG
        logging.info(f"Watermarked image saved to: {output_path}")
        return True

    except FileNotFoundError:
        logging.error(f"Image file not found for watermarking: {image_path}")
        return False
    except Exception as e:
        logging.error(f"Error applying watermark to {image_path}: {e}")
        return False

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Watermark specific images for a blog post.")
    parser.add_argument('--slug', required=True, help='The slug of the blog post.')
    parser.add_argument('--image-id', action='append', required=True, help='Image ID to process. Can be specified multiple times.')
    args = parser.parse_args()

    post_slug = args.slug
    image_ids_to_process = args.image_id

    logging.info(f"--- Starting Watermarking for post: {post_slug} ---")
    logging.info(f"Processing Image IDs: {', '.join(image_ids_to_process)}")

    image_library = load_json_data(IMAGE_LIBRARY_PATH)
    workflow_status = load_json_data(WORKFLOW_STATUS_PATH)
    if image_library is None or workflow_status is None:
        logging.critical("Failed to load essential data files (image library or workflow status). Aborting.")
        exit(1)

    # Ensure post entry exists in workflow status
    if post_slug not in workflow_status:
        workflow_status[post_slug] = {"stages": {}}
    if 'stages' not in workflow_status[post_slug]:
        workflow_status[post_slug]['stages'] = {}
    if 'images' not in workflow_status[post_slug]['stages']:
         workflow_status[post_slug]['stages']['images'] = {}
    if 'watermarks' not in workflow_status[post_slug]['stages']['images']:
        workflow_status[post_slug]['stages']['images']['watermarks'] = {}


    all_successful = True
    image_library_updated = False
    workflow_status_updated = False

    for img_id in image_ids_to_process:
        logging.info(f"--- Processing Image ID: {img_id} ---")
        img_details = image_library.get(img_id)

        if not img_details:
            logging.error(f"Image ID '{img_id}' not found in library {IMAGE_LIBRARY_PATH}. Skipping.")
            all_successful = False
            # Update status to error?
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error'
            workflow_status_updated = True
            continue

        source_details = img_details.get("source_details", {})
        filename_local = source_details.get("filename_local")
        local_dir_rel = source_details.get("local_dir", f"images/posts/{post_slug}") # Default path structure

        if not filename_local:
            logging.error(f"Missing 'filename_local' for image ID '{img_id}'. Skipping.")
            all_successful = False
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error'
            workflow_status_updated = True
            continue

        input_path = BASE_DIR / local_dir_rel.strip('/') / filename_local
        if not input_path.is_file():
            logging.error(f"Input image file not found: {input_path}. Skipping.")
            all_successful = False
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error'
            workflow_status_updated = True
            continue

        # Prepare paths
        original_stem = input_path.stem
        original_suffix = input_path.suffix
        output_dir = input_path.parent
        backup_filename = f"{original_stem}_raw{original_suffix}"
        backup_path = output_dir / backup_filename
        output_filename = f"{original_stem}.jpg" # Force JPG output
        output_path = output_dir / output_filename

        logging.info(f"Input: {input_path}")
        logging.info(f"Backup: {backup_path}")
        logging.info(f"Output: {output_path}")

        # 1. Backup original (only if backup doesn't exist)
        try:
            if not backup_path.exists():
                shutil.copy2(input_path, backup_path) # copy2 preserves metadata
                logging.info(f"Original backed up to: {backup_path}")
            else:
                logging.info(f"Backup file already exists: {backup_path}")
        except Exception as e:
            logging.error(f"Failed to backup original file {input_path}: {e}")
            all_successful = False
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error'
            workflow_status_updated = True
            continue # Don't proceed without backup

        # 2. Add watermark
        if add_watermark(input_path, output_path):
            logging.info(f"Successfully watermarked '{img_id}'")
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'complete'
            workflow_status_updated = True

            # 3. Update image library if suffix changed
            if original_suffix.lower() != ".jpg":
                logging.warning(f"Image '{img_id}' suffix changed from {original_suffix} to .jpg. Updating image library.")
                try:
                    image_library[img_id]['source_details']['filename_local'] = output_filename
                    image_library_updated = True
                    # Delete the old non-jpg file? Optional. For now, we leave it.
                    # if input_path.exists() and input_path != output_path:
                    #     input_path.unlink()
                    #     logging.info(f"Deleted original non-JPG file: {input_path}")

                except KeyError:
                     logging.error(f"Could not update filename in image library for '{img_id}' - structure issue?")
                     all_successful = False # Mark as failure if we can't update library
                     workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error' # Downgrade status
        else:
            logging.error(f"Failed to apply watermark for '{img_id}'.")
            all_successful = False
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error'
            workflow_status_updated = True


    # --- Save updated JSON files (if changes were made) ---
    if image_library_updated:
        if not save_json_data(IMAGE_LIBRARY_PATH, image_library):
            logging.critical("Failed to save updated image library!")
            all_successful = False # Critical failure

    if workflow_status_updated:
        if not save_json_data(WORKFLOW_STATUS_PATH, workflow_status):
            logging.critical("Failed to save updated workflow status!")
            all_successful = False # Critical failure

    logging.info(f"--- Watermarking finished for post: {post_slug} ---")

    if all_successful:
        logging.info("All requested images processed successfully (or skipped non-errors).")
        exit(0)
    else:
        logging.error("One or more errors occurred during watermarking.")
        exit(1)