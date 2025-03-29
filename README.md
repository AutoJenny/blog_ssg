---
title: "Blog Post Creation Workflow"
---

## Blog Post Creation Workflow (Manual)

This document outlines the current manual steps required to create and publish a new blog post using the Eleventy framework established in this project. This serves as a reference and a basis for future automation efforts.

**Goal:** To add a new, formatted blog post with associated images, metadata, and tags, viewable locally and committed to Git.

**Prerequisites:**

1.  **Content:** The main text content for the post, including section breaks, is written (e.g., in a separate document).
2.  **Images:** Raw image files intended for the post are gathered and available.
3.  **Project Setup:** The Eleventy project is set up, and `npm install` has been run.
4.  **Author Data:** If using a new author, ensure their details are added to `_data/authors.json` with a unique key.

**Authoring article:**
1. **First draft** Use ChatGPT4.5 (or new better authoring AI) with prompt eg
"Please write a 2000 word blog article titled "xxx". Give the article a subtitle, a summary-introduction, and about 6-10 sections covering all aspects of its earliest origins to the modern day, exploring its evolution and usage and meaning. Use only UK English spellings and idioms."
2. **Make HTML** .

**Step-by-Step Process:**

1.  **Determine Post Slug:**ort, URL-friendly identifier for the post (e.g., `new-post-topic`). This will be used for the filename and the image subdirectory. Keep it lowercase, using hyphens for spaces.

2.  **Create Markdown File:**
    *   In the `posts/` directory, create a new Markdown file named using the slug: `posts/<your-post-slug>.md` (e.g., `posts/new-post-topic.md`).

3.  **Add YAML Front Matter:**
    *   At the very top of the new `.md` file, add the YAML block (`--- ... ---`).
    *   Fill in the required and optional metadata fields, referencing existing posts for structure:
        *   `title`: "Your Full Post Title"
        *   `subtitle`: "Optional Subtitle" (if applicable)
        *   `description`: "A concise sentence or two summarizing the post for SEO/sharing."
        *   `layout`: "post.njk" (Should usually be this)
        *   `date`: YYYY-MM-DD (The publication date)
        *   `author`: "author-key" (The unique key matching an entry in `_data/authors.json`)
        *   `tags`:
            *   `- post` (Essential for the post collection)
            *   `- relevant-tag-1`
            *   `- relevant-tag-2`
            *   (Add other relevant keywords/topics)
        *   `headerImage`: (Object with `src`, `alt`, `caption`. Path TBD in step 6).
        *   `summary`: "<p>HTML summary paragraph(s).</p>"
        *   `sections`: (Array of objects, each with `heading`, `text` [using HTML paragraphs], `image` [object with `src`, `alt`, `caption`. Path TBD in step 6]).
        *   `conclusion`: (Optional object with `heading`, `text`).

4.  **Prepare Image Subdirectory:**
    *   In the `images/` directory, create a new subdirectory named after the post slug: `images/<your-post-slug>/`
    *   Use the command line (from project root): `mkdir -p images/<your-post-slug>`

5.  **Process and Place Images:**
    *   Rename your gathered raw image files using descriptive, URL-friendly names based on their content or section (e.g., `header.jpg`, `section-1-topic.jpg`, `conclusion-image.png`). Use lowercase and hyphens. Ensure they have appropriate file extensions (`.jpg`, `.png`, `.webp`, etc.).
    *   Move the renamed images into the newly created subdirectory: `images/<your-post-slug>/`.

6.  **Update Image Paths in Front Matter:**
    *   Go back to the `.md` file's front matter.
    *   Update the `src` path for the `headerImage` and each `image` within the `sections` array to point to the correct file within the new subdirectory. Paths should be relative to the site root:
        *   Example: `src: "/images/<your-post-slug>/header.jpg"`
        *   Example: `src: "/images/<your-post-slug>/section-1-topic.jpg"`

7.  **Watermark Images (Optional Manual Step):**
    *   If watermarking is desired *before* local preview uses them (this depends on your desired workflow):
        *   Run the watermarking script, targeting the *new* image subdirectory and outputting to a *new* watermarked directory:
          ```bash
          python3 watermark_images.py images/<your-post-slug> images/site/clan-watermark.png
          ```
        *   This will create `images/<your-post-slug>-watermarked/`.
        *   **Note:** Currently, the templates (`post.njk`) read image paths from the front matter, which point to the *original* (non-watermarked) directory (`/images/<your-post-slug>/`). The watermarked images are generated but not used by default in the local preview or build. Further workflow changes would be needed to use the watermarked images directly.

8.  **Preview Locally:**
    *   Run the Eleventy development server from the project root:
        ```bash
        npm start
        ```
    *   Open your browser and navigate to the post's URL: `http://localhost:8080/<your-post-slug>/`
    *   Check for:
        *   Correct rendering of title, subtitle, meta (date/author).
        *   All sections appearing correctly.
        *   All images loading (check developer console for 404 errors).
        *   Correct display of tags at the bottom.
        *   Working navigation links.

9.  **Commit to Git:**
    *   Once satisfied with the preview:
        *   Stop the server (`Ctrl+C`).
        *   Stage the new/modified files (the `.md` file and the new image directory/files).
          ```bash
          git status
          git add .
          ```
        *   Commit the changes with a descriptive message:
          ```bash
          git commit -m "feat: Add blog post '<Your Post Title>'"
          ```
        *   Push the changes to the remote repository:
          ```bash
          git push origin main
          ```

---

**Potential Future Automation Points:**

*   Script to generate a boilerplate `.md` file with front matter structure based on a slug.
*   Script to automatically create the image subdirectory.
*   Script/tool to assist with renaming/moving images based on section titles or prompts.
*   Integration of the watermarking script into the build process or as an easier-to-run task (potentially only watermarking for production builds).
*   A simple CLI or GUI to manage post creation steps.

---
    *   Choose a sh