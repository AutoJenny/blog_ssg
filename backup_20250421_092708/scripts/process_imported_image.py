#!/usr/bin/env python3

import os
import sys
import argparse
import json
import logging
from pathlib import Path
import shutil
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError # Added UnidentifiedImageError, ImageDraw

# --- Define Base Directory ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
# --- End Base Directory Definition ---

# --- Configuration ---
# Input/Output Structure
IMPORT_DIR = BASE_DIR / "_SOURCE_MEDIA/_IMPORT_IMAGES"
RAW_OUTPUT_DIR_TEMPLATE = "images/posts/{slug}" # Relative to BASE_DIR
PUBLISHED_OUTPUT_DIR_TEMPLATE = "images/posts/{slug}" # Relative to BASE_DIR
WATERMARKED_OUTPUT_DIR = BASE_DIR / "images/watermarked" # Central dir for watermarked
IMAGE_LIBRARY_FILE = BASE_DIR / "_data/image_library.json"

# Processing Parameters
PUBLISHED_FORMAT = "WEBP" # Target format (WEBP, JPEG, PNG)
PUBLISHED_QUALITY = 85 # Quality setting for WEBP/JPEG (0-100)
MAX_WIDTH = 1200 # Resize images wider than this (pixels), None to disable

# <<< --- Watermark Settings from OLD Script --- >>>
WATERMARK_PATH_REL = "images/site/clan-watermark.png" # Relative to BASE_DIR
WATERMARK_PATH = BASE_DIR / WATERMARK_PATH_REL # Absolute path to watermark image
TARGET_WATERMARK_WIDTH = 200 # Resize watermark to this width
OFFSET = 15 # Pixel offset from bottom-right corner
# Background settings for watermark
ADD_BACKGROUND = True # Whether to add semi-transparent background behind watermark
BACKGROUND_COLOR = (128, 128, 128) # RGB for grey background
BACKGROUND_OPACITY = 0.5 # Opacity for background (0.0 to 1.0)
# <<< --- End Old Script Settings --- >>>
# --- End Configuration ---


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - SCRIPT(process_img) - %(message)s', stream=sys.stderr)
# --- End Logging Setup ---


# --- Helper Functions --- (Keep load_json_data, save_json_data as before)
def load_json_data(file_path: Path):
    # ... (same as previous version) ...
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
        logging.error(f"Unexpected error loading JSON data from {file_path}: {e}", exc_info=True)
        return None

def save_json_data(file_path: Path, data: dict):
    # ... (same as previous version) ...
    logging.info(f"Attempting to save JSON data to: {file_path}")
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Data saved successfully to {file_path.name}")
        return True
    except IOError as e:
        logging.error(f"IOError saving JSON data to {file_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error saving JSON data to {file_path}: {e}", exc_info=True)
        return False

# --- UPDATED Watermark Function (Using Old Script's Image Logic) ---
def apply_watermark(image: Image.Image):
    """
    Applies an IMAGE watermark (with optional background) to the given Pillow image object.
    Uses global constants for watermark image, width, offset, background settings.
    Returns the watermarked image object.
    """
    logging.info(f"Applying image watermark from: {WATERMARK_PATH}...")
    if not WATERMARK_PATH.is_file():
        logging.error(f"Watermark image file not found: {WATERMARK_PATH}. Skipping watermark.")
        return image # Return original if watermark file missing

    try:
        # Ensure base image is RGBA for compositing
        base_image_rgba = image.convert("RGBA")

        # Use 'with' for watermark image loading
        with Image.open(WATERMARK_PATH).convert("RGBA") as watermark_image:

            # --- Resize Watermark ---
            wm_width, wm_height = watermark_image.size
            if wm_width == 0 or wm_height == 0:
                logging.error(f"Watermark dimensions invalid for {WATERMARK_PATH}. Skipping watermark.")
                return image # Return original

            aspect_ratio = wm_height / wm_width
            new_wm_height = int(TARGET_WATERMARK_WIDTH * aspect_ratio)
            if new_wm_height == 0: new_wm_height = 1 # Ensure minimum height

            try: # Use modern resampling if available
                watermark_resized = watermark_image.resize((TARGET_WATERMARK_WIDTH, new_wm_height), Image.Resampling.LANCZOS)
            except AttributeError: # Fallback for older Pillow
                 logging.warning("Using fallback Image.LANCZOS resizing for watermark.")
                 watermark_resized = watermark_image.resize((TARGET_WATERMARK_WIDTH, new_wm_height), Image.LANCZOS)

            wm_resized_width, wm_resized_height = watermark_resized.size

            # --- Calculate Position ---
            base_width, base_height = base_image_rgba.size
            pos_x = max(0, base_width - wm_resized_width - OFFSET)
            pos_y = max(0, base_height - wm_resized_height - OFFSET)
            position = (pos_x, pos_y)

            # --- Create Composite Layer ---
            composite_layer = Image.new('RGBA', base_image_rgba.size, (0, 0, 0, 0)) # Transparent layer

            # --- Draw Background (Optional) ---
            if ADD_BACKGROUND:
                draw = ImageDraw.Draw(composite_layer)
                bg_rect_coords = [ position[0], position[1], position[0] + wm_resized_width, position[1] + wm_resized_height ]
                # Calculate RGBA color with opacity
                bg_fill_color = BACKGROUND_COLOR + (int(255 * BACKGROUND_OPACITY),)
                draw.rectangle(bg_rect_coords, fill=bg_fill_color)
                del draw # Release draw object
                logging.debug("Added watermark background.")

            # --- Paste Watermark onto Composite Layer ---
            # Paste using the watermark itself as the mask for transparency
            composite_layer.paste(watermark_resized, position, watermark_resized)
            logging.debug("Pasted watermark image onto composite layer.")

            # --- Composite onto Base Image ---
            watermarked_image = Image.alpha_composite(base_image_rgba, composite_layer)
            logging.info("Watermark applied successfully.")

            # --- Convert back to original mode if appropriate ---
            # If the original was RGB, convert back to avoid saving RGBA unnecessarily
            if image.mode == 'RGB':
                logging.debug("Converting final watermarked image back to RGB mode.")
                return watermarked_image.convert('RGB')
            else:
                # Keep as RGBA if original had transparency or if saving format supports it (like WEBP/PNG)
                return watermarked_image

    except FileNotFoundError:
        logging.error(f"Error: Watermark file not found during processing: {WATERMARK_PATH}")
        return image # Return original
    except UnidentifiedImageError:
        logging.error(f"Error: Cannot identify watermark image file: {WATERMARK_PATH}")
        return image # Return original
    except Exception as e:
        logging.error(f"Error applying image watermark: {e}", exc_info=True)
        return image # Return original on error


# --- Main Processing Function ---
def process_image(input_path_str: str, slug: str, filename_base: str, description: str, alt_text: str, blog_caption: str, prompt: str = ""):
    """Processes the image: copies raw, optimizes, watermarks, updates library."""
    input_path = Path(input_path_str)
    logging.info(f"--- Processing image for slug: '{slug}', base: '{filename_base}' ---")
    logging.info(f"Input file: {input_path}")

    if not input_path.is_file():
        logging.error(f"Input file not found: {input_path}")
        return False

    # 1. Derive ID and Output Paths
    image_id = f"{slug}_{filename_base}"
    logging.info(f"Generated Image ID: {image_id}")

    raw_output_dir = BASE_DIR / RAW_OUTPUT_DIR_TEMPLATE.format(slug=slug)
    published_output_dir = BASE_DIR / PUBLISHED_OUTPUT_DIR_TEMPLATE.format(slug=slug)
    raw_filename = f"{image_id}_raw{input_path.suffix}" # Keep original suffix for raw
    raw_output_path_abs = raw_output_dir / raw_filename
    # Published/Watermarked use target format (e.g., .webp)
    published_filename = f"{image_id}.{PUBLISHED_FORMAT.lower()}"
    published_output_path_abs = published_output_dir / published_filename
    watermarked_output_path_abs = WATERMARKED_OUTPUT_DIR / published_filename # Store watermarked centrally

    logging.info(f"  Raw output target: {raw_output_path_abs}")
    logging.info(f"  Published output target: {published_output_path_abs}")
    logging.info(f"  Watermarked output target: {watermarked_output_path_abs}")

    # 2. Ensure Output Directories Exist
    try:
        raw_output_dir.mkdir(parents=True, exist_ok=True)
        published_output_dir.mkdir(parents=True, exist_ok=True)
        WATERMARKED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.error(f"Error creating output directories: {e}")
        return False

    img = None
    success_flag = True

    try:
        # 3. Save Raw Copy
        logging.info(f"Copying original to raw path: {raw_output_path_abs}...")
        shutil.copy2(input_path, raw_output_path_abs)
        logging.info("  Raw copy saved.")

        # 4. Load Image with Pillow
        logging.info("Loading image with Pillow...")
        img = Image.open(input_path)
        if img.mode not in ['RGB', 'RGBA']:
            logging.info(f"  Converting image mode from {img.mode} to RGB for processing.")
            img = img.convert('RGB')
        original_format = img.format
        logging.info(f"  Image loaded (Format: {original_format}, Mode: {img.mode}, Size: {img.size}).")

        # 5. Optimize & Save Published Version
        img_processed = img.copy()

        # Resize
        if MAX_WIDTH and img_processed.width > MAX_WIDTH:
            logging.info(f"  Resizing image width from {img_processed.width} to {MAX_WIDTH}...")
            aspect_ratio = img_processed.height / img_processed.width
            new_height = int(MAX_WIDTH * aspect_ratio)
            try: # Use modern resampling
                img_processed = img_processed.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            except AttributeError: # Fallback
                 img_processed = img_processed.resize((MAX_WIDTH, new_height), Image.LANCZOS)
            logging.info(f"  Resized image size: {img_processed.size}")

        # Prepare save options
        save_options = {}
        if PUBLISHED_FORMAT.upper() in ["JPEG", "JPG", "WEBP"]:
            save_options['quality'] = PUBLISHED_QUALITY
        if PUBLISHED_FORMAT.upper() == "WEBP":
            save_options['lossless'] = False # Use lossy for webp usually

        # Save (Convert to RGB if saving as JPEG from RGBA)
        img_to_save = img_processed
        if img_processed.mode == 'RGBA' and PUBLISHED_FORMAT.upper() in ['JPEG', 'JPG']:
             logging.info("  Converting RGBA to RGB before saving published as JPEG.")
             img_to_save = img_processed.convert('RGB')

        logging.info(f"Saving optimized/published version to {published_output_path_abs} (Format: {PUBLISHED_FORMAT})...")
        img_to_save.save(published_output_path_abs, format=PUBLISHED_FORMAT, **save_options)
        logging.info("  Published version saved.")

        # 6. Apply **IMAGE** Watermark & Save Watermarked Version
        # Apply watermark to the potentially resized/converted image (img_processed)
        img_watermarked = apply_watermark(img_processed.copy()) # Use updated function

        # Save watermarked version (use same format and options as published)
        # Convert back to RGB if necessary (apply_watermark tries to do this already if original was RGB)
        img_wm_to_save = img_watermarked
        if img_watermarked.mode == 'RGBA' and PUBLISHED_FORMAT.upper() in ['JPEG', 'JPG']:
            logging.info("  Converting watermarked RGBA to RGB before saving as JPEG.")
            img_wm_to_save = img_watermarked.convert('RGB')

        logging.info(f"Saving watermarked version to {watermarked_output_path_abs} (Format: {PUBLISHED_FORMAT})...")
        img_wm_to_save.save(watermarked_output_path_abs, format=PUBLISHED_FORMAT, **save_options)
        logging.info("  Watermarked version saved.")

        # 7. Update Image Library JSON
        logging.info("Updating image library JSON file...")
        image_library_data = load_json_data(IMAGE_LIBRARY_FILE)
        if image_library_data is None:
            logging.error("Failed to load image library data for update. Aborting JSON update.")
            success_flag = False
        else:
            raw_relative = Path(os.path.relpath(raw_output_path_abs, BASE_DIR)).as_posix()
            published_relative = Path(os.path.relpath(published_output_path_abs, BASE_DIR)).as_posix()
            watermarked_relative = Path(os.path.relpath(watermarked_output_path_abs, BASE_DIR)).as_posix()

            image_entry = {
                "id": image_id,
                "description": description,
                "prompt": prompt or "",
                "metadata": { "alt": alt_text, "blog_caption": blog_caption },
                "source_details": {
                    "original_import_path": str(input_path),
                    "raw_file_path": raw_relative,
                    "published_file_path": published_relative, # Path to optimized, UNwatermarked
                    "published_format": PUBLISHED_FORMAT.lower(),
                    "watermarked_file_path": watermarked_relative # Path to watermarked version
                }
            }
            image_library_data[image_id] = image_entry
            if save_json_data(IMAGE_LIBRARY_FILE, image_library_data):
                logging.info("  Image library JSON updated successfully.")
            else:
                logging.error("  Failed to save updated image library JSON!")
                success_flag = False

    except FileNotFoundError as e:
        logging.error(f"File not found during processing: {e}")
        success_flag = False
    except UnidentifiedImageError as e:
         logging.error(f"Cannot identify image file (corrupted or unsupported format?): {input_path} - {e}")
         success_flag = False
    except Exception as e:
        logging.error(f"An error occurred during image processing: {e}", exc_info=True)
        success_flag = False
    finally:
        if img: img.close() # Ensure image file handle is closed

    # 8. Cleanup Input File ONLY if successful
    if success_flag:
        try:
            logging.info(f"Processing successful. Deleting original input file: {input_path}")
            os.remove(input_path)
            logging.info("  Input file deleted.")
        except OSError as e:
            logging.error(f"Error deleting input file {input_path}: {e}")
    else:
        logging.warning(f"Processing finished with errors. Original input file NOT deleted: {input_path}")

    logging.info(f"--- Finished processing for image ID: {image_id} ---")
    return success_flag


# --- Main Execution --- (Keep argparse and call to process_image as before)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an imported image: copy raw, optimize, watermark, and update image library.")
    parser.add_argument("input_image_path", help="Path to the raw input image file (e.g., _SOURCE_MEDIA/_IMPORT_IMAGES/my_raw_image.png).")
    parser.add_argument("--slug", required=True, help="Blog post slug this image belongs to (e.g., 'kilt-evolution').")
    parser.add_argument("--base-name", required=True, help="Descriptive base name for the output files (e.g., 'header-collage', 'early-origins').")
    parser.add_argument("--desc", required=True, help="Image description for the library.")
    parser.add_argument("--alt", required=True, help="Alt text for accessibility.")
    parser.add_argument("--caption", required=True, help="Caption to potentially use in the blog.")
    parser.add_argument("--prompt", default="", help="Optional: Prompt used for AI image generation.")

    args = parser.parse_args()

    if not Path(args.input_image_path).is_file():
        print(f"ERROR: Input image file not found: {args.input_image_path}", file=sys.stderr)
        sys.exit(1)

    success = process_image(
        input_path_str=args.input_image_path,
        slug=args.slug,
        filename_base=args.base_name,
        description=args.desc,
        alt_text=args.alt,
        blog_caption=args.caption,
        prompt=args.prompt
    )

    if success:
        print(f"SUCCESS: Image '{args.input_image_path}' processed successfully for ID '{args.slug}_{args.base_name}'.")
        sys.exit(0)
    else:
        print(f"ERROR: Image processing failed for '{args.input_image_path}'. Check logs above.", file=sys.stderr)
        sys.exit(1)