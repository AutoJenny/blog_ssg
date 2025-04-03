# Technical Implementation Plan: Blog Post Syndication MVP (Instagram & Facebook)

**Goal:** Create a local Python script that reads metadata about blog post images from a central JSON file, identifies images pending publication, and posts them with appropriate captions and hashtags to specified Instagram Business/Creator accounts and Facebook Pages via their respective APIs.

**Scope (MVP):**

* Target Platforms: Instagram (single image feed posts), Facebook Page (single image posts).
* Trigger: Manual execution of the local Python script.
* Data Source: Local JSON file (`_data/syndication.json`).
* Image Source: Assumes images will eventually have publicly accessible URLs (placeholders used initially for testing).
* Functionality: Post pending images, update status in JSON upon success/failure.
* Content: Platform-specific captions and hashtags loaded from JSON.

---

## Phase 1: Setup & Data Definition

* [X] **1.1. Python Environment:**
  * Ensure Python 3 is installed and accessible (`python3 --version`).
  * Consider setting up a virtual environment (optional but recommended):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate # Linux/macOS
    # or .\.venv\Scripts\activate # Windows
    ```
* [X] **1.2. Install Dependencies:**
  ```bash
  pip install requests python-dotenv Pillow # Pillow might be useful later for validation/local testing
  ```
* [X] **1.3. Define Data Structure (`_data/syndication.json`):**
  * Create the `_data` directory if it doesn't exist.
  * Create `_data/syndication.json`.
  * Define the JSON structure (example below, adjust as needed):
    ```json
    {
      "POST_SLUG": { // e.g., "kilt-evolution"
        "IMAGE_KEY": { // e.g., "header", "early-highland-dress"
          "source_path_local": "/images/kilt-evolution/kilt-evolution-header.jpg", // Relative local path
          "source_url_public": null, // Placeholder for public URL needed by API
          "alt": "Descriptive alt text...",
          "blog_caption": "Caption used on the blog...",
          "prompt": "LLM prompt used for generation...", // Optional
          "syndication": {
            "instagram": {
              "status": "pending", // pending | published | error | skipped
              "post_id": null, // ID returned by API on success
              "last_attempt": null, // ISO 8601 timestamp
              "error_message": null,
              "caption": "Platform-specific caption for Instagram. #hashtags",
              "hashtags": ["list", "of", "hashtags"] // Store separately if preferred
            },
            "facebook": {
              "status": "pending",
              "post_id": null,
              "last_attempt": null,
              "error_message": null,
              "caption": "Platform-specific caption/text for Facebook Page."
            }
          }
        }
        // ... more images for this post ...
      }
      // ... more posts ...
    }
    ```
* [X] **1.4. Populate Initial Data:**
  * Manually fill `_data/syndication.json` with entries for the images from the `kilt-evolution` post. Leave `source_url_public` as `null` for now. Draft initial Instagram/Facebook captions and hashtags.
* [X] **1.5. Configuration (`.env` file):**
  * Create a file named `.env` in the project root.
  * **Add `.env` to your `.gitignore` file** to avoid committing secrets.
  * Define placeholder variables needed for API access (we'll get the real values in Phase 2):
    ```dotenv
    # .env file
    META_APP_ID=YOUR_APP_ID
    META_APP_SECRET=YOUR_APP_SECRET
    META_ACCESS_TOKEN=YOUR_LONG_LIVED_USER_OR_PAGE_ACCESS_TOKEN
    FB_PAGE_ID=YOUR_FACEBOOK_PAGE_ID
    IG_BUSINESS_ACCOUNT_ID=YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID
    ```

---

## Phase 2: API Credentials & Setup (Meta/Facebook/Instagram)

* **Note:** This phase involves interacting with the Meta Developer platform and can be complex. Refer to official documentation frequently.

* [ ] **2.1. Meta Developer Account & App:**
  * Register as a Meta Developer at [developers.facebook.com](https://developers.facebook.com/).
  * Create a new Meta App (Type: Business).
* [ ] **2.2. Connect Facebook Page & Instagram Account:**
  * Ensure you have an Instagram Business or Creator account.
  * Ensure this Instagram account is correctly linked to a Facebook Page that you manage.
* [ ] **2.3. Configure App Permissions:**
  * In the Meta App Dashboard, add the "Instagram Graph API" and "Facebook Login" (even for app tokens) products.
  * Request/Add the necessary permissions:
    * `pages_show_list` (to find Page ID)
    * `pages_read_engagement` (needed by IG)
    * `instagram_basic` (to get IG Account ID)
    * `instagram_content_publish` (to post to IG)
    * (Optional for FB Page posting if needed: `pages_manage_posts`)
* [ ] **2.4. Obtain IDs:**
  * Find your Facebook Page ID (often visible in Page settings or via Graph API Explorer `me/accounts`).
  * Use the Graph API Explorer (`GET me/accounts?fields=instagram_business_account{id}`) with a User Token that has `instagram_basic` and `pages_show_list` permissions to find your Instagram Business Account ID linked to your Page.
* [ ] **2.5. Obtain Access Token:**
  * Use the Graph API Explorer to generate a **User Access Token** with *all* the required permissions from step 2.3.
  * **Crucially:** Extend this short-lived User Token into a **Long-Lived User Access Token** (lasts ~60 days). Document the expiry. (For true automation, a System User or server-side Page Token flow is needed later, but a long-lived User token is sufficient for initial local scripting).
  * *(Alternative for FB Page posting only: Obtain a Page Access Token directly if possible/needed)*.
* [ ] **2.6. Populate `.env`:**
  * Fill in the actual values obtained in steps 2.1, 2.4, and 2.5 into your `.env` file.

---

## Phase 3: Script Development (`syndicate.py`)

* [ ] **3.1. Create Script File:** Create `syndicate.py` in the project root.
* [ ] **3.2. Boilerplate & Config Loading:**
  * Add necessary imports (`os`, `json`, `requests`, `datetime`, `dotenv`).
  * Use `dotenv.load_dotenv()` to load variables from `.env`.
  * Define constants for API base URLs (e.g., `https://graph.facebook.com/v18.0`).
* [ ] **3.3. Load Syndication Data:**
  * Write function to load `_data/syndication.json` into a Python dictionary. Handle potential `FileNotFoundError`.
* [ ] **3.4. Save Syndication Data:**
  * Write function to save the (updated) Python dictionary back to `_data/syndication.json`.
* [ ] **3.5. Core Logic - Identify Pending Posts:**
  * Implement logic to iterate through the loaded data.
  * Identify images where `syndication.instagram.status == "pending"` or `syndication.facebook.status == "pending"`.
  * **Crucially:** Skip items where `source_url_public` is still `null`. Print a warning.
* [ ] **3.6. Instagram Posting Function (MVP):**
  * **3.6.1. Hashtag Research:** Perform research using online tools, competitor analysis, and platform search to identify relevant, effective hashtags for the kilt/quaich posts. Consider a mix of high-volume, medium, and niche tags. Update the `hashtags` field in the JSON data.
  * **3.6.2. Create Media Container:** Implement API call (`POST /{ig-user-id}/media`) with `image_url` and `caption` (including hashtags from JSON). Handle API response, check for errors. Extract the returned container `id`.
  * **3.6.3. Publish Media Container:** Implement API call (`POST /{ig-user-id}/media_publish`) with `creation_id` (the container ID from the previous step). Handle API response. Extract the final media (post) `id` on success.
  * **3.6.4. Error Handling:** Basic try/except blocks around API calls. Log errors.
* [ ] **3.7. Facebook Page Posting Function (MVP):**
  * **3.7.1. API Call:** Implement API call (`POST /{page-id}/photos`) with `url` (public image URL) and `caption` (message/text from JSON). Handle API response. Extract `post_id` on success.
  * **3.7.2. Error Handling:** Basic try/except blocks. Log errors.
* [ ] **3.8. Update State Logic:**
  * After attempting a post for a platform:
    * If successful: Update the corresponding platform's `status` to "published", store the `post_id`, update `last_attempt` timestamp.
    * If failed: Update `status` to "error", store the `error_message`, update `last_attempt`.
* [ ] **3.9. Main Script Flow:**
  * Load config & data.
  * Loop through pending items.
  * Call Instagram function if needed. Update state.
  * Call Facebook function if needed. Update state.
  * Save updated data back to JSON file at the end.
  * Add print statements for logging progress.

---

## Phase 4: Local Testing

* [ ] **4.1. Prepare Test Data:**
  * Ensure `_data/syndication.json` has entries for testing.
  * **Temporarily** fill in `source_url_public` for 1-2 test images using known public URLs (e.g., from Wikimedia Commons, Unsplash, or even a GitHub raw link if the repo is public).
* [ ] **4.2. Execute Script:**
  * Run `python3 syndicate.py` locally from the project root.
* [ ] **4.3. Verify Posts:**
  * Check your Instagram account and Facebook Page to see if the test images were posted correctly with captions/hashtags.
* [ ] **4.4. Verify JSON Update:**
  * Check `_data/syndication.json` to confirm the `status`, `post_id`, `last_attempt`, and `error_message` fields were updated as expected.
* [ ] **4.5. Test Error Cases (Optional):** Temporarily use an invalid token or bad image URL to ensure error status is recorded correctly.

---

## Phase 5: Future Enhancements (Post-MVP)

* [ ] **Error Handling:** Implement retry logic for transient API errors. More detailed error reporting/logging.
* [ ] **Token Management:** Implement a more robust solution for Access Tokens (auto-refresh, System Users if running server-side).
* [ ] **Content Types:** Support video posts, Instagram Carousels/Reels/Stories.
* [ ] **Instagram Hashtags:** Option to post hashtags as the first comment instead of in the caption.
* [ ] **Scheduling/Automation:** Use `cron` (Linux/macOS), Task Scheduler (Windows), or cloud services (GitHub Actions, AWS Lambda) to run the script automatically.
* [ ] **User Interface:** Develop a CLI or web interface to manage syndication status and trigger posts.

* **Public URL Strategy:** Integrate with the blog deployment process to automatically populate `source_url_public` in the JSON file once the site (and images) are live.

* [ ] **Refactoring:** Improve script structure (e.g., classes, helper functions).
* [ ] **Platform Refinements:** Add location tagging, user tagging, etc.

---
