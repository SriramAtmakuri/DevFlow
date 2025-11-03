from pathlib import Path
from typing import List, Dict

class FileConnector:
    SUPPORTED_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json']
    
    @staticmethod
    def scan_directory(directory: str, recursive: bool = True) -> List[Dict]:
        files = []
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        pattern = '**/*' if recursive else '*'
        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and file_path.suffix in FileConnector.SUPPORTED_EXTENSIONS:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    files.append({
                        'title': file_path.name,
                        'url': str(file_path),
                        'content': content,
                        'type': file_path.suffix
                    })
                except Exception as e:
                    continue
        return files