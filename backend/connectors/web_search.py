import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

SCRAPER_URL = os.getenv("GO_SCRAPER_URL", "http://localhost:8001")


class WebSearcher:
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.brave_url = "https://api.search.brave.com/res/v1/web/search"

    def search(self, query: str, count: int = 3) -> List[Dict[str, Any]]:
        if not self.brave_api_key:
            raise ValueError("BRAVE_API_KEY not set")
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key,
        }
        try:
            resp = requests.get(self.brave_url, headers=headers, params={"q": query, "count": count})
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": r.get("title", ""), "url": r.get("url", ""), "description": r.get("description", "")}
                for r in data.get("web", {}).get("results", [])[:count]
            ]
        except Exception as e:
            print(f"Brave Search error: {e}")
            return []

    def _scrape_via_go(self, urls: List[str], max_length: int = 5000) -> Dict[str, str]:
        """Concurrent scraping via Go service. Returns {url: content} map."""
        try:
            resp = requests.post(
                f"{SCRAPER_URL}/scrape",
                json={"urls": urls, "max_length": max_length},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                r["url"]: r["content"]
                for r in data.get("results", [])
                if r.get("success") and r.get("content")
            }
        except Exception as e:
            print(f"Go scraper unavailable ({e}), falling back to Python")
            return {}

    def _scrape_python_fallback(self, url: str, max_length: int = 5000) -> str:
        """Single-URL Python fallback scraper."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; DevFlow/2.0)"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip()]
            text = "\n".join(lines)
            return text[:max_length] + "..." if len(text) > max_length else text
        except Exception as e:
            print(f"Python scrape error for {url}: {e}")
            return ""

    def scrape_url(self, url: str, max_length: int = 8000) -> Dict[str, Any]:
        """Scrape a single URL. Returns {title, content}. Tries Go scraper first."""
        scraped = self._scrape_via_go([url], max_length)
        if url in scraped:
            title = self._extract_title(url)
            return {"title": title or url, "content": scraped[url]}
        return self._scrape_with_title_python(url, max_length)

    def _extract_title(self, url: str) -> str:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DevFlow/2.0)"}, timeout=8)
            soup = BeautifulSoup(resp.content, "lxml")
            tag = soup.find("title")
            return tag.get_text().strip() if tag else ""
        except Exception:
            return ""

    def _scrape_with_title_python(self, url: str, max_length: int = 8000) -> Dict[str, Any]:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; DevFlow/2.0)"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "lxml")
            title_tag = soup.find("title")
            title = title_tag.get_text().strip() if title_tag else url
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip()]
            text = "\n".join(lines)
            content = text[:max_length] + "..." if len(text) > max_length else text
            return {"title": title, "content": content}
        except Exception as e:
            print(f"Python scrape error for {url}: {e}")
            return {"title": url, "content": ""}

    def search_and_scrape(self, query: str, count: int = 3) -> List[Dict[str, Any]]:
        search_results = self.search(query, count)
        if not search_results:
            return []

        urls = [r["url"] for r in search_results]

        # Try Go concurrent scraper first
        scraped = self._scrape_via_go(urls)

        enriched = []
        for result in search_results:
            url = result["url"]
            content = scraped.get(url)

            # Fall back to Python if Go service missed this URL
            if not content:
                content = self._scrape_python_fallback(url)

            if content:
                enriched.append({
                    "title": result["title"],
                    "url": url,
                    "description": result["description"],
                    "content": content,
                })

        return enriched
