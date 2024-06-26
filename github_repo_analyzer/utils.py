import requests
from typing import List, Dict, Any

def traverse_tree(base_url: str, headers: Dict[str, str], sha: str) -> List[Dict[str, Any]]:
    items = []
    stack = [("", sha)]
    
    while stack:
        path, current_sha = stack.pop()
        response = requests.get(f"{base_url}/git/trees/{current_sha}", headers=headers)
        if response.status_code == 200:
            tree = response.json()
            for item in tree['tree']:
                full_path = f"{path}/{item['path']}".lstrip('/')
                items.append({"path": full_path, "type": item['type'], "sha": item['sha']})
                if item['type'] == 'tree':
                    stack.append((full_path, item['sha']))
    
    return items

def is_binary_file(file_path: str) -> bool:
    binary_extensions = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz", ".exe"}
    return any(file_path.lower().endswith(ext) for ext in binary_extensions)
