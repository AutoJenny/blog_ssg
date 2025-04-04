Briefing Summary: Image Processing Workflow & Metadata Association

Context:
We have developed a Python script (scripts/process_imported_image.py) designed to be the standard workflow for incorporating new images into the system. This script takes a raw input image (from _SOURCE_MEDIA/_IMPORT_IMAGES/) and performs the following actions:

Copies the original raw file to a designated backup location (images/posts/{slug}/..._raw.*).

Creates an optimized, unwatermarked "published" version (target format: WebP) in the main post image directory (images/posts/{slug}/...webp).

Creates a separate watermarked version (also WebP) in a dedicated directory (images/watermarked/...webp).

Registers the image by adding/updating an entry in the central _data/image_library.json file, including paths to all three versions and descriptive metadata (description, alt text, caption, optional AI prompt).

Deletes the original file from the import directory upon success.

Current Task & Point of Discussion:
We were working on implementing a UI button ("Process Imported Images") within the Admin Interface (/admin/post/<slug>) to trigger this process_imported_image.py script automatically for all relevant new images found in the import directory for that post slug.

The Core Issue / User Concern:
The current design of process_imported_image.py requires the descriptive metadata (description, alt, caption) to be provided as input arguments when it runs, because it performs the image registration (#4 above) simultaneously with the file processing (#1-3, #5).

To facilitate triggering this via a simple UI button, the proposed solution involved:

Manually creating a sidecar JSON file (_SOURCE_MEDIA/_IMPORT_IMAGES/image_metadata.json) containing the necessary metadata mapped to the raw filenames before clicking the button.

The API endpoint triggered by the button would read this sidecar file to get the metadata to pass to the script for each image.

The user feels this approach is incorrect, stating that associating the structured metadata (description, alt, caption) should happen at a different stage in the overall process, separate from the initial file format conversion, watermarking, and placement triggered by the UI button. The user desires the UI-triggered action to focus primarily on the file operations, with metadata handled elsewhere or later.

Next Steps Required:
Re-evaluate the image processing workflow. Determine the optimal point and method for capturing and associating descriptive metadata with image assets. Decide if the process_imported_image.py script should be split or modified:

Should the UI button trigger a script that only performs file operations (copy raw, create published webp, create watermarked webp, move to final locations) without updating image_library.json?

If so, how and when does the necessary metadata get added to image_library.json for these processed images before they are needed for deployment or other tasks? (e.g., via separate Admin UI editing features targeting the image library directly?)

Alternatively, is there a better way to provide the required metadata to the current combined script when triggered via the UI?