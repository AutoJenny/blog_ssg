# Development Plan: Content Creation Workflow

**Goal:** Streamline, assist, and eventually automate the creation and preparation of blog posts and associated media (initially images), integrating LLM capabilities while maintaining brand authenticity.

**Current State:**
*   Blog posts are created manually by editing Markdown files (`.md`) in the `posts/` directory.
*   Images are processed manually via `scripts/process_imported_image.py`, requiring command-line execution with metadata arguments.
*   Front matter structure includes fields for title, date, tags, description, and image IDs (`headerImageId`, `sections.imageId`, `conclusion.imageId`).

---

### **Phase 1: Foundational Improvements (Near-Term)**

*   **Goal:** Improve the manual process and add basic UI integration.
*   **Tasks:**
    *   [ ] **1.1. UI Trigger for Image Processing:** Implement the "Process Imported Images for Post" button and corresponding API endpoint in `app.py`. *(See Admin Interface Plan: 2.1)*.
    *   [ ] **1.2. Basic Post Creation UI:** Implement simple form and API endpoint to create new `.md` files with basic front matter. *(See Admin Interface Plan: 2.2)*.
    *   [ ] **1.3. Basic Metadata Editing UI:** Implement form and API endpoint to edit existing front matter in `.md` files. *(See Admin Interface Plan: 2.3)*.
    *   [ ] **1.4. Refine Front Matter Schema:** Define standard required/optional fields clearly (e.g., add `short_content`, `categories`, `meta_fields`, `list_thumbnail`, `post_thumbnail` if needed by API/syndication, clarify usage of `description`/`summary`). Update documentation/examples.

---

### **Phase 2: Integrating LLM Assistance (Mid-Term)**

*   **Goal:** Leverage LLMs to assist the human editor in content creation tasks.
*   **Tasks:**
    *   [ ] **2.1. LLM Backend Service/Module:**
        *   [ ] Choose LLM provider/API (e.g., OpenAI, Anthropic, local model).
        *   [ ] Implement secure API key handling (using `.env`).
        *   [ ] Create Python functions/module (`llm_utils.py`?) to handle common API calls (e.g., text generation, summarization). Include error handling.
    *   [ ] **2.2. Title/Headline Suggestions:**
        *   [ ] Create API endpoint in `app.py` that takes draft content/topic -> calls LLM function -> returns suggestions.
        *   [ ] Add UI button in Admin Interface (post edit view) to trigger this API.
    *   [ ] **2.3. Alt Text Suggestions:**
        *   [ ] Create API endpoint in `app.py` that takes image description/caption/ID -> calls LLM function -> returns alt text suggestions.
        *   [ ] Add UI button in Admin Interface (image library view or post detail image section) to trigger.
    *   [ ] **2.4. Summary/Excerpt Generation:**
        *   [ ] Create API endpoint to take post content -> call LLM summarization -> return summary (for `short_content` or meta description).
        *   [ ] Add UI button in Admin Interface.
    *   [ ] **2.5. Content Outline Generation:**
        *   [ ] Create API endpoint to take topic/title -> call LLM -> return suggested section headings/outline.
        *   [ ] Add UI button (perhaps in post creation view).

---

### **Phase 3: Towards Automated Drafting (Longer-Term)**

*   **Goal:** Implement pipelines for more automated content generation, requiring human review.
*   **Tasks:**
    *   [ ] **3.1. Define Drafting Pipeline:** Formalize steps: Topic -> Outline -> Section Drafts -> Image Prompt Ideas -> Human Review -> Final Polish.
    *   [ ] **3.2. Implement Pipeline Orchestration:**
        *   [ ] Extend `workflow_status.json` schema to track pipeline steps.
        *   [ ] Develop backend logic (in `app.py` or separate service) to manage transitions between steps, potentially calling different LLM functions.
        *   [ ] Create UI views in Admin Interface to manage and interact with pipeline stages (e.g., approve outline, view drafts).
    *   [ ] **3.3. Image Prompt Generation:** Implement LLM call to suggest image generation prompts based on section content/context.
    *   [ ] **3.4. Brand Voice/Authenticity Checks:**
        *   [ ] Develop prompts or fine-tuning methods to align LLM output with CLAN.com's voice.
        *   [ ] Implement automated checks (LLM evaluating output against guidelines?) to flag content needing careful review.

---