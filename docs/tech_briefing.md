# Technical Briefing: AutoJenny/blog_ssg Project (Updated)

## 1. Overview

This document provides a technical overview of the `AutoJenny/blog_ssg` GitHub repository. The project is a static site generator (SSG) setup for building and deploying a blog, intended for the website `clan.com`. It utilizes Eleventy (11ty) as its core engine. It is supplemented by Python scripts for auxiliary tasks (deployment, image processing) and includes a local **Flask-based admin interface (`app.py`)** for monitoring content status, viewing post details, and managing workflow stages (via API).

## 2. Technology Stack

*   **Core SSG:** Node.js, Eleventy (11ty)
*   **Configuration:** JavaScript (`.eleventy.js`)
*   **Templating:** Nunjucks (`.njk`), Markdown (`.md`)
*   **Content:** Markdown files with YAML Front Matter
*   **Data Management:** JSON (`_data/`, specifically `image_library.json`, `workflow_status.json`), JavaScript (`*.11tydata.js`)
*   **Styling:** CSS (`css/`)
*   **Node.js Dependencies:** Managed via `package.json` / `package-lock.json` (e.g., `@11ty/eleventy`, `luxon`, `markdown-it`, `@11ty/eleventy-img`)
*   **Admin Interface & API:** Python 3, Flask
*   **Auxiliary Scripting:** Python 3
*   **Python Dependencies (for scripts/app):** Flask, python-frontmatter, Pillow (for watermarking), Paramiko (for SFTP), Requests.

## 3. Project Structure Highlights

*   `.eleventy.js`: **Central Eleventy configuration file.** Defines build behaviour, plugins, collections, filters, shortcodes, and asset handling.
*   `_data/`: Contains global and workflow JSON data files:
    *   `image_library.json`: Stores metadata and source details for reusable images.
    *   `workflow_status.json`: **Tracks the status of various stages (images, writing, publishing) for each post slug.** Includes detailed **per-image watermarking status**.
    *   Other potential JSON files (e.g., `authors.json`).
*   `_includes/`: Reusable Nunjucks template partials (e.g., `base.njk`, `post.njk`).
*   `_site/`: **Output directory** for the generated static site (specified in `.gitignore`).
*   `css/`: Source CSS files. Copied directly to `_site/css/` via passthrough rules.
*   `docs/`: Markdown files containing project planning and documentation. Copied to `_site/docs/`.
*   `images/`: Source image assets. Copied directly to `_site/images/` via passthrough rules. Referenced by `image_library.json` and processed by the `image` shortcode during Eleventy build.
*   `posts/`: Blog post content (Markdown `.md` files) and associated Eleventy data files (`*.11tydata.js/.json`).
*   `scripts/`: Contains auxiliary Python scripts:
    *   `watermark_images.py`: Adds watermarks to source images (manual process).
    *   `post_to_clan.py`: Deploys the built site (`_site/`) via SFTP.
*   `templates/`: Contains Nunjucks templates, including those used by the Flask admin app (`admin_index.html`, `admin_post_detail.html`). Copied to `_site/`.
*   `app.py`: **Flask application** providing the local admin web interface and supporting API endpoints. Contains significant logic for loading data, calculating statuses, and interacting with workflow data.
*   `index.njk`: Nunjucks template for the site's homepage (Eleventy build).
*   `package.json`: Node.js project definition, dependencies, and run scripts (`start`, `build`).
*   `.gitignore`: Specifies files/directories ignored by Git (e.g., `node_modules/`, `_site/`).

## 4. Core Build Process (Eleventy via `.eleventy.js`)

*   *(This section remains largely unchanged from the previous briefing, describing the Eleventy build)*
*   **Configuration:** Centralized in `.eleventy.js`.
*   **Input/Output:** Reads from root (`./`), outputs to `_site/`.
*   **Passthrough Copy:** Copies `images/`, `css/`, `docs/`, `templates/admin*`, `syndication_plan/index.html` directly to the `_site` directory.
*   **Template Engines:** Processes `.njk` (Nunjucks) and `.md` (Markdown) files.
*   **Markdown:** Uses `markdown-it` with HTML enabled and `markdown-it-anchor` for heading links.
*   **Collections:** `posts` (sorted by date), `tagList`.
*   **Filters:** `readableDate`, `htmlDateString`, `head`, `syndicationLinks` (placeholder).
*   **Shortcodes:** `image` (using `@11ty/eleventy-img` for responsive images).
*   **Environment:** Uses `process.env.ELEVENTY_ENV`.

## 5. Auxiliary Components & Workflows (Updated)

*   **Admin Interface (`app.py` & `templates/admin*.html`):**
    *   A **Flask application** providing a local web interface (`http://127.0.0.1:5001` typically). Run via `python app.py`.
    *   **Dashboard (`/`):** Displays a list of posts and their publishing status (read from `workflow_status.json`).
    *   **Post Detail View (`/admin/post/<slug>`):**
        *   Displays detailed metadata loaded from the post's Markdown front matter.
        *   Shows the status of various workflow stages (images, writing, etc.) loaded from `workflow_status.json`.
        *   **Image Workflow Section:** Displays images referenced in the post's front matter.
            *   Fetches image details from `image_library.json`.
            *   Displays the source image preview.
            *   Calculates and displays the status of image sub-tasks (prompt defined, assets prepared, metadata integrated) based on `image_library.json` content and file existence checks.
            *   Displays the **individual watermarking status** for each image, loaded from the post's entry in `workflow_status.json`.
    *   **Helper Functions:** Includes robust `load_json_data` and `save_json_data` helpers for consistent file handling.
    *   **API Endpoints:**
        *   `/api/update_status/<slug>/<stage_key>` (POST): Allows updating the status of a specific stage (or sub-stage like watermarking) for a post within `workflow_status.json`. Expects JSON body like `{"status": "complete"}`.
        *   `/api/publish_clan/<slug>` (POST): Triggers the `scripts/post_to_clan.py` deployment script for the specified post's Markdown file (passing relative path). Returns script output.
        *   Other minor API endpoints (`/api/workflow`, `/api/reload-data`).

*   **Image Watermarking (`scripts/watermark_images.py`):**
    *   A Python script using `Pillow` to add a text watermark.
    *   **Decoupled Process:** Intended as a **manual command-line step**. It is **not** triggered directly via the Flask admin interface.
    *   **Status Update:** The script itself likely does **not** update `workflow_status.json`. Status updates for watermarking probably occur manually via the `/api/update_status` endpoint after running the script, or require modifications to the script itself.
    *   Requires clarification on where watermarked images are saved (e.g., subdirectory, naming convention).

*   **Deployment (`scripts/post_to_clan.py`):**
    *   A Python script using `Paramiko` for **SFTP deployment**. Triggered via the `/api/publish_clan` endpoint in the admin interface or run manually.
    *   Connects to the remote server.
    *   Synchronizes the contents of the local `_site/` directory to the remote server. *(Security note on credential handling remains critical)*.

*   **Development Workflow:**
    1.  Edit content/templates/code.
    2.  Run `npm start` for Eleventy build/serve (`http://localhost:8080` default).
    3.  Run `python app.py` for the admin interface (`http://127.0.0.1:5001` default).

*   **Deployment Workflow:**
    1.  Run `python scripts/watermark_images.py` (if needed, manually).
    2.  Update watermarking status in `workflow_status.json` (likely manual step via API/direct edit, unless script is modified).
    3.  Run `npm run build` to generate the production site in `_site/`.
    4.  Trigger deployment using the admin interface button (`/api/publish_clan/<slug>`) or run `python scripts/post_to_clan.py` manually.

## 6. Documentation & Planning

*   The `docs/` directory contains Markdown files outlining plans and design decisions. Valuable for understanding project history and intent.

## 7. Key Files Quick Reference (Updated)

*   `.eleventy.js`: Core Eleventy build configuration.
*   `package.json`: Node.js dependencies and scripts (`start`, `build`).
*   `app.py`: **Flask admin interface application & API backend.**
*   `templates/admin_post_detail.html`: Template for the detailed post admin view (displays image workflow).
*   `scripts/post_to_clan.py`: Deployment script.
*   `scripts/watermark_images.py`: Manual watermarking script.
*   `_data/workflow_status.json`: Stores workflow state per post slug, including per-image watermarking.
*   `_data/image_library.json`: Stores source image metadata.
*   `posts/`: Blog content (Markdown).