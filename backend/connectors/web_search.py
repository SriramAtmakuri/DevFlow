import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

class WebSearcher:
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.brave_url = "https://api.search.brave.com/res/v1/web/search"
    
    def search(self, query: str, count: int = 3) -> List[Dict[str, Any]]:
        """Search the web using Brave Search API"""
        if not self.brave_api_key:
            raise ValueError("BRAVE_API_KEY not set")
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key
        }
        
        params = {
            "q": query,
            "count": count
        }
        
        try:
            response = requests.get(self.brave_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("web", {}).get("results", [])[:count]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", "")
                })
            
            return results
        except Exception as e:
            print(f"Brave Search error: {e}")
            return []
    
    def scrape_content(self, url: str, max_length: int = 5000) -> str:
        """Scrape and extract main content from a URL"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)
            
            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
        except Exception as e:
            print(f"Scraping error for {url}: {e}")
            return ""
    
    def search_and_scrape(self, query: str, count: int = 3) -> List[Dict[str, Any]]:
        """Search web and scrape content from top results"""
        search_results = self.search(query, count)
        
        enriched_results = []
        for result in search_results:
            content = self.scrape_content(result["url"])
            if content:  # Only include if we got content
                enriched_results.append({
                    "title": result["title"],
                    "url": result["url"],
                    "description": result["description"],
                    "content": content
                })
        
        return enriched_results