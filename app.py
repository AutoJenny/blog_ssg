from flask import Flask, render_template
import os
import yaml
from datetime import datetime
import pytz

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
    with open('posts.yaml', 'r') as file:
        data = yaml.safe_load(file)
        return data.get('posts', [])

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
    return render_template('post_detail.html', post=post)

@app.route('/llms')
def llms():
    return render_template('llms.html')

@app.route('/preview')
def preview():
    return render_template('preview.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)