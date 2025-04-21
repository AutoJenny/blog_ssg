from flask import Flask, render_template
import os
import yaml
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
app.config['TEMPLATES_AUTO_RELOAD'] = True

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