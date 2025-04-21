# Migration Plan: Eleventy+Flask to Flask-only

## Current Issues
1. Template conflicts between Eleventy and Flask
2. Image path mismatches causing 404s
3. Complex data flow between static and dynamic content
4. Duplicate template logic
5. Inconsistent URL structures

## Migration Strategy

### Phase 1: Setup and Structure (1-2 hours)
1. Create new Flask routes for public pages:
   ```python
   @app.route('/')                      # Blog listing
   @app.route('/post/<slug>')           # Individual post
   @app.route('/tag/<tag>')             # Tag listing
   @app.route('/author/<author>')       # Author listing
   ```

2. Create unified template structure:
   ```
   /templates/
   ├── base.html                    # Single base template
   ├── public/
   │   ├── index.html              # Blog listing
   │   ├── post.html              # Individual post
   │   ├── tag.html              # Tag listing
   │   └── author.html           # Author listing
   └── admin/                    # (existing admin templates)
       ├── base.html
       ├── index.html
       └── post_detail.html
   ```

### Phase 2: Data Management (2-3 hours)
1. Create Post class for unified data handling:
   ```python
   class Post:
       def __init__(self, slug, content, metadata)
       @staticmethod
       def from_file(file_path)
       def to_html(self)
       def get_preview(self, length=200)
   ```

2. Create PostManager class:
   ```python
   class PostManager:
       def get_all_posts()
       def get_post(slug)
       def get_posts_by_tag(tag)
       def get_posts_by_author(author)
   ```

3. Move all data handling to Flask:
   - Convert Eleventy data files to Python
   - Implement caching for performance
   - Create unified image handling

### Phase 3: Template Migration (2-3 hours)
1. Convert Nunjucks templates to Jinja2:
   - Move layouts to Flask template inheritance
   - Convert filters and helpers
   - Update image paths and static assets

2. Implement Flask template filters:
   ```python
   @app.template_filter('format_date')
   @app.template_filter('markdown')
   @app.template_filter('truncate_html')
   ```

### Phase 4: Image and Asset Handling (1-2 hours)
1. Create unified image serving:
   ```python
   @app.route('/images/<path:filename>')
   def serve_image(filename):
       return send_from_directory(IMAGES_DIR, filename)
   ```

2. Update image processing pipeline:
   - Move watermarking to Flask
   - Implement image optimization
   - Fix path handling

### Phase 5: Testing and Cleanup (2-3 hours)
1. Test all routes and functionality:
   - Post listing and pagination
   - Individual posts
   - Image serving
   - Admin interface
   - Post creation/editing
   - Image upload/processing

2. Remove Eleventy:
   - Remove Eleventy config and dependencies
   - Clean up unused files
   - Update documentation

## Implementation Order

1. Start with Phase 1 to establish new structure
2. Move to Phase 2 to ensure data handling
3. Implement Phase 3 for templates
4. Add Phase 4 for assets
5. Complete with Phase 5 for testing

## Success Criteria
1. All current functionality works in Flask
2. No 404 errors for images
3. Simplified template structure
4. Single source of truth for data
5. Improved performance
6. No dependency on Eleventy

## Rollback Plan
1. Keep Eleventy files until full testing
2. Maintain backup of working state
3. Document all changes for potential rollback

## Timeline
Total estimated time: 8-13 hours
Recommended approach: Phase by phase with testing between each phase 