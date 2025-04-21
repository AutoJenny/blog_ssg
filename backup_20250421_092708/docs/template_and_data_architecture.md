# Template and Data Architecture

## Template Structure

### Static Site (Eleventy/Nunjucks)
- Location: `/templates/`
- Base template: `base.html`
- Post templates: `post.html`
- Purpose: Generates the static blog content

### Admin Interface (Flask/Jinja2)
- Location: `/templates/admin/`
- Base template: `_includes/admin/base.html`
- Admin templates:
  - `index.html`: Post listing
  - `post_detail.html`: Individual post management
- Purpose: Provides the admin interface for managing posts

## Data Flow

### Static Data (Eleventy)
1. Post Content
   - Source: `/posts/*.md`
   - Format: Markdown with YAML frontmatter
   - Usage: Generates blog post pages

2. Global Data
   - Source: `/_data/`
   - Files:
     - `workflow_status.json`: Post workflow stages
     - `image_library.json`: Image metadata and paths
   - Usage: Available to templates via Eleventy data cascade

### Dynamic Data (Flask)
1. Post Management
   - Source: Same files as static data
   - Access: Read/write via Flask routes
   - Updates: Through admin API endpoints

2. UI State
   - Hidden posts toggle: Stored in browser localStorage
   - Draft visibility: Controlled by admin interface

## Implementation Notes

### Post Visibility
1. Hidden posts are controlled by:
   - Frontend: JavaScript toggle in admin interface
   - Backend: Workflow status in `workflow_status.json`
   - Display: CSS classes for showing/hiding based on status

### Content Truncation
1. Blurb/concept fields should be truncated:
   - In templates using Nunjucks/Jinja2 filters
   - Character limit defined in template
   - Ellipsis added when truncated

### Template Inheritance Chain
1. Admin Interface:
   ```
   base.html (Flask)
   └── admin/base.html
       ├── admin/index.html
       └── admin/post_detail.html
   ```

2. Static Site:
   ```
   base.html (Eleventy)
   └── post.html
   ```

## Common Issues

1. Template Not Found
   - Ensure templates are in correct directories
   - Check template inheritance paths
   - Verify Jinja2/Nunjucks loader paths

2. Data Access
   - Flask and Eleventy need separate data loading logic
   - Changes in one system need to be reflected in the other
   - Use consistent data structure between systems 