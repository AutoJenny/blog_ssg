# Project Plan: CLAN.com Integrated Promotion System (CIPS)

## 1. Introduction & Vision

**1.1. Overview:**
This document outlines the phased development plan for the CLAN.com Integrated Promotion System (CIPS). CIPS aims to evolve from the current Eleventy-based blog generator and Flask admin tool into a sophisticated, multi-channel content creation, management, and promotion engine. The ultimate goal is a highly automated system leveraging Large Language Models (LLMs) and other AI tools to support brand building and drive sales for CLAN.com, while strictly adhering to its reputation for authenticity and expertise in Scottish heritage.

**1.2. Core Goal:**
To develop a local-first (initially) management interface that orchestrates the creation, adaptation, scheduling, deployment, and monitoring of promotional content across multiple channels (Blog, Social Media, potentially others), significantly automating the process through integrated AI/LLM capabilities.

**1.3. Strategic Context (CLAN.com):**
All development must align with CLAN.com's brand identity:
*   **Authenticity:** Content must be accurate, respectful, and reflect deep heritage knowledge.
*   **Expertise:** Position CLAN.com as a world leader in tartan and Scottish heritage.
*   **Brand Building:** Focus on raising awareness, desirability, and trust.
*   **Subtle Promotion:** Avoid hard-sell tactics; integrate product/service awareness naturally within valuable content.
*   **Community Engagement:** Foster a sense of community around shared heritage interests.

**1.4. Architectural Philosophy:**
The system will be designed with the following principles:
*   **Modularity:** Features (content types, channels, AI tools, modules) should be developed as distinct components for easier extension ("bolt-on").
*   **Extensibility:** Utilize clear APIs, data schemas, and event hooks to allow future integrations.
*   **Data-Centric:** Centralize core data (content, assets, workflow status, personas, performance) in well-defined structures.
*   **API-Driven:** Encourage internal components (Admin UI, LLM connectors, channel publishers) to communicate via internal APIs where feasible.
*   **LLM Integration Points:** Design workflows with clear stages where LLM assistance or automation can be plugged in.
*   **User Experience (Admin):** Provide an intuitive interface for managing increasingly complex workflows and automation.
*   **Measurability:** Build in mechanisms to track content performance and system effectiveness.

**1.5. Current Status (Foundation):**
*   Eleventy SSG configured for blog generation.
*   Basic Flask Admin UI (`app.py`) providing read-only views of posts and workflow status.
*   Workflow tracking established in `_data/workflow_status.json`.
*   Image library concept (`_data/image_library.json`) and responsive image shortcode implemented.
*   Manual watermarking script (`scripts/watermark_images.py`).
*   Manual SFTP deployment script (`scripts/post_to_clan.py`) triggerable via API.
*   Basic API for status updates and deployment triggering exists.

---

## 2. Phased Development Plan

**Phase 1: Foundation Hardening & Core Content Workflow (Consolidating the Base)**

*Goal: Ensure the existing blog generation and basic admin UI are robust, stable, and use standardized data structures.*

*   [x] Set up Eleventy (11ty) as the Static Site Generator.
*   [x] Configure core Eleventy settings (`.eleventy.js`).
*   [x] Define basic site structure (input/output dirs, includes, layouts).
*   [x] Implement Markdown processing for posts.
*   [x] Define Core Post Front Matter Structure (Title, Date, Tags, Image IDs, Sections, Conclusion).
*   [x] Create basic Nunjucks templates (`base.njk`, `post.njk`, `index.njk`).
*   [x] Implement post collections (e.g., sorted by date).
*   [x] Implement tag collections/pages.
*   [x] Set up CSS handling/passthrough copy.
*   [x] Establish `_data/workflow_status.json` as the central workflow tracking file.
    *   [x] Define initial schema for core stages (e.g., writing, images, publishing_clancom).
*   [x] Refactor `app.py` for robust data loading/saving (`load_json_data`, `save_json_data`).
*   [x] Refactor `app.py` to use standardized constants and path handling.
*   [x] Ensure basic Admin UI (`/`, `/admin/post/<slug>`) accurately reflects data from `workflow_status.json`.
*   [x] Implement basic API (`/api/update_status`) for manual workflow state changes.
*   [ ] **Define Formal JSON Schemas:** Document and potentially validate the structure of `workflow_status.json` and `image_library.json` to ensure consistency.
*   [ ] **Improve Error Handling & Logging:** Enhance robustness in `app.py` and scripts.

**Phase 2: Enhanced Image Workflow & Management**

*Goal: Streamline image preparation, integrate watermarking better, and prepare for AI assistance.*

*   [x] Integrate `eleventy-img` plugin for responsive image generation.
*   [x] Define and implement a Nunjucks shortcode (`image`) for responsive images.
*   [x] Create a central image library data file (`_data/image_library.json`).
*   [x] Establish system/schema for image metadata within `image_library.json` (Desc, Prompt, Source, Alt, Caption).
*   [x] Implement manual image watermarking script (`scripts/watermark_images.py`).
*   [x] Define workflow structure for tracking image sub-stages within `_data/workflow_status.json`.
    *   [x] Track image prompt status.
    *   [x] Track image source asset preparation status (file existence).
    *   [x] Track image metadata integration status (alt, caption).
    *   [x] Track **per-image** watermarking status within the post's workflow entry.
*   [x] Display detailed image workflow status (including watermarking) in Admin UI (`/admin/post/<slug>`).
*   [ ] **Specify Watermarked Image Output:** Define clear location/naming for watermarked images (e.g., `images/posts/watermarked/`). Update script if needed.
*   [ ] **Integrate Watermarking Trigger (Optional):**
    *   [ ] Develop API endpoint in `app.py` to trigger `watermark_images.py` for a specific image/post.
    *   [ ] Add button in Admin UI to trigger watermarking via API.
    *   [ ] Modify `watermark_images.py` to accept parameters (image ID/path, slug) and update `workflow_status.json` upon completion via API call or direct file edit.
*   [ ] **Image Library Management in Admin UI:**
    *   [ ] View/Browse `image_library.json` contents.
    *   [ ] Basic search/filter capabilities.
*   [ ] **LLM Hook: Alt Text Generation:**
    *   [ ] Add button in Admin UI (per image) to "Suggest Alt Text".
    *   [ ] Implement backend logic to call an LLM API (using image description/caption/prompt) to generate alt text suggestions.
    *   [ ] Allow user to accept/edit/reject suggestion (updates `image_library.json`).

**Phase 3: Admin Interface - Towards Content Creation & Editing**

*Goal: Transform the Admin UI from read-only to a functional content creation and management hub.*

*   [x] Plan Admin UI features (`docs/interface_plan.md`).
*   [x] Develop Flask backend (`app.py`) with basic data loading/display routes.
*   [ ] **Implement CRUD for Blog Posts:**
    *   [ ] Create New Post: UI form to input title, slug (auto-suggest?), basic metadata -> creates new `.md` file with front matter.
    *   [ ] Edit Post Metadata: UI form to modify front matter fields -> saves changes to `.md` file.
    *   [ ] Edit Post Content: Integrate a Markdown editor (e.g., SimpleMDE, EasyMDE) to edit the body of the `.md` file -> saves changes.
    *   [ ] Delete Post: Confirmation -> removes `.md` file (and potentially associated workflow data?).
*   [ ] **Implement CRUD for Image Library:**
    *   [ ] Add New Image Entry: UI form to input description, prompt, source details, metadata -> adds entry to `image_library.json`.
    *   [ ] Edit Image Entry: UI form to modify fields -> updates `image_library.json`.
    *   [ ] Delete Image Entry: Confirmation -> removes entry (handle referenced images?).
    *   [ ] (Optional) Image Upload: Handle file uploads, place in `images/` directory, create corresponding library entry.
*   [ ] **Refine Workflow Management UI:**
    *   [ ] Make status indicators interactive (clickable) to trigger status updates via `/api/update_status`.
    *   [ ] Add UI elements for triggering actions (like integrated watermarking, deployment).
*   [ ] **LLM Hook: Content Assistance:**
    *   [ ] Title Suggestions: Button to call LLM API based on draft content/topic.
    *   [ ] Summary Generation: Button to generate a post summary.
    *   [ ] Content Outline: Generate potential section headings based on a title/topic.
*   [ ] **UI Framework Adoption (Optional but Recommended):** Consider HTMX, Alpine.js, or a lightweight frontend framework to improve UI reactivity without a full SPA build.

**Phase 4: Multi-Channel Syndication Engine**

*Goal: Extend beyond the blog to automatically adapt and publish content to key social media channels.*

*   [x] Plan syndication strategy (`docs/syndication_plan.md`).
*   [x] Define initial structure for tracking syndication status in `workflow_status.json`.
*   [ ] **Develop Core Syndication Module:**
    *   [ ] Define generic internal representation of content adaptable for different channels.
    *   [ ] Create plugin architecture for adding new channel publishers.
*   [ ] **Refine Workflow Schema:** Add detailed per-channel tracking in `workflow_status.json` (e.g., `stages.syndication.instagram.status`, `stages.syndication.instagram.postId`, `stages.syndication.facebook.status`).
*   [ ] **Implement Blog Publishing Integration:**
    *   [x] Deployment script (`post_to_clan.py`) exists.
    *   [x] API trigger (`/api/publish_clan`) exists.
    *   [ ] Enhance script/API to update `workflow_status.json` (`publishing_clancom` stage) reliably on success/failure.
*   [ ] **Implement Instagram Publisher:**
    *   [ ] Research Instagram API requirements (likely requires Facebook Graph API).
    *   [ ] Develop logic to adapt blog content/images for Instagram (e.g., select key image, generate concise caption - *LLM opportunity*). Respect brand guidelines.
    *   [ ] Implement API calls to post images/carousels/reels (initially images).
    *   [ ] Store resulting Post ID and update status in `workflow_status.json`.
    *   [ ] Add UI elements in Admin Interface to preview, approve, and trigger Instagram publication.
*   [ ] **Implement Facebook Publisher:**
    *   [ ] Research Facebook Graph API requirements.
    *   [ ] Develop logic to adapt content for Facebook (e.g., generate link preview text, longer text post with image/link - *LLM opportunity*). Respect brand guidelines.
    *   [ ] Implement API calls to post to a Page/Group.
    *   [ ] Store resulting Post ID/URL and update status in `workflow_status.json`.
    *   [ ] Add UI elements in Admin Interface to preview, approve, and trigger Facebook publication.
*   [ ] **Develop Content Adaptation Engine (LLM Powered):**
    *   [ ] Create service/functions that take core content + target channel + brand guidelines -> generate adapted text (captions, summaries, hooks).
    *   [ ] Integrate this into the publishing workflow for each channel.
*   [ ] **Scheduling Capability:**
    *   [ ] Add `scheduled_publish_time` fields to workflow status.
    *   [ ] Implement a scheduler mechanism (e.g., separate Python process using `APScheduler`, external cron job calling an API endpoint) to trigger publishing actions at scheduled times.

**Phase 5: Deeper LLM Integration & Automation**

*Goal: Move from LLM assistance to more automated content generation and workflow orchestration.*

*   [ ] **Content Idea Generation:**
    *   [ ] Integrate with external trends/monitoring tools (Phase 7?) or internal analytics (Phase 6).
    *   [ ] Use LLM to suggest blog post topics relevant to CLAN.com and current trends/events.
    *   [ ] Present suggestions in Admin UI.
*   [ ] **Draft Generation Pipeline:**
    *   [ ] Define workflow: Topic -> Outline (LLM) -> Draft Sections (LLM) -> Human Review/Edit -> Image Prompt Generation (LLM) -> Final Polish.
    *   [ ] Implement UI and backend logic to manage this pipeline, updating `workflow_status.json` at each step.
*   [ ] **Image Prompt Generation:** Use LLM based on post content/section context to suggest prompts for image generation (requires integration with an image generation model/API later or manual use).
*   [ ] **Brand Voice & Authenticity Check:**
    *   [ ] Develop LLM prompts/fine-tuning to ensure generated/adapted content matches CLAN.com's voice.
    *   [ ] Implement automated checks (e.g., LLM evaluates generated text against brand guidelines) flagging content for review.
*   [ ] **Automated Workflow Progression:** Based on configurable rules or LLM analysis, automatically advance workflow stages (e.g., mark writing 'complete' after review, trigger adaptation after blog publish). Requires careful design.

**Phase 6: Performance Monitoring & Analytics**

*Goal: Understand content effectiveness to inform strategy and LLM tuning.*

*   [ ] **Define Key Performance Indicators (KPIs):** E.g., Blog views, social media engagement (likes, shares, comments), referral traffic to CLAN.com, product page visits from content, conversions (requires e-commerce integration).
*   [ ] **Basic Engagement Tracking:** Store manually entered or estimated engagement metrics in `workflow_status.json` or a separate analytics store.
*   [ ] **Integrate Web Analytics:** Capture referral data from blog posts (e.g., UTM parameters) linking back to CLAN.com site analytics.
*   [ ] **Integrate Social Media Platform Analytics:**
    *   [ ] Regularly fetch basic engagement data (likes, comments, shares) via APIs for posts published by the system.
    *   [ ] Store aggregated data linked to the original content/workflow entry.
*   [ ] **Admin UI Analytics Dashboard:** Display key metrics per post, per channel, overall campaign performance.
*   [ ] **Feedback Loop:** Use performance data to refine content strategies and potentially provide feedback to LLM generation prompts (long-term goal).

**Phase 7: Advanced Modules & Future Expansion**

*Goal: Incorporate planned future modules, leveraging the established architecture.*

*   [ ] **Commenting & Interaction Module:**
    *   [ ] Strategy: Integrate with third-party services (Disqus?), platform-native comments (FB), or build a custom solution?
    *   [ ] Fetching/Displaying Comments: API integrations to pull comments related to syndicated posts. Display consolidated view in Admin UI.
    *   [ ] Responding: UI for drafting responses. *LLM opportunity for suggesting replies*. API integrations to post replies.
*   [ ] **Influencer Persona Module:**
    *   [ ] Define Persona Data Structure: Store characteristics, voice, target audience, goals for different brand personas (if needed).
    *   [ ] Integrate Personas into Content Generation: Use selected persona data to guide LLM prompts for tone and style.
    *   [ ] Track Content by Persona: Tag content generated under specific personas for performance analysis.
*   [ ] **Media Monitoring Module:**
    *   [ ] Integrate with Social Listening Tools (APIs): Monitor mentions of CLAN.com, key topics, competitors.
    *   [ ] Surface Relevant Mentions/Trends: Display in Admin UI.
    *   [ ] Rapid Response Workflow: Use monitoring insights to trigger content creation (e.g., reactive blog post, social media reply). *LLM opportunity for drafting responses*.
*   [ ] **Media Development (Video):**
    *   [ ] Strategy: Define types of video content (e.g., blog summaries, product highlights, heritage explainers).
    *   [ ] Script Generation: Use LLM to adapt blog content into video scripts.
    *   [ ] Asset Integration: Link video assets (source files, final renders) to content workflows.
    *   [ ] (Future) AI Video Generation: Integrate with tools that create video from text/images (highly speculative currently).
    *   [ ] Video Publishing: Extend syndication engine for video platforms (YouTube, TikTok, Instagram Reels).
*   [ ] **E-commerce Integration:** Deeper integration with CLAN.com product catalogue and sales data for direct performance tracking.

---

This revised plan provides a comprehensive roadmap. Each unchecked item represents a potential development task or area requiring further research and design. The modular approach and focus on data/APIs should allow for flexibility as priorities evolve and new technologies (especially in AI) emerge. Remember to constantly evaluate decisions against the core brand principles of CLAN.com.