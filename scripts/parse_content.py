import re
import os
import sys
from bs4 import BeautifulSoup
import markdown
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_html(content):
    """Parse HTML content and extract sections."""
    soup = BeautifulSoup(content, 'html.parser')
    
    # Extract summary (first paragraph)
    summary = None
    first_p = soup.find('p')
    if first_p:
        summary = first_p.get_text().strip()
    
    # Extract sections
    sections = []
    current_section = None
    
    for element in soup.find_all(['h2', 'p']):
        if element.name == 'h2':
            if current_section:
                sections.append(current_section)
            current_section = {
                'heading': element.get_text().strip(),
                'text': ''
            }
        elif element.name == 'p' and current_section:
            if current_section['text']:
                current_section['text'] += '\n\n'
            current_section['text'] += element.get_text().strip()
    
    if current_section:
        sections.append(current_section)
    
    # Extract conclusion (last section)
    conclusion = None
    if sections:
        last_section = sections.pop()
        conclusion = {
            'heading': last_section['heading'],
            'text': last_section['text']
        }
    
    return {
        'summary': summary,
        'sections': sections,
        'conclusion': conclusion
    }

def parse_markdown(content):
    """Parse Markdown content and extract sections."""
    # Convert markdown to HTML first
    html = markdown.markdown(content)
    return parse_html(html)

def parse_file(file_path):
    """Parse a content file based on its extension."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        _, ext = os.path.splitext(file_path)
        if ext.lower() in ['.html', '.htm']:
            return parse_html(content)
        elif ext.lower() in ['.md', '.markdown']:
            return parse_markdown(content)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parse_content.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        result = parse_file(file_path)
        print(result)
    except Exception as e:
        logger.error(f"Failed to parse file: {str(e)}")
        sys.exit(1) 