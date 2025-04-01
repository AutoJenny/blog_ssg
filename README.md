# Blog Post Creation & Management Workflow

This document outlines the current steps required to create, manage, and publish new blog posts using the Eleventy framework and associated scripts established in this project. This serves as a reference and a basis for future automation efforts.

## Authoring Article Content

This initial phase focuses on generating the raw text content for the blog post.

1.  **First Draft (AI Assisted):**
    *   Use an appropriate authoring AI (e.g., ChatGPT 4 or newer).
    *   Provide a detailed prompt, including:
        *   Desired Title (e.g., "The Tradition of the Scottish Quaich")
        *   Request for a Subtitle and a Summary/Introduction paragraph.
        *   Request for 6-10 distinct sections covering the topic chronologically or thematically (origins, evolution, usage, modern relevance, etc.).
        *   Specify desired length (e.g., ~2000 words).
        *   **Crucially, request output using only UK English spellings and idioms.**
2.  **Review and Edit Text:**
    *   Carefully review the AI-generated text for accuracy, flow, tone, and completeness.
    *   Edit and refine the text as necessary. Ensure factual correctness.
3.  **Prepare HTML Content:**
    *   Format the final text for each section (including the summary and conclusion) using basic HTML tags (primarily `<p>`, `<b>`, `<i>`, `<ul>`, `<li>`). This formatted HTML will be pasted into the YAML front matter later.

## Manual Workflow Steps

These are the steps to integrate the content into the project, add metadata, manage assets, and publish.

### Preparing Content and Metadata File (`.md`)

1.  **Determine Post Slug:**
    *   Choose a short, URL-friendly identifier for the post (e.g., `quaich-traditions`). This will be used for the filename and the image subdirectory. Keep it lowercase, using hyphens for spaces.
2.  **Create Markdown File:**
    *   In the `posts/` directory, create a new Markdown file named using the slug: `posts/<your-post-slug>.md` (e.g., `posts/quaich-traditions.md`).
3.  **Add YAML Front Matter & Content:**
    *   At the very top of the new `.md` file, add the YAML block (`--- ... ---`).
    *   Fill in the metadata fields:
        *   `title`: "Your Full Post Title"
        *   `subtitle`: "Your Post Subtitle"
        *   `description`: "A concise sentence or two summarizing the post for SEO/sharing."
        *   `layout`: "post.njk" (Usually this)
        *   `date`: YYYY-MM-DD (The publication date)
        *   `author`: "author-key" (The unique key matching an entry in `_data/authors.json`. Add new authors to that file first if needed.)
        *   `tags`:
            *   `- post` (Essential for the post collection)
            *   `- relevant-tag-1`
            *   `- relevant-tag-2`
            *   (Add other relevant keywords/topics)
        *   `headerImage`: (Object: `src`, `alt`, `caption`, `imagePrompt`, `notes`. `src` path defined in "Managing Images".)
        *   `summary`: "<p>Paste the formatted HTML summary here.</p>"
        *   `sections`: (Array of objects. Each needs `heading`, `text` [formatted HTML], `image` [object: `src`, `alt`, `caption`], `imagePrompt`, `notes`. `src` path defined in "Managing Images".)
        *   `conclusion`: (Optional object with `heading`, `text` [formatted HTML], optionally `imagePrompt`, `notes`).

### Managing Images

4.  **Prepare Image Subdirectory:**
    *   In the `images/` directory, create a new subdirectory named after the post slug: `images/<your-post-slug>/`
    *   Command (from project root): `mkdir -p images/<your-post-slug>`
5.  **Generate/Select, Rename, and Place Images:**
    *   Use the `imagePrompt` values from the front matter to generate images using an AI tool, or select appropriate existing images.
    *   Rename the final image files using descriptive, URL-friendly names (e.g., `quaich-header-collage.jpg`, `early-origins-wooden.jpg`). Use lowercase and hyphens. Ensure standard extensions (`.jpg`, `.png`, `.webp`). **Crucially, filenames must be unique across all posts** as they currently land in the same target directory on the server (`/media/blog/`).
    *   Move the renamed images into the subdirectory: `images/<your-post-slug>/`.
6.  **Update Image Paths & Details in Front Matter:**
    *   Go back to the `.md` file's front matter.
    *   Update the `src` path for `headerImage` and each `image` within `sections` to point to the correct file. Paths must be relative to the site root (e.g., `src: "/images/<your-post-slug>/your-image-name.jpg"`).
    *   Fill in accurate `alt` text (for accessibility) and `caption` text for each image.

### Watermarking Images

7.  **Watermark (Optional Manual Step):**
    *   If watermarking is desired *before* publishing:
        *   Run the watermarking script, targeting the *new* image subdirectory:
          ```bash
          python3 watermark_images.py images/<your-post-slug>
          ```
        *   This creates `images/<your-post-slug>-watermarked/`.
        *   **Note:** The main publishing script (`post_to_clan.py`) currently uploads images from the *original* directory (`images/<your-post-slug>/`). To publish the watermarked versions, you would need to either manually copy them over the originals or modify the `post_to_clan.py` script to read from the `-watermarked` directory instead.

### Previewing Locally

8.  **Preview Site:**
    *   Run the Eleventy development server (ensure Flask app on port 5001 is stopped or use a different port if needed):
        ```bash
        npm start
        ```
    *   Open browser to `http://localhost:8080/` (for index) and `http://localhost:8080/<your-post-slug>/` (for the new post).
    *   Check thoroughly: title, subtitle, meta, sections, images loading, tags, navigation links. Check browser console for errors.

### Committing to Git

9.  **Commit Changes:**
    *   Once satisfied with the local preview:
        *   Stop the Eleventy server (`Ctrl+C`).
        *   Stage changes (the `.md` file, `_data/authors.json` if updated, new `images/<slug>/` directory and contents, `_data/syndication.json` if post ID was added).
          ```bash
          git status
          git add .
          ```
        *   Commit:
          ```bash
          git commit -m "feat: Add blog post '<Your Post Title>'" # Or "chore: Update post..."
          ```
        *   Push:
          ```bash
          git push origin main
          ```

### Publishing to Clan.com (via Admin Interface)

10. **Publish/Update Live Post:**
    *   This step uses the Flask web interface.
    *   Ensure the Flask app is running: `python3 app.py`
    *   Open the interface in your browser (e.g., `http://127.0.0.1:5001`).
    *   Find the desired post in the "Manage Posts" list.
    *   Click the "Publish/Update Clan.com" button next to it.
    *   Monitor the "Action Log / Output" section in the interface for progress and success/error messages from the `post_to_clan.py` script. This script handles:
        *   Running `npm run build`.
        *   Extracting/cleaning HTML content.
        *   Uploading required images (header and section images) via the `uploadImage` API.
        *   Calling the `createPost` or `editPost` API with the post metadata, HTML content, and uploaded image paths (thumbnails).
        *   Updating the local `_data/syndication.json` with the `clan_com_post_id` on successful creation.
    *   Verify the post on the live site (`clan.com/blog`) after the script reports success.

---

### Potential Future Automation Points

*   Script/Interface button to generate a boilerplate `.md` file.
*   Interface button to automatically create the image subdirectory.
*   Tool/Interface integration for easier image renaming/placement.
*   Integration of watermarking into the publishing script (e.g., triggered by a flag, potentially only for production uploads).
*   Direct content editing (summary, section text) within the interface.
*   Interface for managing `_data/authors.json`.
*   Interface/Script for triggering/managing social media syndication (Instagram, Facebook).

---