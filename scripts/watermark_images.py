import os
import sys
from PIL import Image, ImageDraw, UnidentifiedImageError
import argparse # Keep argparse just for the input directory

# --- Configuration ---
# <<< --- EDIT THIS VARIABLE FOR THE TARGET DIRECTORY --- >>>
DEFAULT_INPUT_DIRECTORY = "images/kilt-evolution" # Default if no argument provided
# <<< --- OTHER FIXED SETTINGS --- >>>
WATERMARK_PATH = "images/site/clan-watermark.png"
TARGET_WATERMARK_WIDTH = 200  # Baked in: 250px
OFFSET = 10                   # Baked in: 10px
# Background settings
ADD_BACKGROUND = True         # Set to False to disable background
BACKGROUND_COLOR = (128, 128, 128) # RGB for grey
BACKGROUND_OPACITY = 0.5      # 0.0 (transparent) to 1.0 (opaque) -> 50%

# --- Internal Constants ---
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png')

def add_watermark(image_path, watermark_path, output_path):
    """
    Adds a watermark (with optional background) to an image and saves it.

    Uses baked-in global constants for width, offset, background settings.

    Args:
        image_path (str): Path to the main image.
        watermark_path (str): Path to the watermark image.
        output_path (str): Path to save the watermarked image.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Use 'with' statement for automatic closing of files
        with Image.open(image_path).convert("RGBA") as base_image, \
             Image.open(watermark_path).convert("RGBA") as watermark_image:

            # --- Resize Watermark ---
            wm_width, wm_height = watermark_image.size
            if wm_width == 0 or wm_height == 0:
                print(f"    Error: Watermark dimensions invalid for {watermark_path}")
                return False

            aspect_ratio = wm_height / wm_width
            new_wm_height = int(TARGET_WATERMARK_WIDTH * aspect_ratio)
            if new_wm_height == 0: new_wm_height = 1 # Ensure minimum height

            try:
                # Use Resampling.LANCZOS for high-quality resizing
                watermark_resized = watermark_image.resize((TARGET_WATERMARK_WIDTH, new_wm_height), Image.Resampling.LANCZOS)
            except AttributeError: # Fallback for older Pillow versions
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
                # Delete draw object (good practice, though maybe not strictly needed here)
                del draw

            # --- Paste Watermark onto Composite Layer ---
            # Paste the resized watermark over the background (if any) on the composite layer
            composite_layer.paste(watermark_resized, position, watermark_resized) # Use mask for transparency

            # --- Composite onto Base Image ---
            watermarked_image = Image.alpha_composite(base_image, composite_layer)

            # --- Save ---
            # Handle different save formats
            file_ext = os.path.splitext(output_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg']:
                watermarked_image.convert('RGB').save(output_path, "JPEG", quality=95)
            else:
                watermarked_image.save(output_path)

            return True

    except FileNotFoundError:
        print(f"    Error: File not found ({image_path} or {watermark_path})")
        return False
    except UnidentifiedImageError:
        print(f"    Error: Cannot identify image file ({image_path})")
        return False
    except Exception as e:
        print(f"    Error processing {image_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Add a watermark to images in a directory.")
    # Only argument is the input directory, with a default
    parser.add_argument("directory", nargs='?', default=DEFAULT_INPUT_DIRECTORY,
                        help=f"Directory containing images to watermark (default: {DEFAULT_INPUT_DIRECTORY}).")

    args = parser.parse_args()
    input_directory = args.directory

    # --- Validate Inputs ---
    if not os.path.isdir(input_directory):
        print(f"Error: Input directory not found: {input_directory}")
        sys.exit(1)
    if not os.path.isfile(WATERMARK_PATH):
        print(f"Error: Watermark file not found: {WATERMARK_PATH}")
        sys.exit(1)

    # --- Calculate and Create Output Directory ---
    output_directory = f"{input_directory}-watermarked"
    if not os.path.exists(output_directory):
         print(f"Output directory {output_directory} not found, creating it.")
         os.makedirs(output_directory) # exist_ok=True is default in Python 3.2+
    else:
         print(f"Output directory {output_directory} already exists.")


    # --- Process Images ---
    print(f"\nProcessing images in: {input_directory}")
    print(f"Using watermark: {WATERMARK_PATH}")
    print(f"Watermark target width: {TARGET_WATERMARK_WIDTH}px, Offset: {OFFSET}px")
    if ADD_BACKGROUND:
        print(f"Adding background: Color {BACKGROUND_COLOR}, Opacity {BACKGROUND_OPACITY*100:.0f}%")
    print(f"Saving watermarked images to: {output_directory}")
    print("-" * 30)

    processed_count = 0
    skipped_count = 0

    for filename in os.listdir(input_directory):
        # Check if it's a file and has a supported extension
        file_path = os.path.join(input_directory, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(SUPPORTED_EXTENSIONS):
            print(f"Processing {filename}...")
            output_filename = os.path.join(output_directory, filename)

            if add_watermark(file_path, WATERMARK_PATH, output_filename):
                processed_count += 1
            else:
                skipped_count += 1
        elif os.path.isfile(file_path):
             print(f"Skipping unsupported file: {filename}")
        # else: it's a directory, skip silently


    print("-" * 30)
    print(f"Finished. Processed: {processed_count}, Skipped/Errors: {skipped_count}")

if __name__ == "__main__":
    main()