#!/usr/bin/env python3

import os
import json
import logging
import argparse
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, UnidentifiedImageError # Keep ImageDraw for background

# --- Configuration ---
# Find project base directory (assuming script is in BASE_DIR/scripts)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "_data"
IMAGE_LIBRARY_PATH = DATA_DIR / "image_library.json"
WORKFLOW_STATUS_PATH = DATA_DIR / "workflow_status.json" # To update individual status
DEFAULT_IMAGE_DIR = BASE_DIR / "images" / "posts" # Default if not specified in library

# <<< --- Settings from OLD Script --- >>>
WATERMARK_PATH_REL = "images/site/clan-watermark.png" # Relative to BASE_DIR
WATERMARK_PATH = BASE_DIR / WATERMARK_PATH_REL
TARGET_WATERMARK_WIDTH = 200
OFFSET = 10
# Background settings
ADD_BACKGROUND = True
BACKGROUND_COLOR = (128, 128, 128) # RGB for grey
BACKGROUND_OPACITY = 0.5
# <<< --- End Old Script Settings --- >>>

# Internal Constant
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.tiff') # Added more common types

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions (Keep from current script) ---
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

# --- MODIFIED Watermark Function (Using Old Script Logic) ---
def add_watermark(image_path, output_path):
    """
    Adds an image watermark (with optional background) to an image and saves it.
    Uses global constants for watermark image, width, offset, background settings.

    Args:
        image_path (Path): Path to the main image.
        output_path (Path): Path to save the watermarked image (will be JPG).

    Returns:
        bool: True if successful, False otherwise.
    """
    if not WATERMARK_PATH.is_file():
        logging.error(f"Watermark image file not found: {WATERMARK_PATH}")
        return False

    try:
        # Use 'with' statement for automatic closing of files
        with Image.open(image_path).convert("RGBA") as base_image, \
             Image.open(WATERMARK_PATH).convert("RGBA") as watermark_image:

            # --- Resize Watermark ---
            wm_width, wm_height = watermark_image.size
            if wm_width == 0 or wm_height == 0:
                logging.error(f"Watermark dimensions invalid for {WATERMARK_PATH}")
                return False

            aspect_ratio = wm_height / wm_width
            new_wm_height = int(TARGET_WATERMARK_WIDTH * aspect_ratio)
            if new_wm_height == 0: new_wm_height = 1 # Ensure minimum height

            try:
                # Use Resampling.LANCZOS for high-quality resizing
                watermark_resized = watermark_image.resize((TARGET_WATERMARK_WIDTH, new_wm_height), Image.Resampling.LANCZOS)
            except AttributeError: # Fallback for older Pillow versions
                 logging.warning("Using fallback Image.LANCZOS resizing.")
                 watermark_resized = watermark_image.resize((TARGET_WATERMARK_WIDTH, new_wm_height), Image.LANCZOS)

            wm_resized_width, wm_resized_height = watermark_resized.size

            # --- Calculate Position ---
            base_width, base_height = base_image.size
            # Ensure watermark + offset doesn't exceed image dimensions
            pos_x = max(0, base_width - wm_resized_width - OFFSET)
            pos_y = max(0, base_height - wm_resized_height - OFFSET)
            position = (pos_x, pos_y)

            # --- Create Composite Layer ---
            # Start with a transparent layer the size of the base image
            composite_layer = Image.new('RGBA', base_image.size, (0, 0, 0, 0))

            # --- Draw Background (Optional) ---
            if ADD_BACKGROUND:
                draw = ImageDraw.Draw(composite_layer)
                # Define the rectangle for the background
                bg_rect_coords = [
                    position[0], position[1], # Top-left corner
                    position[0] + wm_resized_width, position[1] + wm_resized_height # Bottom-right corner
                ]
                # Calculate RGBA color for background
                bg_fill_color = BACKGROUND_COLOR + (int(255 * BACKGROUND_OPACITY),)
                # Draw the rectangle onto the composite layer
                draw.rectangle(bg_rect_coords, fill=bg_fill_color)
                del draw # Release draw object

            # --- Paste Watermark onto Composite Layer ---
            # Paste the resized watermark over the background (if any) on the composite layer
            composite_layer.paste(watermark_resized, position, watermark_resized) # Use mask for transparency

            # --- Composite onto Base Image ---
            watermarked_image = Image.alpha_composite(base_image, composite_layer)

            # --- Save as JPG (Force conversion) ---
            # Convert to RGB (implicitly handles transparency against white default bg if needed)
            final_image_rgb = watermarked_image.convert('RGB')
            final_image_rgb.save(output_path, "JPEG", quality=95) # Save as high-quality JPG
            logging.info(f"Watermarked image saved to: {output_path}")

            return True

    except FileNotFoundError:
        logging.error(f"Error: File not found during processing ({image_path} or {WATERMARK_PATH})")
        return False
    except UnidentifiedImageError:
        logging.error(f"Error: Cannot identify image file ({image_path})")
        return False
    except Exception as e:
        logging.error(f"Error applying watermark to {image_path}: {e}")
        return False

# --- Main Execution (Keep from current script) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Watermark specific images for a blog post.")
    parser.add_argument('--slug', required=True, help='The slug of the blog post.')
    parser.add_argument('--image-id', action='append', required=True, help='Image ID to process. Can be specified multiple times.')
    args = parser.parse_args()

    post_slug = args.slug
    image_ids_to_process = args.image_id

    logging.info(f"--- Starting Watermarking for post: {post_slug} ---")
    logging.info(f"Using watermark image: {WATERMARK_PATH}")
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
        workflow_status[post_slug]['stages']['images']['watermarks'] = {} # Store individual watermark status here


    all_successful = True
    image_library_updated = False
    workflow_status_updated = False

    for img_id in image_ids_to_process:
        logging.info(f"--- Processing Image ID: {img_id} ---")
        img_details = image_library.get(img_id)

        if not img_details:
            logging.error(f"Image ID '{img_id}' not found in library {IMAGE_LIBRARY_PATH}. Skipping.")
            all_successful = False
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error'
            workflow_status_updated = True
            continue

        source_details = img_details.get("source_details", {})
        filename_local = source_details.get("filename_local")
        # Use a safer default relative path construction
        local_dir_rel_str = source_details.get("local_dir", f"images/posts/{post_slug}")

        if not filename_local:
            logging.error(f"Missing 'filename_local' for image ID '{img_id}'. Skipping.")
            all_successful = False
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error'
            workflow_status_updated = True
            continue

        input_path = BASE_DIR / local_dir_rel_str.strip('/') / filename_local
        if not input_path.is_file():
            logging.error(f"Input image file not found: {input_path}. Skipping.")
            all_successful = False
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'error'
            workflow_status_updated = True
            continue

        # Check if file extension is supported *before* processing
        if not input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
             logging.warning(f"Skipping unsupported file extension: {input_path.suffix} for {input_path.name}")
             # Don't mark as error, just skip
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

        # 2. Add watermark using the image-based function
        if add_watermark(input_path, output_path):
            logging.info(f"Successfully watermarked '{img_id}'")
            workflow_status[post_slug]['stages']['images']['watermarks'][img_id] = 'complete'
            workflow_status_updated = True

            # 3. Update image library if suffix changed
            if original_suffix.lower() != ".jpg":
                logging.warning(f"Image '{img_id}' suffix changed from {original_suffix} to .jpg. Updating image library.")
                try:
                    # Ensure structure exists before updating
                    if 'source_details' not in image_library[img_id]:
                        image_library[img_id]['source_details'] = {}
                    image_library[img_id]['source_details']['filename_local'] = output_filename
                    image_library_updated = True

                    # Delete the old non-jpg file? Optional. Be careful here.
                    if input_path.exists() and input_path.resolve() != output_path.resolve():
                         try:
                             input_path.unlink()
                             logging.info(f"Deleted original non-JPG file: {input_path}")
                         except Exception as del_e:
                             logging.error(f"Failed to delete original non-JPG file {input_path}: {del_e}")


                except KeyError:
                     logging.error(f"Could not update filename in image library for '{img_id}' - ID might be missing unexpectedly?")
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
         # Update overall images stage status based on individual watermarks
        all_watermarked_complete = True
        for img_id in image_ids_to_process:
            if workflow_status[post_slug]['stages']['images']['watermarks'].get(img_id) != 'complete':
                all_watermarked_complete = False
                break
        # Only update the main status if ALL requested images were successfully watermarked
        if all_watermarked_complete and image_ids_to_process: # Check if list wasn't empty
             workflow_status[post_slug]['stages']['images']['watermarking_status'] = 'complete' # Set overall status
        else:
             # Keep existing overall status or set to partial/pending/error based on more complex logic if desired
             pass # For now, just update individual statuses

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