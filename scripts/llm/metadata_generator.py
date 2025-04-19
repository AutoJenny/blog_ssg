from typing import Dict, Any, Optional
from .base import LLMProvider, LLMResponse
from .factory import LLMFactory
from .config import load_config

class MetadataGenerator:
    """Generates metadata for blog posts using LLM."""
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        """Initialize with optional provider, otherwise uses default config."""
        if provider:
            self.provider = provider
        else:
            configs = load_config()
            self.provider = LLMFactory.create_provider(configs["default"])
    
    def _validate_length(self, text: str, max_length: int, field_name: str) -> str:
        """Ensure text meets length requirements."""
        if len(text) > max_length:
            return text[:max_length]
        return text
    
    def generate_title(self, content: str, current_title: Optional[str] = None) -> LLMResponse:
        """Generate a catchy title for the blog post."""
        prompt = f"""Given the following blog post content, generate a catchy, SEO-friendly title 
        that accurately represents the content while being engaging for readers.
        
        Current title: {current_title if current_title else 'None'}
        
        Content:
        {content[:2000]}  # Using first 2000 chars for context
        
        Requirements:
        - Title should be clear and descriptive
        - Include relevant keywords for SEO
        - Be engaging and encourage clicks
        - MUST be 60 characters or less
        - Don't use clickbait tactics
        - Focus on Scottish/Celtic heritage themes
        
        Respond with only the title, no explanation."""
        
        response = self.provider.generate_text(prompt)
        if not response.error:
            response.text = self._validate_length(response.text.strip(), 60, "title")
        response.prompt = prompt
        return response
    
    def generate_meta_description(self, content: str) -> LLMResponse:
        """Generate SEO meta description."""
        prompt = f"""Create a compelling meta description for the following blog post content.
        
        Content:
        {content[:2000]}
        
        Requirements:
        - MUST be between 150-160 characters
        - Include primary keywords naturally
        - Accurately summarize content
        - Be engaging and encourage clicks
        - Use active voice
        - Include a call to action if appropriate
        - Focus on Scottish/Celtic heritage value
        
        Respond with only the meta description, no explanation."""
        
        response = self.provider.generate_text(prompt)
        if not response.error:
            response.text = self._validate_length(response.text.strip(), 160, "meta_description")
        response.prompt = prompt
        return response
    
    def generate_keywords(self, content: str) -> LLMResponse:
        """Generate SEO keywords/tags."""
        prompt = f"""Extract relevant keywords and tags from the following blog post content.
        
        Content:
        {content[:2000]}
        
        Requirements:
        - Include both broad and specific keywords
        - Focus on relevant Scottish/Celtic heritage terms
        - Include location-based keywords if relevant
        - Maximum 10 keywords/tags
        - Order by relevance
        - Format as comma-separated list
        - Include variations of important terms
        - Consider seasonal/event relevance
        
        Respond with only the keywords as a comma-separated list, no explanation."""
        
        response = self.provider.generate_text(prompt)
        if not response.error:
            # Ensure proper comma separation and limit to 10 keywords
            keywords = [k.strip() for k in response.text.split(',')][:10]
            response.text = ', '.join(keywords)
        response.prompt = prompt
        return response
    
    def generate_subtitle(self, content: str, title: str) -> LLMResponse:
        """Generate an engaging subtitle."""
        prompt = f"""Create an engaging subtitle for the following blog post.
        
        Title: {title}
        
        Content:
        {content[:2000]}
        
        Requirements:
        - Complement the title without repeating it
        - Provide additional context
        - MUST be 100 characters or less
        - Use engaging language
        - Include secondary keywords if natural
        - Focus on Scottish/Celtic heritage value
        - Add emotional or practical appeal
        
        Respond with only the subtitle, no explanation."""
        
        response = self.provider.generate_text(prompt)
        if not response.error:
            response.text = self._validate_length(response.text.strip(), 100, "subtitle")
        response.prompt = prompt
        return response
    
    def generate_all_metadata(self, content: str, current_title: Optional[str] = None) -> Dict[str, str]:
        """Generate all metadata fields in one call."""
        title = self.generate_title(content, current_title)
        if title.error:
            return {"error": f"Failed to generate title: {title.error}"}
            
        metadata = {
            "title": title.text.strip(),
            "subtitle": self.generate_subtitle(content, title.text).text.strip(),
            "meta_description": self.generate_meta_description(content).text.strip(),
            "keywords": self.generate_keywords(content).text.strip()
        }
        
        # Final validation of all fields
        try:
            if len(metadata["title"]) > 60:
                metadata["title"] = metadata["title"][:60]
            if len(metadata["subtitle"]) > 100:
                metadata["subtitle"] = metadata["subtitle"][:100]
            if len(metadata["meta_description"]) > 160:
                metadata["meta_description"] = metadata["meta_description"][:160]
            if not metadata["keywords"]:
                metadata["keywords"] = "scottish, celtic"  # Default fallback
        except Exception as e:
            return {"error": f"Error validating metadata: {str(e)}"}
        
        return metadata 