import re
import os
import sys
from bs4 import BeautifulSoup
import markdown
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_html(content):
    """Parse HTML content and extract sections, summary, and conclusion."""
    try:
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract summary (first paragraph, preserving HTML)
        summary = str(soup.find('p')) if soup.find('p') else ""
        
        # Extract concept (from meta tag or first h2)
        concept = ""
        meta_concept = soup.find('meta', attrs={'name': 'concept'})
        if meta_concept:
            concept = meta_concept.get('content', '')
        else:
            first_h2 = soup.find('h2')
            if first_h2 and first_h2.get_text().lower().startswith('concept'):
                concept = str(first_h2.find_next('p')) if first_h2.find_next('p') else ""
        
        # Extract sections
        sections = []
        for h2 in soup.find_all('h2'):
            # Skip sections with headings that are 'concept', 'summary', or 'conclusion'
            if h2.get_text().lower() not in ['concept', 'summary', 'conclusion']:
                # Get all content until the next h2, preserving HTML
                section_content = []
                next_element = h2.find_next_sibling()
                while next_element and next_element.name != 'h2':
                    section_content.append(str(next_element))
                    next_element = next_element.find_next_sibling()
                
                section = {
                    'heading': h2.get_text(),
                    'text': '\n'.join(section_content)
                }
                sections.append(section)
        
        # Extract conclusion
        conclusion_h2 = soup.find('h2', text=lambda t: t and t.lower() == 'conclusion')
        conclusion_content = []
        if conclusion_h2:
            next_element = conclusion_h2.find_next_sibling()
            while next_element:
                conclusion_content.append(str(next_element))
                next_element = next_element.find_next_sibling()
        
        conclusion = {
            'heading': 'Conclusion',
            'text': '\n'.join(conclusion_content)
        }
        
        return {
            'concept': concept,
            'summary': summary,
            'sections': sections,
            'conclusion': conclusion
        }
    except Exception as e:
        logger.error(f"Error parsing HTML content: {str(e)}", exc_info=True)
        raise

def parse_markdown(content):
    """Parse Markdown content and extract sections, summary, and conclusion."""
    try:
        # Convert markdown to HTML with extensions for better formatting
        html_content = markdown.markdown(content, extensions=['extra'])
        
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract summary (first paragraph, preserving HTML)
        summary = str(soup.find('p')) if soup.find('p') else ""
        
        # Extract sections
        sections = []
        for h2 in soup.find_all('h2'):
            if h2.get_text().lower() not in ['concept', 'conclusion']:
                # Get all content until the next h2, preserving HTML
                section_content = []
                next_element = h2.find_next_sibling()
                while next_element and next_element.name != 'h2':
                    section_content.append(str(next_element))
                    next_element = next_element.find_next_sibling()
                
                section = {
                    'heading': h2.get_text(),
                    'text': '\n'.join(section_content)
                }
                sections.append(section)
        
        # Extract conclusion
        conclusion_h2 = soup.find('h2', text=lambda t: t and t.lower() == 'conclusion')
        conclusion_content = []
        if conclusion_h2:
            next_element = conclusion_h2.find_next_sibling()
            while next_element:
                conclusion_content.append(str(next_element))
                next_element = next_element.find_next_sibling()
        
        conclusion = {
            'heading': 'Conclusion',
            'text': '\n'.join(conclusion_content)
        }
        
        return {
            'summary': summary,
            'sections': sections,
            'conclusion': conclusion
        }
    except Exception as e:
        logger.error(f"Error parsing Markdown content: {str(e)}", exc_info=True)
        raise

def parse_file(file_path):
    """Parse a content file (HTML or Markdown) and extract sections, summary, and conclusion."""
    try:
        logger.info(f"Attempting to parse file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine file type
        if file_path.endswith('.html'):
            logger.info("Parsing HTML file")
            return parse_html(content)
        elif file_path.endswith('.md'):
            logger.info("Parsing Markdown file")
            return parse_markdown(content)
        else:
            raise ValueError("Unsupported file format. Please provide HTML or Markdown.")
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {str(e)}", exc_info=True)
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
        logger.error(f"Failed to parse file: {str(e)}", exc_info=True)
        sys.exit(1) 