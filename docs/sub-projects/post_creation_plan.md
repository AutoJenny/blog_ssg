# Implementation Plan: Blog Post Detail & Workflow Page

**Goal:** Create a dedicated web page within the Flask interface for managing the workflow of a single blog post, displaying its status using traffic lights and collapsible sections, and allowing interaction with specific stages.

---

## Phase 1: Data Structure & Backend Route

*   [ ] **1.1. Finalize Workflow Status Structure (`_data/workflow_status.json`):**
    *   Review the proposed structure (from previous discussion) with stages (`conceptualisation`, `authoring`, `metadata`, `images`, `validation`, `publishing_clancom`, `watermarking`, `syndication`) and sub-statuses.
    *   Confirm status values (e.g., `pending`, `partial`, `complete`, `error`).
    *   Decide which data points belong here vs. front matter for MVP (recommend keeping content/prompts in `.md` for now, store only status and operational IDs like `clan_com_post_id` here).
    *   Manually populate initial entries for `kilt-evolution` and `quaich-traditions` based on their current state.
*   [ ] **1.2. Create Flask Route (`app.py`):**
    *   Define a new route: `@app.route('/admin/post/<string:slug>')`.
    *   Import necessary modules (`os`, `json`, `pathlib`, `frontmatter`).
    *   Implement the route function `view_post_detail(slug)`:
        *   Construct paths to `posts/<slug>.md` and `_data/workflow_status.json`.
        *   Load the post's front matter using `frontmatter.load()`. Handle file not found.
        *   Load the entire `workflow_status.json` using the helper function. Handle file/JSON errors.
        *   Extract the specific status data for the requested `slug` from the loaded workflow data (provide default/empty status if not found).
        *   Pass both the `metadata` (from front matter) and the `status_data` (for this slug) to a new template.
        *   Render the template: `render_template('admin_post_detail.html', slug=slug, metadata=metadata, status=status_data)`.
*   [ ] **1.3. Create Detail Template Stub (`templates/admin_post_detail.html`):**
    *   Create the basic HTML file `templates/admin_post_detail.html`.
    *   Add basic boilerplate (head, body).
    *   Display the post title prominently using `{{ metadata.title }}`.
    *   Add placeholders for where the workflow stages will go.
*   [ ] **1.4. Link from Index Page (`templates/admin_index.html`):**
    *   Change the main post title link on the index page to point to this new detail route:
        ```html
        <!-- Find this line in the index template loop -->
        <strong><a href="{{ url_for('view_post_detail', slug=post.slug) }}">{{ post.title }}</a></strong>
        ```
        *(Note: Using `url_for` is Flask's preferred way to generate URLs for routes)*. Make sure to import `url_for` from `flask` in `app.py`.
*   [ ] **1.5. Test Backend:** Run Flask app. Navigate from the index page to `/admin/post/kilt-evolution`. Verify the detail page loads (even if mostly empty) and shows the correct title. Check terminal logs for errors.

---

## Phase 2: Display Workflow Stages & Status

*   [ ] **2.1. Implement Collapsible Sections (`admin_post_detail.html`):**
    *   Use HTML `<details>` and `<summary>` tags for each major workflow stage (Conceptualisation, Authoring, etc.).
        ```html
        <details class="workflow-stage" data-stage-key="conceptualisation">
            <summary>
                <span class="traffic-light" data-status="{{ status.stages.conceptualisation.status | default('pending') }}"></span> <!-- Traffic light placeholder -->
                I. Conceptualisation
            </summary>
            <div class="stage-content">
                <!-- Content for this stage goes here -->
                <p>Status: {{ status.stages.conceptualisation.status | default('pending') }}</p>
                <p>Notes: {{ status.stages.conceptualisation.notes | default('N/A') }}</p>
            </div>
        </details>
        <!-- Repeat for all stages -->
        ```
*   [ ] **2.2. Add Traffic Light CSS (`admin_post_detail.html` or separate CSS):**
    *   Define CSS classes for the traffic light span based on status:
        ```css
        .traffic-light { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; vertical-align: middle; }
        .traffic-light[data-status="pending"] { background-color: #ccc; /* Grey */ }
        .traffic-light[data-status="partial"] { background-color: #f0ad4e; /* Orange */ }
        .traffic-light[data-status="complete"] { background-color: #5cb85c; /* Green */ }
        .traffic-light[data-status="error"] { background-color: #d9534f; /* Red */ }
        ```
*   [ ] **2.3. Populate Stage Content (`admin_post_detail.html`):**
    *   Inside each `<details>` block's `div.stage-content`:
        *   Display relevant status details read from the `status` variable passed by Flask (e.g., `{{ status.stages.images.prompts_defined_status }}`). Use the `default()` filter for safety (e.g., `| default('pending')`).
        *   Display relevant data read from the `metadata` variable (e.g., show `metadata.description` in the Metadata stage). Use read-only fields or simple text for now.
        *   Add placeholder text or simple input fields for data that *will* be edited later (e.g., a textarea for stage notes).
*   [ ] **2.4. Test Display:** Run Flask app. Navigate to a post detail page. Verify:
    *   All stages appear as collapsible sections.
    *   Traffic lights reflect the status loaded from `_data/workflow_status.json`.
    *   Relevant data points (from metadata and status file) are displayed within the sections.

---

## Phase 3: Implement Manual Status Updates

*   [ ] **3.1. Add Status Change Buttons/Forms (`admin_post_detail.html`):**
    *   Within each stage's content (`div.stage-content`), add simple buttons or dropdowns to manually mark a stage/sub-stage as complete, pending, etc.
    *   Assign data attributes to these elements indicating the `slug`, `stage_key` (e.g., `authoring`), and desired `new_status`.
        ```html
        <button class="status-update-button" data-slug="{{ slug }}" data-stage="images" data-new-status="complete">Mark Images Stage Complete</button>
        ```
*   [ ] **3.2. Create Flask API Endpoint for Status Update (`app.py`):**
    *   Define a route like `@app.route('/api/update_status/<string:slug>/<string:stage_key>', methods=['POST'])`.
    *   Import `request` from `flask`.
    *   Inside the route function:
        *   Get the `new_status` from the request data (e.g., `request.json.get('status')`).
        *   Load the `workflow_status.json` data.
        *   Find the entry for the `slug`.
        *   Update the `status` field for the specified `stage_key`.
        *   Add/update the `last_updated` timestamp.
        *   Save the modified data back to `workflow_status.json` using `save_syndication_data`.
        *   Return a success/failure JSON response: `jsonify({"success": True/False, "slug": slug, "stage": stage_key, "new_status": new_status})`.
*   [ ] **3.3. Add JavaScript for Status Update (`admin_post_detail.html`):**
    *   Add an event listener for clicks on `.status-update-button`.
    *   When clicked:
        *   Get `slug`, `stage_key`, `new_status` from data attributes.
        *   Use `fetch` to send a `POST` request to `/api/update_status/...` with the `new_status` in the request body (as JSON).
        *   Handle the response: update the corresponding traffic light and status text on the page dynamically based on the response. Log success/failure.
*   [ ] **3.4. Test:** Run Flask app. Go to a detail page. Click a status update button. Verify the traffic light changes, the status text updates (if you added dynamic updates), and the `_data/workflow_status.json` file is modified correctly.

---

## Phase 4: Integrate Action Buttons

*   [ ] **4.1. Place Action Buttons (`admin_post_detail.html`):**
    *   Move or copy the "Publish/Update Clan.com" button into the appropriate stage section (e.g., "Publishing Workflow"). Ensure it has the correct `data-slug`.
    *   Add placeholder buttons for other actions (Watermark, Syndicate) in their relevant stage sections.
*   [ ] **4.2. Connect Buttons to API Calls (JavaScript):**
    *   Ensure the JavaScript event listener correctly identifies clicks on `.publish-clan-button` (and future action buttons).
    *   Ensure it calls the correct Flask API endpoint (`/api/publish_clan/<slug>` for the publish button).
    *   Ensure the log output is displayed correctly in the log area on the detail page.
*   [ ] **4.3. Test Action Trigger:** Run Flask app. Navigate to the detail page. Click the "Publish/Update Clan.com" button *within the stage section*. Verify it triggers the script and displays output in the log area.

---