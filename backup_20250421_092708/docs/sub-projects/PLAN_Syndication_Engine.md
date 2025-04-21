# Development Plan: Syndication Engine

**Goal:** Develop a modular and extensible system to adapt core blog content and publish it effectively across multiple relevant channels (starting with Facebook), tracking the status and performance of each syndicated piece.

**Current State:**
*   No syndication functionality implemented.
*   Blog publishing to clan.com is functional via `scripts/post_to_clan.py` and API trigger.
*   `workflow_status.json` has basic structure for tracking stages, can be extended for syndication.

---

### **Phase 1: Facebook MVP (Immediate Focus)**

*   **Goal:** Implement basic posting to a Facebook Page.
*   **Tasks:** *(Aligns with Current Priorities: Priority 1)*
    *   [ ] **1.1. Facebook API Setup:** Obtain App credentials, Page Token; store securely in `.env`.
    *   [ ] **1.2. Develop Core Function (`post_to_facebook`):** Create Python function (e.g., in `scripts/syndication_utils.py`) using `requests` to call Graph API (decide link post vs. image post initially). Handle response/errors.
    *   [ ] **1.3. Create API Endpoint (`app.py`):** `/api/syndicate/facebook/<slug>` to orchestrate loading data and calling `post_to_facebook`.
    *   [ ] **1.4. Implement Status Tracking:** Update `/api/syndicate/facebook` endpoint to modify `_data/workflow_status.json` (create `stages.syndication.facebook` entry, set `status`, `postId`/`last_error`).
    *   [ ] **1.5. Basic UI Trigger:** Add "Post to Facebook" button in `admin_post_detail.html` with JS to call the API and display results.

---

### **Phase 2: Core Engine & Instagram (Mid-Term)**

*   **Goal:** Build foundational syndication architecture and add Instagram support.
*   **Tasks:**
    *   [ ] **2.1. Refine Workflow Schema:** Define detailed, consistent structure within `workflow_status.json` for multiple channels (e.g., `stages.syndication.<channel>.status`, `stages.syndication.<channel>.postId`, `stages.syndication.<channel>.publishedUrl`, `stages.syndication.<channel>.last_attempt`, `stages.syndication.<channel>.last_error`).
    *   [ ] **2.2. Develop Content Adaptation Logic (Initial):**
        *   [ ] Create helper functions (Python) to generate channel-specific text (e.g., shorter caption for Instagram, hashtags) from post title/summary/tags. *(LLM hook later)*.
        *   [ ] Decide which image version to use for each channel (e.g., watermarked for social?).
    *   [ ] **2.3. Implement Instagram Publisher:**
        *   [ ] Research & Setup: Instagram Graph API (requires Facebook). Permissions needed (e.g., `instagram_content_publish`). Store credentials.
        *   [ ] Develop `post_to_instagram` function: Handle image/video upload, caption formatting (using adaptation logic).
        *   [ ] Create API endpoint `/api/syndicate/instagram/<slug>`.
        *   [ ] Integrate status updates in API endpoint.
        *   [ ] Add UI trigger button.
    *   [ ] **2.4. Refactor to Plugin/Module Structure (Optional but recommended):** Create a base class or standard structure for channel publishers to make adding new channels easier.

---

### **Phase 3: Scheduling & Content Adaptation Engine (Mid- to Long-Term)**

*   **Goal:** Enable scheduled publishing and introduce LLM-powered content adaptation.
*   **Tasks:**
    *   [ ] **3.1. Scheduling Capability:**
        *   [ ] Add `scheduled_publish_time` field(s) to workflow status schema.
        *   [ ] Implement UI elements (datetime picker?) to set schedule times.
        *   [ ] Develop scheduler mechanism (e.g., `APScheduler` in a separate process, cron job calling dedicated API endpoint) to check `workflow_status.json` and trigger relevant syndication APIs at the scheduled time.
    *   [ ] **3.2. Develop LLM Content Adaptation Engine:**
        *   [ ] Create dedicated service/functions (Python).
        *   [ ] Input: Core content, target channel, brand guidelines/persona.
        *   [ ] Output: Adapted text (captions, summaries, hooks), potentially suggested hashtags.
        *   [ ] Integrate calls to this engine within the specific channel publisher functions (e.g., `post_to_facebook`, `post_to_instagram`).

---

### **Phase 4: Additional Channels & Advanced Features (Longer-Term)**

*   **Goal:** Expand reach and sophistication.
*   **Tasks:**
    *   [ ] **4.1. Implement LinkedIn Publisher:** Research API, develop function, API endpoint, UI trigger, status tracking.
    *   [ ] **4.2. Implement Twitter/X Publisher:** Research API, develop function, API endpoint, UI trigger, status tracking.
    *   [ ] **4.3. Implement dev.to/Medium Publisher:** Research APIs/publishing methods, develop function, API endpoint, UI trigger, status tracking. Handle Markdown conversion/formatting differences.
    *   [ ] **4.4. Performance Tracking Integration:** Add logic to fetch basic engagement stats from platform APIs and store/display them. *(Links to Analytics Plan)*.
    *   [ ] **4.5. Video Syndication:** Extend engine to handle video uploads/publishing to relevant platforms (YouTube, Reels, etc.). *(Links to Media Development Plan)*.

---