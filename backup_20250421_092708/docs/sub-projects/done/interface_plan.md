# Implementation Plan: Rudimentary Blog Workflow Interface (Flask MVP)

**Goal:** Create a simple, local web interface using Flask to list blog posts, display their status, trigger the existing `post_to_clan.py` script, and show the script's output.

---

## Phase 1: Basic Setup

* [X] **1.1. Install Flask:**
  ```bash
  pip install Flask python-dotenv requests python-frontmatter beautifulsoup4 lxml # Ensure all needed deps are listed
  # Add Flask to requirements.txt
  ```
* [X] **1.2. Create Project Structure:**
  * Create `app.py` in the project root.
  * Create `templates/` directory in the project root.
  * Create `templates/admin_index.html` file.
* [X] **1.3. Basic Flask App (`app.py`):**
  * Import `Flask`, `render_template`.
  * Initialize Flask app: `app = Flask(__name__)`.
  * Create basic index route (`@app.route('/')`) that renders `admin_index.html`.
  * Add `if __name__ == '__main__': app.run(debug=True)` block.
* [X] **1.4. Basic Template (`templates/admin_index.html`):**
  * Create basic HTML boilerplate (head, body).
  * Add a title: `<h1>Blog Workflow Manager</h1>`.
  * Add placeholders for Post List and Log Output.
* [X] **1.5. Run & Test:**
  * Run `python3 app.py`.
  * Visit `http://127.0.0.1:5000` (or the URL Flask provides) in browser.
  * Verify the basic page loads with the title.

---

## Phase 2: Display Post List & Status

* [ ] **2.1. Load Data in Flask (`app.py`):**
  * In the index route (`/`), add logic to:
    * Import `os`, `json`, `pathlib`.
    * Define paths to `posts/` directory and `_data/syndication.json`.
    * Use `os.listdir('posts')` to find `.md` files and extract slugs.
    * Call `load_syndication_data` (reuse/import function from `post_to_clan.py` or duplicate it) to load status info.
    * Create a list of dictionaries, each containing `slug`, `title` (requires parsing front matter - use `python-frontmatter`), `clan_com_status`, etc.
  * Pass this `posts_data` list to `render_template('admin_index.html', posts=posts_data)`.
* [ ] **2.2. Display List in Template (`templates/admin_index.html`):**
  * Use Jinja2 `{% for post in posts %}` loop to iterate through the passed data.
  * Display `post.title`, `post.slug`.
  * Display `post.clan_com_status` (format nicely, e.g., show ID if present).
  * Add a placeholder button "Publish/Update Clan.com" for each post, including the `post.slug` in a data attribute (e.g., `data-slug="{{ post.slug }}"`).
  * Add a `<pre id="log-output"></pre>` area for logs.
* [ ] **2.3. Test:** Run Flask app, verify post list and status display correctly.

---

## Phase 3: Trigger `post_to_clan.py` Action

* [X] **3.1. Create Flask API Endpoint (`app.py`):**
  * Import `subprocess`, `jsonify`.
  * Define a new route like `@app.route('/api/publish_clan/<string:slug>', methods=['POST'])`.
  * Inside the route function:
    * Construct the path to the target markdown file: `posts/<slug>.md`.
    * Construct the command: `['python3', 'post_to_clan.py', 'posts/<slug>.md']`
    * Use `subprocess.run(command, capture_output=True, text=True, check=False)` (use `check=False` initially to handle script errors).
    * Capture `result.stdout` and `result.stderr`.
    * Determine success based on `result.returncode`.
    * (Optional: Reload `syndication.json` to get updated status).
    * Return a JSON response: `return jsonify({"success": success, "output": result.stdout + "\n" + result.stderr, "slug": slug})`. Handle potential errors during subprocess call.
* [X] **3.2. Add JavaScript to Template (`templates/admin_index.html`):**
  * Add a `<script>` block at the bottom.
  * Add an event listener (e.g., using `document.addEventListener('click', ...)` and checking `event.target.matches('.publish-clan-button')`).
  * When a button is clicked:
    * Get the `slug` from the button's `data-slug` attribute.
    * Get the log output element (`document.getElementById('log-output')`).
    * Display "Starting job for [slug]..." in the log area.
    * Use `fetch('/api/publish_clan/' + slug, { method: 'POST' })`.
    * Use `.then(response => response.json())` to parse the JSON result.
    * Use `.then(data => { ... })` to handle the result:
      * Display `data.output` in the log area.
      * Optionally update the status display for that post row (more complex, maybe defer).
    * Add `.catch(error => { ... })` to display fetch/network errors.
* [X] **3.3. Test:** Run Flask app. Click the "Publish/Update" button for a post. Verify the script runs (check terminal where Flask is running for logs from `post_to_clan.py`), and verify the output appears in the web interface log area. Check if `syndication.json` gets updated with the Post ID if it was a creation.

---

## Phase 4: Documentation Links

* [ ] **4.1. Add Links in Template (`templates/admin_index.html`):**
  * Add small `<a>` tags next to relevant sections or buttons.
  * Set `href` attribute to point to specific anchor links within your `README.md` file (e.g., `href="README.md#publishing-to-clancom" target="_blank"`). You'll need to add corresponding anchors (`<a name="publishing-to-clancom"></a>` or rely on Markdown heading IDs) in your `README.md`.
* [ ] **4.2. Test:** Verify links open the README file correctly (or to the specific section if the browser supports fragment navigation for local files well).

---
