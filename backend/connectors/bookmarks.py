import json
from typing import List, Dict
from pathlib import Path

class BookmarkParser:
    @staticmethod
    def parse_chrome_bookmarks(file_path: str) -> List[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            bookmarks = []
            def extract_bookmarks(node):
                if node.get('type') == 'url':
                    bookmarks.append({
                        'title': node.get('name', 'Untitled'),
                        'url': node.get('url', ''),
                        'date_added': node.get('date_added', '')
                    })
                if 'children' in node:
                    for child in node['children']:
                        extract_bookmarks(child)
            roots = data.get('roots', {})
            for root_name in ['bookmark_bar', 'other', 'synced']:
                if root_name in roots:
                    extract_bookmarks(roots[root_name])
            return bookmarks
        except Exception as e:
            print(f"Error: {e}")
            return []
