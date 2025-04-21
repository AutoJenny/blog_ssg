# CLAN.com Blog Authoring & Management System

This project provides a local development environment and management interface for creating, previewing, and publishing blog posts for the CLAN.com blog.

**Core Technologies:**

*   **Content:** Markdown files with YAML front matter (`posts/`).
*   **Static Site Generation:** Eleventy (`@11ty/eleventy`) builds the static HTML/CSS site for local preview.
*   **Management Interface:** A local Flask web application (`app.py`) provides a UI for managing the workflow.
*   **Publishing:** A Python script (`post_to_clan.py`) handles interacting with the Clan.com Blog API.
*   **Data:** Global data (authors, syndication status) is stored in JSON files within the `_data/` directory.

---

## Running the Local Environment

To work on blog posts, you typically need **two** local servers running simultaneously in separate terminal windows, opened within the project directory (`blog_ssg/`):

**1. Terminal 1: Eleventy Dev Server (Live Preview)**

*   **Purpose:** Builds the static blog site and provides a live preview that automatically updates when content or template files are saved.
*   **Command:**
    ```bash
    npm start
    ```
*   **Access:** Usually runs at `http://localhost:8080`. Use this URL to preview individual posts via the "Preview Locally" links in the Management Interface.

**2. Terminal 2: Flask Management Interface**

*   **Purpose:** Runs the web-based interface used to view post status and trigger actions like publishing to the live Clan.com site.
*   **Command:**
    ```bash
    # Activate virtual environment first if using one (e.g., source .venv/bin/activate)
    python3 app.py
    ```
*   **Access:** Usually runs at `http://127.0.0.1:5001`. Open this URL in your browser to manage the workflow.

---

## Using the Workflow Manager (`http://127.0.0.1:5001`)

The Management Interface provides the main hub for day-to-day tasks:

*   **View Posts:** Lists all posts found locally in the `posts/` directory.
*   **Check Status:** Shows the current publishing status on Clan.com based on locally stored data (`_data/syndication.json`).
*   **Trigger Actions:** Use the buttons next to each post (e.g., "Publish/Update Clan.com") to execute the underlying Python scripts (`post_to_clan.py`).
*   **Monitor Output:** The "Action Log / Output" section displays real-time feedback and results from the triggered scripts.
*   **Contextual Help:** **Click the `(?)` icons** next to headings and buttons within the interface for detailed instructions and explanations for each specific workflow step (authoring, image management, publishing, etc.). The detailed step-by-step guides previously in this README are now integrated there.

---

## Content & Data Location

*   **Blog Post Content:** Stored as Markdown files (`.md`) with YAML front matter in the `posts/` directory.
*   **Post Images:** Stored in the `images/` directory, typically organized into subdirectories named after the post slug (e.g., `images/kilt-evolution/`).
*   **Author Information:** Managed centrally in `_data/authors.json`.
*   **Publishing/Syndication Status:** Tracked in `_data/syndication.json`.
*   **Site Layouts:** Eleventy templates are in `_includes/`.
*   **Site CSS:** Found in `css/`.

---

## Project Structure Overview

*   `app.py`: Flask application for the management interface.
*   `templates/`: HTML templates for the Flask interface.
    *   `help/`: Contains help text snippets used in the interface.
*   `post_to_clan.py`: Python script to interact with the Clan.com Blog API.
*   `watermark_images.py`: Python script to watermark images.
*   `syndicate.py` (Future): Script for social media syndication.
*   `posts/`: Contains blog post content as Markdown files with YAML front matter.
*   `images/`: Contains source images, organized into subdirectories per post slug.
    *   `site/`: Contains site-wide images (header, footer, watermark).
*   `_data/`: Contains global data files used by Eleventy and scripts (e.g., `authors.json`, `syndication.json`).
*   `_includes/`: Contains Eleventy layout templates (`base.njk`, `post.njk`).
*   `css/`: Contains CSS for the generated Eleventy site.
*   `_site/`: Output directory where Eleventy builds the static site (ignored by Git).
*   `.eleventy.js`: Eleventy configuration file.
*   `package.json`: Node.js project configuration and dependencies.
*   `requirements.txt` (Recommended): Lists Python dependencies.
*   `README.md`: This file - project overview and setup.

---