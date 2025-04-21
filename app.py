from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import yaml
from datetime import datetime
import pytz
import re
import logging
import json
from pathlib import Path

# Import LLM modules
from scripts.llm import MetadataGenerator
from scripts.llm.config import load_config, save_config
from scripts.llm.base import LLMConfig, LLMResponse
from scripts.llm.factory import LLMFactory

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d %b %y : %H:%M'):
    if not value:
        return ''
    try:
        # Parse the input date string
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        # Convert to local timezone (you can change this to your preferred timezone)
        local_tz = pytz.timezone('Europe/London')
        local_dt = dt.astimezone(local_tz)
        # Format the date
        return local_dt.strftime(format)
    except (ValueError, AttributeError):
        return value

def load_posts():
    try:
        logger.debug("Loading posts from posts.yaml")
        with open('posts.yaml', 'r') as file:
            data = yaml.safe_load(file)
            logger.debug(f"Loaded posts: {data}")
            return data.get('posts', [])
    except FileNotFoundError:
        logger.debug("posts.yaml not found, returning empty list")
        return []
    except Exception as e:
        logger.error(f"Error loading posts: {str(e)}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def posts():
    posts_data = load_posts()
    return render_template('posts.html', posts=posts_data)

@app.route('/posts/<slug>')
def post_detail(slug):
    posts_data = load_posts()
    post = next((p for p in posts_data if p['slug'] == slug), None)
    if not post:
        return render_template('404.html'), 404
    
    # Ensure all required post attributes exist with default values
    post.setdefault('title', '')
    post.setdefault('subtitle', '')
    post.setdefault('concept', '')
    post.setdefault('summary', '')
    post.setdefault('sections', [])
    post.setdefault('conclusion', {'heading': '', 'text': ''})
    post.setdefault('meta_description', '')
    post.setdefault('meta_keywords', '')
    post.setdefault('categories', [])
    post.setdefault('tags', [])
    post.setdefault('author', '')
    post.setdefault('creation_date', '')
    post.setdefault('published_date', '')
    post.setdefault('modified_date', '')
    post.setdefault('header_image', None)
    post.setdefault('status', 'development')
    post.setdefault('clan_id', None)
    
    # Load workflow status
    workflow_status_path = Path('data/workflow_status.json')
    workflow_status = {}
    if workflow_status_path.exists():
        try:
            with open(workflow_status_path, 'r') as f:
                workflow_status = json.load(f)
        except Exception as e:
            logger.error(f"Error loading workflow status: {str(e)}")
    
    # Get post status or initialize with defaults
    post_status = workflow_status.get(slug, {'stages': {}})
    
    # Initialize missing stages with default values
    for stage in ['conceptualisation', 'authoring', 'metadata', 'images', 'checking', 'publishing']:
        if stage not in post_status['stages']:
            post_status['stages'][stage] = {'status': 'pending'}
            if stage == 'images':
                post_status['stages'][stage].update({
                    'prompts_defined_status': 'pending',
                    'assets_prepared_status': 'pending',
                    'metadata_integrated_status': 'pending'
                })

    # Load authors data
    try:
        authors_path = Path('_data/authors.json')
        if authors_path.exists():
            with open(authors_path, 'r', encoding='utf-8') as f:
                authors = json.load(f)
        else:
            authors = {}
            logger.warning("Authors file not found at: %s", authors_path)
    except Exception as e:
        logger.error(f"Error loading authors: {e}")
        authors = {}
    
    return render_template('post_detail.html', post=post, status=post_status, authors=authors)

@app.route('/posts/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        try:
            logger.debug(f"Received form data: {request.form}")
            
            # Get form data
            working_title = request.form.get('working_title', '').strip()
            author = request.form.get('author', '').strip()
            concept = request.form.get('concept', '').strip()
            
            logger.debug(f"Processed form data - Title: {working_title}, Author: {author}, Concept: {concept}")
            
            if not all([working_title, author, concept]):
                logger.warning("Missing required fields")
                return "Missing required fields", 400
            
            # Load existing posts
            posts_data = load_posts()
            logger.debug(f"Current posts data: {posts_data}")
            
            # Create new post with matching structure
            new_post = {
                'id': len(posts_data) + 1,
                'title': working_title,  # Using working_title as initial title
                'slug': generate_slug(working_title),
                'author': author,
                'categories': [],
                'concept': concept,
                'creation_date': datetime.now().strftime('%Y-%m-%d'),
                'modified_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'header_image': None,
                'status': 'development',
                'clan_id': None,
                'published_date': None,
                'tags': []
            }
            
            logger.debug(f"New post to be added: {new_post}")
            
            # Add new post to the list
            posts_data.append(new_post)
            
            # Save updated posts
            save_posts(posts_data)
            
            logger.debug("Post saved successfully, redirecting to posts list")
            
            # Redirect to posts list
            return redirect(url_for('posts'))
        except Exception as e:
            logger.error(f"Error creating new post: {str(e)}")
            return f"Error creating post: {str(e)}", 500
    
    return render_template('post_form.html')

def generate_slug(text):
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().replace(' ', '-')
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    return slug.strip('-')

def save_posts(posts):
    try:
        logger.debug(f"Saving posts: {posts}")
        # Create a temporary file first
        temp_file = 'posts.yaml.tmp'
        with open(temp_file, 'w') as file:
            yaml.dump({'posts': posts}, file, default_flow_style=False)
        
        # If successful, rename the temporary file to the actual file
        import os
        os.replace(temp_file, 'posts.yaml')
        logger.debug("Posts saved successfully")
    except Exception as e:
        logger.error(f"Error saving posts: {str(e)}")
        # Try to remove the temporary file if it exists
        try:
            os.remove(temp_file)
        except:
            pass
        raise

@app.route('/posts/<slug>/edit', methods=['GET'])
def edit_post(slug):
    posts_data = load_posts()
    post = next((p for p in posts_data if p['slug'] == slug), None)
    if not post:
        return render_template('404.html'), 404
    return render_template('post_form.html', post=post)

@app.route('/llms')
def llms():
    # Load current LLM configuration
    configs = load_config()
    default_config = configs.get("default", LLMConfig(
        provider_type="ollama",
        model_name="mistral",
        api_base="http://localhost:11434",
        api_key=None
    ))

    # Create a metadata generator instance
    generator = MetadataGenerator()
    
    # Extract prompt templates from the generator methods
    example_content = "Example blog post content about Scottish heritage."
    example_title = "Example Current Title"
    
    # Get the prompts by calling the methods but extracting just the prompt part
    title_response = generator.generate_title(example_content, example_title)
    meta_desc_response = generator.generate_meta_description(example_content)
    keywords_response = generator.generate_keywords(example_content)

    prompts = {
        "title_generation": title_response.prompt if hasattr(title_response, 'prompt') else "Title generation prompt not available",
        "meta_description": meta_desc_response.prompt if hasattr(meta_desc_response, 'prompt') else "Meta description prompt not available",
        "keywords": keywords_response.prompt if hasattr(keywords_response, 'prompt') else "Keywords prompt not available"
    }

    return render_template('llms.html', config=default_config, prompts=prompts)

@app.route('/preview')
def preview():
    return render_template('preview.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/llm/test', methods=['POST'])
def test_llm():
    """Test the LLM with a given prompt."""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
            
        # Load current configuration
        configs = load_config()
        config = configs.get("default", LLMConfig(
            provider_type="ollama",
            model_name="mistral",
            api_base="http://localhost:11434",
            api_key=None
        ))
        
        # Create provider and test
        provider = LLMFactory.create_provider(config)
        response = provider.generate_text(prompt)
        
        if response.error:
            return jsonify({"error": response.error}), 500
            
        return jsonify({"response": response.text})
        
    except Exception as e:
        logging.error(f"Error testing LLM: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<slug>/title', methods=['POST'])
def update_title(slug):
    """Update a post's title and optionally its slug."""
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({"success": False, "error": "Missing title in request body"}), 400

        new_title = data['title'].strip()
        if not new_title:
            return jsonify({"success": False, "error": "Title cannot be empty"}), 400

        # Load existing posts
        posts_data = load_posts()
        
        # Find the post
        post = next((p for p in posts_data if p['slug'] == slug), None)
        if not post:
            return jsonify({"success": False, "error": "Post not found"}), 404

        # Update the title
        post['title'] = new_title
        post['modified_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        # Update slug if requested and post is not published
        new_slug = slug
        if data.get('update_slug') and post['status'] != 'published':
            new_slug = generate_slug(new_title)
            # Check if the new slug is already in use
            if new_slug != slug and any(p['slug'] == new_slug for p in posts_data):
                return jsonify({"success": False, "error": "A post with this slug already exists"}), 400
            post['slug'] = new_slug

        # Save the updated posts
        save_posts(posts_data)

        return jsonify({
            "success": True,
            "message": "Title updated successfully",
            "title": new_title,
            "new_slug": new_slug
        })

    except Exception as e:
        logger.error(f"Error updating title: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/posts/<slug>/concept', methods=['POST'])
def update_concept(slug):
    """Update a post's concept."""
    try:
        data = request.get_json()
        if not data or 'concept' not in data:
            return jsonify({"success": False, "error": "Missing concept in request body"}), 400

        new_concept = data['concept'].strip()

        # Load existing posts
        posts_data = load_posts()
        
        # Find the post
        post = next((p for p in posts_data if p['slug'] == slug), None)
        if not post:
            return jsonify({"success": False, "error": "Post not found"}), 404

        # Update the concept
        post['concept'] = new_concept
        post['modified_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        # Save the updated posts
        save_posts(posts_data)

        return jsonify({
            "success": True,
            "message": "Concept updated successfully",
            "concept": new_concept
        })

    except Exception as e:
        logger.error(f"Error updating concept: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/posts/<slug>/author', methods=['POST'])
def update_author(slug):
    """Update a post's author."""
    try:
        data = request.get_json()
        if not data or 'author' not in data:
            return jsonify({"success": False, "error": "Missing author in request body"}), 400

        new_author = data['author'].strip()

        # Load existing posts
        posts_data = load_posts()
        
        # Find the post
        post = next((p for p in posts_data if p['slug'] == slug), None)
        if not post:
            return jsonify({"success": False, "error": "Post not found"}), 404

        # Update the author
        post['author'] = new_author
        post['modified_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        # Save the updated posts
        save_posts(posts_data)

        return jsonify({
            "success": True,
            "message": "Author updated successfully",
            "author": new_author
        })

    except Exception as e:
        logger.error(f"Error updating author: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

def load_llm_tasks():
    """Load LLM task configurations from YAML file."""
    tasks_path = Path('_data/llm_tasks.yaml')
    try:
        if tasks_path.exists():
            with open(tasks_path, 'r') as f:
                return yaml.safe_load(f)
        return {'tasks': {}}
    except Exception as e:
        logger.error(f"Error loading LLM tasks: {e}")
        return {'tasks': {}}

@app.route('/api/posts/<slug>/generate_concept', methods=['POST'])
def generate_concept(slug):
    """Generate a concept for a post using the LLM."""
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({"success": False, "error": "Missing title in request body"}), 400

        # Load LLM task configuration
        llm_tasks = load_llm_tasks()
        task_config = llm_tasks['tasks'].get('generate_concept')
        if not task_config:
            return jsonify({"success": False, "error": "LLM task configuration not found"}), 500

        # Format the prompt with the title
        prompt = task_config['prompt'].format(title=data['title'])

        # Load LLM configuration
        configs = load_config()
        config = configs.get("default", LLMConfig(
            provider_type="ollama",
            model_name="mistral",
            api_base="http://localhost:11434",
            api_key=None
        ))

        # Create provider and generate
        provider = LLMFactory.create_provider(config)
        response = provider.generate_text(
            prompt,
            temperature=task_config['model_settings']['temperature'],
            max_tokens=task_config['model_settings']['max_tokens'],
            top_p=task_config['model_settings']['top_p']
        )

        if response.error:
            return jsonify({"success": False, "error": response.error}), 500

        # Load existing posts
        posts_data = load_posts()
        
        # Find the post
        post = next((p for p in posts_data if p['slug'] == slug), None)
        if not post:
            return jsonify({"success": False, "error": "Post not found"}), 404

        # Update the concept
        post['concept'] = response.text.strip()
        post['modified_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        # Save the updated posts
        save_posts(posts_data)

        return jsonify({
            "success": True,
            "concept": post['concept']
        })

    except Exception as e:
        logger.error(f"Error generating concept: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)