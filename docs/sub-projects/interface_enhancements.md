# Revised Plan: Admin Interface Enhancements

**Goal:** Enhance the existing Flask-based Admin Interface (`app.py`, `admin_index.html`, `admin_post_detail.html`) to provide better status visualization, facilitate manual workflow actions, and improve usability for managing the blog post lifecycle.

**Current State:**
*   Admin Index (`/`) lists posts and their Clan.com publish status. Includes a button to trigger deployment via `/api/publish_clan`. Displays script output.
*   Admin Post Detail (`/admin/post/<slug>`) displays post metadata, detailed workflow status (including per-image statuses), and image previews.
*   API endpoints exist for updating status (`/api/update_status`) and triggering deployment (`/api/publish_clan`).
*   Image processing is handled by a separate script (`scripts/process_imported_image.py`), triggered manually.
*   Watermarking status is tracked per image but applied manually (no UI trigger).

---

### **Phase 1: Status Visualization & Basic Interaction (Admin Index)**

*   **Goal:** Improve clarity of the main dashboard.
*   **Tasks:**
    *   [ ] **1.1. Refine Status Display (`templates/admin_index.html`):**
        *   [ ] Use CSS classes based on `clan_com_status_val` (e.g., `status-complete`, `status-error`, `status-pending`) to visually style the status text (colors, icons).
        *   [ ] If status is 'error', display the `last_error` message (truncated) from `workflow_status.json` directly on this page (perhaps in a tooltip or small text below the status). *(Requires passing this data from the `index` route in `app.py`)*.
    *   [ ] **1.2. Enhance Action Log (`templates/admin_index.html` & JS):**
        *   [ ] Style the `<pre id="log-output">` area for better readability.
        *   [ ] Add timestamps to messages logged by the frontend JavaScript.
        *   [ ] Consider automatically scrolling the log area to the bottom on new output.
        *   [ ] Clearly indicate SUCCESS or ERROR based on the `data.success` flag returned by the API.
    *   [ ] **1.3. Deployment Button State (`templates/admin_index.html` & JS):**
        *   [ ] Disable the "Publish/Update" button while a job for that specific slug is running (prevent double-clicks). Re-enable on completion/error.
        *   [ ] Optionally change button text (e.g., "Publishing...") while running.

---

### **Phase 2: Detailed Workflow Interaction (Admin Post Detail)**

*   **Goal:** Allow users to manually update workflow statuses directly from the detail page. *(This directly addresses Priority 4 from CURRENT_priorities.md)*.
*   **Tasks:**
    *   [ ] **2.1. Make Stage Statuses Clickable (`templates/admin_post_detail.html`):**
        *   [ ] Identify elements displaying key statuses (e.g., `images.status`, `writing.status`, `images.prompts_defined_status`, etc.).
        *   [ ] Wrap these status display elements (or add adjacent icons/buttons) with appropriate classes/data attributes indicating the `slug` and the full `stage_key` (e.g., `data-slug="{{ slug }}" data-stage-key="images.status"`).
    *   [ ] **2.2. Make *Individual Image* Statuses Clickable (`templates/admin_post_detail.html`):**
        *   [ ] Inside the `{% for image in images_detailed %}` loop, identify elements displaying statuses like `prompt_status`, `assets_prepared_status`, `metadata_integrated_status`, and `watermarking_status`.
        *   [ ] Wrap these (or add icons/buttons) with classes/data attributes indicating the `slug` and the *nested* `stage_key` (e.g., `data-slug="{{ slug }}" data-stage-key="images.watermarks.{{ image.id }}"`).
    *   [ ] **2.3. Implement Status Update JavaScript (`templates/admin_post_detail.html`):**
        *   [ ] Add a general JavaScript event listener for clicks on elements marked as status triggers (e.g., class `.status-trigger`).
        *   [ ] In the handler:
            *   [ ] Extract `slug` and `stage_key` from data attributes.
            *   [ ] Determine the *current* status and the *next* logical status (define cycle logic: e.g., pending -> complete).
            *   [ ] Make a `fetch` POST request to `/api/update_status/{{ slug }}/{{ stage_key }}` with the `{"status": "new_status"}` in the body.
            *   [ ] Visually update the clicked element (text, CSS class) immediately.
            *   [ ] Handle API success/error responses (revert visual change on error, log errors).
    *   [ ] **2.4. (Optional) Add Trigger for Image Processing Script?:**
        *   [ ] Consider adding a button "Process Imported Images for Post".
        *   [ ] Requires a *new* API endpoint in `app.py` that finds images for the slug in the import directory and runs `scripts/process_imported_image.py` for them. *(More complex, might defer)*.

---

### **Phase 3: Linking & Usability**

*   **Goal:** Integrate documentation and improve navigation.
*   **Tasks:**
    *   [ ] **3.1. Add Documentation Links (`templates/admin_index.html`, `templates/admin_post_detail.html`):**
        *   [ ] Add small help icons (`?`) or links next to relevant sections (e.g., Workflow Stages, Image Processing).
        *   [ ] Link these to specific sections within the `README.md` or relevant files in `/docs/` using fragment identifiers (#) (e.g., `href="../README.md#workflow-status" target="_blank"`). *(Note: Ensure Eleventy copies docs/README to _site if linking there, or use relative paths)*.
        *   [ ] Add corresponding anchors (`<a name="workflow-status"></a>`) or use Markdown heading IDs in the target documentation files.
    *   [ ] **3.2. Improve Navigation:**
        *   [ ] Ensure consistent navigation between the Index and Detail pages.
        *   [ ] Add breadcrumbs if complexity increases.
    *   [ ] **3.3. Visual Refresh (CSS):**
        *   [ ] Apply more polished styling to tables, buttons, status indicators, and layout for better readability and professional feel.

---

**Implementation Notes:**

*   Focus on Phase 1 and Phase 2 first to get the core status interaction working.
*   Leverage the existing `app.py` structure and helper functions.
*   Keep JavaScript minimal and focused initially; consider a lightweight library like Alpine.js later if complexity grows significantly.
*   Remember that changes requiring data from `app.py` (like `last_error`) need the relevant route functions to be updated to load and pass that data to the template.