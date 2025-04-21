# Technical Briefing: AutoJenny/blog_ssg Project (Updated)

## 1. Overview

This document provides a technical overview of the `AutoJenny/blog_ssg` GitHub repository. The project is a static site generator (SSG) setup for building and deploying a blog, intended for the website `clan.com`. It utilizes Eleventy (11ty) as its core engine. It is supplemented by Python scripts for auxiliary tasks (deployment, **structured image processing**) and includes a local **Flask-based admin interface (`app.py`)** for monitoring content status, viewing post details, and managing workflow stages (via API).

## 2. Technology Stack

*   **Core SSG:** Node.js, Eleventy (11ty)
*   **Configuration:** JavaScript (`.eleventy.js`), Environment Variables (`.env`)
*   **Templating:** Nunjucks (`.njk`), Markdown (`.md`)
*   **Content:** Markdown files with YAML Front Matter
*   **Data Management:** JSON (`_data/`, specifically `image_library.json`, `workflow_status.json`), JavaScript (`*.11tydata.js`)
*   **Styling:** CSS (`css/`)
*   **Node.js Dependencies:** Managed via `package.json` / `package-lock.json` (e.g., `@11ty/eleventy`, `luxon`, `markdown-it`, `@11ty/eleventy-img`)
*   **Admin Interface & API:** Python 3, Flask
*   **Auxiliary Scripting:** Python 3
*   **Python Dependencies (for scripts/app):** Flask, python-frontmatter, Pillow (image processing & watermarking), Requests (API communication), python-dotenv (config loading), BeautifulSoup4 (`bs4` - for HTML processing in deploy script), lxml (optional but recommended HTML parser). **(Note: `Paramiko` is likely NOT used as deployment is via HTTP API)**.

## 3. Project Structure Highlights

*   `.eleventy.js`: Central Eleventy configuration file.
*   **`.env`:** Stores configuration variables (API keys, URLs, paths) - **Must not be committed to Git.**
*   `_data/`: Contains global and workflow JSON data files:
    *   `image_library.json`: Stores metadata and **paths** for different versions (raw, published, watermarked) of processed images. **Managed by `scripts/process_imported_image.py`**.
    *   `workflow_status.json`: Tracks the status of various stages per post slug, including per-image watermarking status and deployment status/errors.
*   `_includes/`: Reusable Nunjucks template partials.
*   **`_SOURCE_MEDIA/_IMPORT_IMAGES/`:** **Temporary holding directory** for raw images before processing. Ignored by Git.
*   `_site/`: Output directory for the generated static site (ignored by Git).
*   `css/`: Source CSS files.
*   `docs/`: Project planning documentation.
*   `images/`: Contains processed image assets:
    *   `images/posts/{slug}/`: Stores **raw backups (`_raw.*`)** and **published versions (`.webp`/`.jpg`)** of post images. Copied by Eleventy passthrough.
    *   `images/watermarked/`: Stores **watermarked versions** (likely `.webp`/`.jpg`) of images, potentially for syndication use.
    *   `images/site/`: Site-wide images (e.g., `clan-watermark.png`).
*   `posts/`: Blog post content (Markdown `.md` files).
*   `scripts/`: Contains auxiliary Python scripts:
    *   **`process_imported_image.py`:** New script to process images from import dir: copies raw, optimizes/converts (to WebP), applies image watermark, saves versions to `images/posts` and `images/watermarked`, updates `image_library.json`, and deletes original import.
    *   `post_to_clan.py`: **Builds site**, processes post HTML (removes back link, applies image path rewrites), **uploads referenced published images**, prepares metadata, and **submits post content via HTTP API** (create or edit) to clan.com. Uses `.env` for config.
    *   `watermark_images.py`: **(Likely superseded/obsolete)** Original script for applying watermarks directly; its logic is now integrated into `process_imported_image.py`.
*   `templates/`: Nunjucks templates, including admin interface files (`admin_index.html`, `admin_post_detail.html`).
*   `app.py`: Flask application providing the local admin web interface and API endpoints. Includes logic for triggering deployment, updating workflow status based on deployment results, and serving image previews.
*   `package.json`: Node.js project definition and scripts.
*   `.gitignore`: Specifies ignored files/directories (`node_modules/`, `_site/`, `_SOURCE_MEDIA/`, `.env`).

## 4. Core Build Process (Eleventy via `.eleventy.js`)

*   *(Largely unchanged)*
*   Reads content, uses Nunjucks/Markdown templates.
*   Uses `image` shortcode (likely sourcing image paths from data passed via Eleventy, originating from `image_library.json`) to generate responsive HTML using `eleventy-img` based on the **published image files** (e.g., `images/posts/{slug}/{image_id}.webp`).
*   Outputs static site to `_site/` including passthrough copies of `images/`, `css/` etc.
*   **Permalink Configuration:** Posts are configured (via `posts/posts.11tydata.js`) to output to `_site/{slug}/index.html`.

## 5. Auxiliary Components & Workflows (Updated Significantly)

*   **Image Processing Workflow (`scripts/process_imported_image.py`):**
    *   **Trigger:** Manual execution via command line. Requires input image path, slug, base name, and metadata.
    *   **Input:** Raw image file placed in `_SOURCE_MEDIA/_IMPORT_IMAGES/`.
    *   **Actions:**
        1.  Copies original to `images/posts/{slug}/{image_id}_raw.*`.
        2.  Loads image, optimizes (resizes), converts to target format (e.g., WebP).
        3.  Saves optimized, **unwatermarked** version to `images/posts/{slug}/{image_id}.webp`.
        4.  Applies an **image watermark** (from `images/site/clan-watermark.png`, resized, with optional background) to the optimized version.
        5.  Saves watermarked version to `images/watermarked/{image_id}.webp`.
        6.  Updates `_data/image_library.json` with metadata and relative paths to raw, published, and watermarked files.
        7.  Deletes the original from the import directory upon success.
*   **Admin Interface (`app.py`):**
    *   Provides dashboard (`/`) and detailed post view (`/admin/post/<slug>`).
    *   `/admin/post/<slug>` displays image previews using a static route (`/images/`) pointing to the `images/` directory, constructing URLs based on the `published_file_path` from `image_library.json`. Displays individual image statuses calculated from library/workflow data.
    *   `/api/publish_clan/<slug>` (POST):
        1.  Triggers `scripts/post_to_clan.py`.
        2.  Captures script success/failure status and output.
        3.  **Updates `_data/workflow_status.json`** (`publishing_clancom` stage status, error message, extracted post ID on success).
        4.  Returns script output to the UI.
    *   `/api/update_status/<slug>/<stage_key>` (POST): Updates status in `workflow_status.json` (handles nested keys like `images.watermarks.<id>`).
    *   `/api/watermark_all/<slug>` (POST): Triggers original (now likely obsolete) `watermark_images.py`. **(Needs review/removal if `process_imported_image.py` is the primary method)**.
*   **Deployment (`scripts/post_to_clan.py`):**
    *   **Trigger:** Via `/api/publish_clan/<slug>` endpoint or manual execution.
    *   **Actions:**
        1.  Runs `npm run build` to ensure `_site` is up-to-date.
        2.  Loads post Markdown (`posts/{slug}.md`) for metadata.
        3.  Loads built HTML (`_site/{slug}/index.html`).
        4.  **Processes HTML:** Removes "Back" link (using configured selector), removes comments, **rewrites relative image `src`** attributes within content to point to `IMAGE_PUBLIC_BASE_URL`. **(Note: Does NOT remove H1 title based on last correction)**. Saves processed HTML to a temp file.
        5.  Loads `_data/image_library.json`.
        6.  Identifies all referenced images (`headerImageId`, section/conclusion `imageId`s).
        7.  **Uploads referenced images:** Calls `upload_image_to_clan` for each ID. This function uploads the **published version** (e.g., `images/posts/{slug}/{image_id}.webp`) using an HTTP API (`uploadImage` endpoint) and updates `image_library.json` *in memory* with the returned server path.
        8.  **Saves updated `image_library.json`** if uploads occurred.
        9.  Determines if creating or editing based on `post_id` in `_data/workflow_status.json`.
        10. **Prepares API arguments (`json_args`)**: Maps metadata and **uploaded image thumbnail paths** (from updated image library data) to fields required by clan.com API (`title`, `url_key`, `short_content`, `list_thumbnail`, etc.).
        11. **Submits Post:** Calls the clan.com API (`createPost` or `editPost` endpoint) using `multipart/form-data`, sending `json_args` and the processed HTML as a file upload (`html_file`).
        12. Outputs SUCCESS/ERROR messages to stdout/stderr for capture by `app.py`.
        13. Updates `_data/workflow_status.json` with attempt results.
        14. Cleans up temporary HTML file.

*   **Development Workflow:**
    1.  Place raw images in `_SOURCE_MEDIA/_IMPORT_IMAGES/`.
    2.  Run `python scripts/process_imported_image.py ...` for each image to process it and update library.
    3.  Edit content (`posts/*.md`), reference processed `image_id`s.
    4.  Run `npm start` for Eleventy preview.
    5.  Run `python app.py` for Admin UI.
    6.  Use Admin UI to trigger deployment (`/api/publish_clan`).

*   **Deployment Workflow:** (Largely handled by `scripts/post_to_clan.py` trigger now)
    1.  Ensure images are processed via `process_imported_image.py`.
    2.  Ensure content (`posts/*.md`) is ready.
    3.  Trigger deployment via Admin UI (`/api/publish_clan/<slug>`) which runs build, image upload, and API submission.
    4.  Monitor status in Admin UI / workflow JSON.

## 6. Documentation & Planning

*   The `docs/` directory contains planning documents.

## 7. Key Files Quick Reference (Updated)

*   `.eleventy.js`: Eleventy build config.
*   `.env`: API Keys, URLs, Config (**local only**).
*   `package.json`: Node.js dependencies/scripts.
*   `app.py`: Flask admin UI & API backend.
*   `templates/admin_index.html`, `templates/admin_post_detail.html`: Admin UI templates.
*   **`scripts/process_imported_image.py`:** Image intake, processing, watermarking script.
*   **`scripts/post_to_clan.py`:** Deployment script (build, image upload, API submit).
*   `_data/workflow_status.json`: Stores workflow state per post.
*   `_data/image_library.json`: Stores image metadata and paths.
*   `posts/`: Blog content (Markdown).
*   `_SOURCE_MEDIA/_IMPORT_IMAGES/`: Input directory for raw images.
*   `images/posts/`: Output for raw backups and published images.
*   `images/watermarked/`: Output for watermarked images.