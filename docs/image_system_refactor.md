# Implementation Plan: Refactor Image Management & Data Structure

**Goal:** Rearchitecture the system to use a central JSON file (`_data/image_library.json`) for all image metadata, reference images via unique IDs in posts, implement a globally unique filename convention, and update Eleventy templates and Python scripts accordingly.

**Filename Convention:**

* **Local:** `images/posts/<post-slug>/<post-slug>_<semantic-name>.jpg|png|webp`
* **Server Path (API Submit):** `/blog/<post-slug>_<semantic-name>.jpg|png|webp`
* **Public URL (HTML `src`):** `https://static.clan.com/media/blog/<post-slug>_<semantic-name>.jpg|png|webp`

---

## Phase 1: Prepare New Data Structure & Migrate Existing Post

* [X] **1.1. Define Unique Image IDs:**
  * Decide on an ID format (e.g., sequential `IMG00001`, `IMG00002` or UUIDs). Let's use sequential for simplicity initially.
  * Assign unique IDs to all 11 images currently associated with the `kilt-evolution` post (IMG00001 to IMG00011).
* [X] **1.2. Define New Semantic Filenames:**
  * Determine the unique, semantic filenames for the 11 kilt images using the new convention (e.g., `kilt-evolution_header.jpg`, `kilt-evolution_early-highland-dress.jpg`, etc.).
* [X] **1.3. Create `_data/image_library.json`:**
  * Create the file `_data/image_library.json`.
  * Initialize it with an empty JSON object `{}` or populate it directly in the next step.
* [ ] **1.4. Populate `image_library.json` for Kilt Post:**
  * Create entries for IMG00001 through IMG00011.
  * For each entry:
    * Migrate `description` (create a short internal one).
    * Set initial `status`, `prompt_status`, `generation_status`, `watermark_status` (e.g., "complete" or "pending" as appropriate).
    * Migrate `prompt` from the `.md` file's front matter.
    * Set `source_details`:
      * `filename_local`: Use the *new* unique semantic filename (from 1.2).
      * `post_slug`: "kilt-evolution"
      * `local_dir`: "/images/posts/kilt-evolution/" (*Assuming you rename the existing `images/kilt-evolution` to `images/posts/kilt-evolution`*)
      * `public_url`: `null`
      * `uploaded_path_relative`: `null`
    * Set `metadata`:
      * Migrate `alt` from `.md` front matter.
      * Migrate `blog_caption` from `.md` front matter's `image.caption`.
    * Set `syndication`: Copy/adapt structure from previous `syndication.json` if needed, set initial statuses.
    * Migrate `notes` from `.md` front matter if present.
* [ ] **1.5. Rename/Move Local Image Files:**
  * **Create `images/posts/` directory:** `mkdir -p images/posts`
  * **Rename existing directory:** `mv images/kilt-evolution images/posts/kilt-evolution`
  * **Rename files within `images/posts/kilt-evolution/`** to match the new `filename_local` values defined in step 1.2 and stored in `image_library.json`. Use `mv` commands.
* [ ] **1.6. Update `kilt-evolution.md` Front Matter:**
  * Remove the detailed `headerImage` object and replace with `headerImageId: "IMG00001"`.
  * For each item in the `sections` array:
    * Remove the `image` object.
    * Remove the `imagePrompt` and `notes` keys (they are now in `image_library.json`).
    * Add the corresponding `imageId: "IMGXXXXX"` reference.
* [ ] **1.7. Commit Initial Refactoring:**
  * Stage changes (`_data/image_library.json`, `posts/kilt-evolution.md`, the renamed image files/directory).
  * `git add .`
  * `git commit -m "refactor(data): Implement image_library.json and migrate kilt post"`
  * `git push origin main`

---

## Phase 2: Update Eleventy Templates

* [ ] **2.1. Load Image Library Data (`.eleventy.js`):**
  * Ensure Eleventy automatically loads `_data/image_library.json` into a global `image_library` variable (Eleventy does this by default for files in `_data`). No change likely needed here, but verify data is accessible.
* [ ] **2.2. Update Post Template (`_includes/post.njk`):**
  * Modify the `<img>` tag generation for both `headerImage` and `sections` images:
    * Use `{% if headerImageId and image_library[headerImageId] %}` (and similar for `section.imageId`).
    * Get the image data: `{% set imgData = image_library[the_image_id] %}`.
    * Construct the `src` using the local path: `src="{{ (imgData.source_details.local_dir + imgData.source_details.filename_local) | url }}"`.
    * Use `imgData.metadata.alt` for the `alt` attribute.
    * Use `imgData.metadata.blog_caption` for the `<figcaption>`.
* [ ] **2.3. Test Local Preview:**
  * Run `npm start`.
  * Check the `kilt-evolution` post preview (`http://localhost:8080/kilt-evolution/`).
  * Verify all images load correctly from their new local paths based on the lookup from `image_library.json`. Check image alt text and captions are correct. Check browser console for errors.

---

## Phase 3: Update Python Scripts

* [ ] **3.1. Update `upload_image_to_clan` (`post_to_clan.py`):**
  * Modify the function to accept the *image ID* instead of the local path.
  * Inside the function:
    * Load `image_library.json`.
    * Look up the image ID to get `local_dir` and `filename_local`.
    * Construct the full local path: `BASE_DIR / local_dir.strip('/') / filename_local`.
    * Perform the upload using this path.
    * On success, parse the public URL, extract the filename, construct the relative submit path (`/blog/<unique_filename>.jpg`).
    * **Crucially:** *Update* the `image_library` data structure in memory with the `public_url` and `uploaded_path_relative` for the processed image ID.
    * Return the relative submit path (`/blog/...`) *and* potentially the updated `image_library` data (or handle saving globally). *Let's simplify: the main function will handle saving the updated data.* Just return the submit path.
* [ ] **3.2. Update `_add_thumbnails_to_args` (`post_to_clan.py`):**
  * Modify this function:
    * Get the `headerImageId` from `post_metadata`.
    * Look up this `headerImageId` in the *updated* `image_library` data (passed from `main`) to get the `uploaded_path_relative`.
    * Use this path for the `list_thumbnail` and `post_thumbnail` args.
* [ ] **3.3. Update `extract_html_content` (`post_to_clan.py`):**
  * Modify the image rewriting logic:
    * When an `<img>` tag is found, get its *local* `src` (e.g., `/images/posts/kilt-evolution/kilt-evolution_header.jpg`).
    * Extract the unique filename (`kilt-evolution_header.jpg`).
    * Construct the full *public* URL (`https://static.clan.com/media/blog/kilt-evolution_header.jpg`).
    * Update the `src` attribute in the HTML soup.
* [ ] **3.4. Update `main` Function (`post_to_clan.py`):**
  * **Image Upload Loop:**
    * Read the `.md` file to get the list of required `imageId`s (`headerImageId` and `section.imageId`s).
    * Load the *initial* `image_library.json` data.
    * Loop through the required `imageId`s:
      * Call `upload_image_to_clan(image_id)`.
      * Store the returned relative submit path (`/blog/...`) in the `uploaded_image_map`, keyed by the original *image ID*.
      * *After* the loop, update the `public_url` and `uploaded_path_relative` fields in the main `image_library` data structure based on the success/results of the uploads. **Save the updated `image_library.json` file.**
  * **Prepare API Args:** Pass the `uploaded_image_map` (keyed by image ID) and the full `image_library` data to `_prepare_api_args` and `_add_thumbnails_to_args` if they need to look up details by ID.
  * **Pass Correct Data to Helpers:** Ensure `_prepare_api_args` and `_add_thumbnails_to_args` are correctly accessing metadata (like `headerImageId`) from `post_metadata` and looking up details in the `image_library` data or `uploaded_image_map` as needed.
* [ ] **3.5. Update `watermark_images.py` (Basic):**
  * Modify the script to optionally accept an `image_id` instead of/in addition to a directory.
  * If an ID is provided, load `image_library.json`, find the entry, get the `local_dir` and `filename_local` to construct the input path.
  * Determine the output path (e.g., using a `-watermarked` suffix on the directory or filename).
  * (Further integration with status updates in `image_library.json` can come later).

---

## Phase 4: Testing End-to-End

* [ ] **4.1. Clear Remote State:** Manually delete the `kilt-evolution` post on `clan.com` again OR ensure the `clan_com_post_id` for it is removed from `_data/workflow_status.json`.
* [ ] **4.2. Clear Image Library State:** Set `public_url` and `uploaded_path_relative` back to `null` for all kilt images in `_data/image_library.json`.
* [ ] **4.3. Run Full Process via Interface:**
  * Start Flask app (`python3 app.py`).
  * Go to `/admin/post/kilt-evolution`.
  * Click "Publish/Update Clan.com".
* [ ] **4.4. Verify:**
  * Check script logs in the UI for successful image uploads (logging the correct `/blog/...` path) and successful `createPost`.
  * Verify the new `clan_com_post_id` is saved in `_data/workflow_status.json`.
  * Verify the `public_url` and `uploaded_path_relative` fields are updated in `_data/image_library.json`.
  * Check the live post on `clan.com/blog` - verify content AND all images load correctly using the `https://static.clan.com/...` URLs, and thumbnails are present.
* [ ] **4.5. Test Edit:** Run the "Publish/Update Clan.com" action again. Verify it correctly identifies the existing ID and performs an *edit* successfully.

---
