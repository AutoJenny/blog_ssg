# Technical Briefing: AutoJenny/blog_ssg Project

## 1. Overview

This document provides a technical overview of the `AutoJenny/blog_ssg` GitHub repository. The project is a static site generator (SSG) setup for building and deploying a blog, intended for the website `clan.com`. It utilizes Eleventy (11ty) as its core engine, supplemented by Python scripts for auxiliary tasks like deployment and image processing, and includes a local Flask-based admin interface for viewing site data.

## 2. Technology Stack

*   **Core SSG:** Node.js, Eleventy (11ty)
*   **Configuration:** JavaScript (`.eleventy.js`)
*   **Templating:** Nunjucks (`.njk`), Markdown (`.md`)
*   **Content:** Markdown files with YAML Front Matter
*   **Data Management:** JSON (`_data/`), JavaScript (`*.11tydata.js`)
*   **Styling:** CSS (`css/`)
*   **Node.js Dependencies:** Managed via `package.json` / `package-lock.json` (e.g., `@11ty/eleventy`, `luxon`, `markdown-it`, `@11ty/eleventy-img`)
*   **Auxiliary Scripting:** Python 3
*   **Admin Interface:** Python 3, Flask
*   **Python Dependencies (for scripts/app):** Pillow (watermarking), Paramiko (SFTP), Requests, Flask, python-frontmatter (likely required based on usage).

## 3. Project Structure Highlights

*   `.eleventy.js`: **Central Eleventy configuration file.** Defines build behaviour, plugins, collections, filters, shortcodes, and asset handling.
*   `_data/`: Global JSON data files (e.g., `authors.json`, `image_library.json`, `syndication.json`).
*   `_includes/`: Reusable Nunjucks template partials (e.g., `base.njk`, `post.njk`).
*   `_site/`: **Output directory** for the generated static site (specified in `.gitignore`).
*   `css/`: Source CSS files. Copied directly to `_site/css/` via passthrough rules.
*   `docs/`: Markdown files containing project planning and documentation. Copied to `_site/docs/`.
*   `images/`: Source image assets. Copied directly to `_site/images/` via passthrough rules. Also processed by the `image` shortcode.
*   `posts/`: Blog post content (Markdown `.md` files) and associated Eleventy data files (`*.11tydata.js/.json`).
*   `scripts/`: Contains auxiliary Python scripts (`watermark_images.py`, `post_to_clan.py`).
*   `templates/`: Contains Nunjucks templates, including those used by the Flask admin app (`admin_index.html`, `admin_post_detail.html`). Copied to `_site/`.
*   `app.py`: A Flask application providing a local admin interface.
*   `index.njk`: Nunjucks template for the site's homepage.
*   `package.json`: Node.js project definition, dependencies, and run scripts (`start`, `build`).
*   `.gitignore`: Specifies files/directories ignored by Git (e.g., `node_modules/`, `_site/`).

## 4. Core Build Process (Eleventy via `.eleventy.js`)

*   **Configuration:** Centralized in `.eleventy.js`.
*   **Input/Output:** Reads from root (`./`), outputs to `_site/`.
*   **Passthrough Copy:** Copies `images/`, `css/`, `docs/`, `templates/admin*`, `syndication_plan/index.html` directly to the `_site` directory.
*   **Template Engines:** Processes `.njk` (Nunjucks) and `.md` (Markdown) files.
*   **Markdown:** Uses `markdown-it` with HTML enabled and `markdown-it-anchor` for heading links.
*   **Collections:**
    *   `posts`: Creates a date-sorted (desc) array of all items tagged `posts`.
    *   `tagList`: Creates a unique, sorted list of all tags used.
*   **Filters:**
    *   `readableDate`: User-friendly date format (e.g., "Jul 22, 2024").
    *   `htmlDateString`: ISO date format for `<time>` elements (e.g., "2024-07-22").
    *   `head`: Returns the first N items of an array.
    *   `syndicationLinks`: Placeholder for future syndication link processing.
*   **Shortcodes:**
    *   `image`: Uses `@11ty/eleventy-img` to generate responsive `<picture>` elements with multiple sizes (e.g., 300, 600, 900px) and formats (AVIF, WebP, JPEG) from source images in `images/`. Includes lazy loading and async decoding attributes.
*   **Environment:** Uses `process.env.ELEVENTY_ENV` (set in `npm run build`) for environment-specific actions.

## 5. Auxiliary Components & Workflows

*   **Admin Interface (`app.py`):**
    *   A **Flask application** providing a **local, read-only** web interface.
    *   Run via `python app.py`.
    *   Routes include `/` (dashboard showing data from `_data/*.json`), `/posts/<slug>` (detailed post view), and simple API endpoints (`/api/workflow`, `/api/reload-data`).
    *   Uses templates from `templates/admin*.html`.
    *   Useful for viewing site status, data, and post content without starting the full Eleventy build.
*   **Image Watermarking (`scripts/watermark_images.py`):**
    *   A Python script using `Pillow`.
    *   Adds a text watermark to images found in `images/posts/`.
    *   Intended as a **manual pre-processing step** before running the Eleventy build.
*   **Deployment (`scripts/post_to_clan.py`):**
    *   A Python script using `Paramiko` for **SFTP deployment**.
    *   Connects to a remote server (presumably hosting `clan.com`).
    *   Synchronizes the contents of the local `_site/` directory (generated by `npm run build`) to the specified remote directory.
    *   **Security Consideration:** How SSH/SFTP credentials (host, user, password/key) are managed is critical. Avoid hardcoding credentials; prefer SSH keys or environment variables.
*   **Development Workflow:**
    1. Edit content/templates.
    2. Run `npm start` for local development server with live reload (`http://localhost:8080` typically).
    3. View admin interface via `python app.py` (runs independently on a different port, e.g., 5000).
*   **Deployment Workflow:**
    1. Optionally run `python scripts/watermark_images.py` if needed.
    2. Run `npm run build` to generate the production site in `_site/`.
    3. Run `python scripts/post_to_clan.py` to upload `_site/` contents to the server.

## 6. Documentation & Planning

*   The `docs/` directory contains Markdown files outlining plans and design decisions for various aspects of the project (image system, admin interface, post creation, syndication). These are valuable for understanding project history and intent.

## 7. Key Files Quick Reference

*   `.eleventy.js`: Core build configuration.
*   `package.json`: Node.js dependencies and scripts (`start`, `build`).
*   `app.py`: Flask admin interface application.
*   `scripts/post_to_clan.py`: Deployment script.
*   `_data/`: Global site data.
*   `_includes/`: Reusable template code.
*   `posts/`: Blog content.