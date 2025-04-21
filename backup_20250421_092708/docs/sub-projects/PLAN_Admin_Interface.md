# Development Plan: Admin Interface

**Goal:** Enhance the existing Flask-based Admin Interface (`app.py`, `admin_index.html`, `admin_post_detail.html`) to provide better status visualization, facilitate manual workflow actions, integrate content creation/editing features, and improve overall usability for managing the CIPS workflow.

**Current State:**
*   Admin Index (`/`) lists posts and their Clan.com publish status. Includes a button to trigger deployment via `/api/publish_clan`. Displays script output. Status updates automatically after deployment trigger.
*   Admin Post Detail (`/admin/post/<slug>`) displays post metadata, detailed workflow status (incl. per-image statuses), and image previews (via static route).
*   API endpoints exist for updating status (`/api/update_status`), triggering deployment (`/api/publish_clan`), and triggering the old watermark script (`/api/watermark_all` - needs review).

---

### **Phase 1: UI Polish & Workflow Interaction (Near-Term)**

*   **Goal:** Improve immediate usability and enable manual status updates.
*   **Tasks:**
    *   [ ] **1.1. Refine Status Display (Index Page):**
        *   [ ] Use CSS classes (e.g., `status-complete`, `status-error`, `status-pending`) to visually style the `clan_com_status` text.
        *   [ ] Display truncated `last_error` message on index page if status is 'error'. *(Requires passing data via `index` route)*.
    *   [ ] **1.2. Enhance Action Log (Index Page):**
        *   [ ] Improve CSS styling of `<pre id="log-output">`.
        *   [ ] Add JS timestamps to frontend log messages.
        *   [ ] Implement auto-scrolling.
        *   [ ] Clearly indicate overall SUCCESS/ERROR in log based on API response.
    *   [ ] **1.3. Deployment Button State (Index Page):**
        *   [ ] Add JS to disable button during API call, re-enable after.
        *   [ ] Optionally change button text while running.
    *   [ ] **1.4. Make Statuses Clickable (Detail Page):** *(Was Priority 4)*
        *   [ ] Add UI elements (buttons/icons/styled text) with `data-slug`, `data-stage-key` attributes for stage-level statuses (e.g., `images.status`).
        *   [ ] Add UI elements with `data-slug`, `data-stage-key` for per-image statuses (e.g., `images.watermarks.<id>`).
        *   [ ] Implement JS click handler: determine next status, call `/api/update_status`, update UI visually.

---

### **Phase 2: Content & Image Management Features (Mid-Term)**

*   **Goal:** Enable basic content creation and image processing management within the UI.
*   **Tasks:**
    *   [ ] **2.1. Trigger Image Processing:**
        *   [ ] Add button on relevant pages (Index or Detail?): "Process Imported Images for [Slug]".
        *   [ ] Create new API endpoint in `app.py` (e.g., `/api/process_images/<slug>`).
        *   [ ] API logic: Find relevant images for slug in `_SOURCE_MEDIA/_IMPORT_IMAGES/`. Run `scripts/process_imported_image.py` for each via `subprocess.run`. Aggregate results/errors.
        *   [ ] Update UI based on API response.
    *   [ ] **2.2. Basic Post Creation UI:**
        *   [ ] Add "Create New Post" button/link.
        *   [ ] Create new template (`admin_post_create.html`?) with a form for `title`, `slug` (auto-suggest from title?), basic metadata (date defaults to now).
        *   [ ] Create new route/API endpoint in `app.py` to handle form submission: Create basic `.md` file in `posts/` with front matter. Redirect to detail page.
    *   [ ] **2.3. Basic Metadata Editing UI (Detail Page):**
        *   [ ] Display current front matter fields (title, description, tags, custom fields?) in editable form elements.
        *   [ ] Add "Save Metadata" button.
        *   [ ] Create new API endpoint in `app.py` (e.g., `/api/update_metadata/<slug>`) to handle form submission: Load `.md` file, update front matter, save file. Handle potential `frontmatter` library errors.
    *   [ ] **2.4. Basic Image Library Viewing:**
        *   [ ] Add new route/template to display contents of `_data/image_library.json` in a table (ID, description, paths).
        *   [ ] Add basic filtering/searching if needed.

---

### **Phase 3: Advanced Features & Usability (Longer-Term)**

*   **Goal:** Add more sophisticated editing, LLM integrations, and documentation links.
*   **Tasks:**
    *   [ ] **3.1. Integrate Markdown Editor:** Replace simple text editing (if implemented) with a JS Markdown editor (e.g., SimpleMDE, EasyMDE) for the main post content. Requires API endpoint to save content body.
    *   [ ] **3.2. Enhance Image Library UI:** Add edit/delete capabilities (requires API endpoints to modify `image_library.json`). Consider image upload functionality.
    *   [ ] **3.3. Add Documentation Links:** Implement links to README/docs sections from relevant UI parts.
    *   [ ] **3.4. Implement LLM Hooks (UI Side):** Add buttons/UI elements to trigger backend LLM functions (defined in Content Creation plan) like "Suggest Title", "Suggest Alt Text", etc. Requires corresponding API endpoints.
    *   [ ] **3.5. Improve Navigation/Layout:** Implement breadcrumbs, refine overall CSS, potentially adopt lightweight JS framework (HTMX, Alpine.js) if complexity warrants it.

---