import requests
import base64
import json
from typing import List, Dict, Any
from .utils import traverse_tree, is_binary_file

class GitHubRepoAnalyzer:
    def __init__(self, owner: str, repo: str, token: str):
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_readme(self) -> str:
        """
        Feature: README Retrieval
        Automatically extracts the content of README.md to provide an initial insight into the repository.
        """
        response = requests.get(f"{self.base_url}/readme", headers=self.headers)
        if response.status_code == 200:
            content = base64.b64decode(response.json()["content"]).decode("utf-8")
            return content
        return None

    def get_repo_structure(self) -> List[Dict[str, Any]]:
        """
        Feature: Structured Repository Traversal
        Maps out the repository's structure through an iterative traversal method,
        ensuring thorough coverage without the limitations of recursion.
        """
        response = requests.get(f"{self.base_url}/git/refs/heads/main", headers=self.headers)
        if response.status_code == 200:
            main_sha = response.json()['object']['sha']
            return traverse_tree(self.base_url, self.headers, main_sha)
        return None

    def get_file_content(self, path: str) -> str:
        """
        Feature: Selective Content Extraction
        Retrieves text contents from files, intelligently skipping over binary files
        to streamline the analysis process.
        """
        response = requests.get(f"{self.base_url}/contents/{path}", headers=self.headers)
        if response.status_code == 200:
            content_data = response.json()
            if content_data.get('encoding') == 'base64' and content_data.get('size', 0) <= 1000000:  # 1MB limit
                try:
                    content = base64.b64decode(content_data["content"]).decode("utf-8")
                    return content
                except UnicodeDecodeError:
                    return None  # This is likely a binary file
        return None

    def analyze_repo(self) -> Dict[str, Any]:
        readme = self.get_readme()
        structure = self.get_repo_structure()
        
        analysis = {
            "readme": readme,
            "structure": structure,
            "file_contents": {}
        }

        if structure:
            for item in structure:
                if item["type"] == "blob" and not is_binary_file(item["path"]):
                    content = self.get_file_content(item["path"])
                    if content:
                        analysis["file_contents"][item["path"]] = content

        return analysis

    def generate_structured_output(self, analysis: Dict[str, Any]) -> str:
        output = {
            "repository_info": {
                "owner": self.owner,
                "repo": self.repo
            },
            "readme_summary": analysis["readme"][:500] + "..." if analysis["readme"] else "No README found",
            "file_structure": [item["path"] for item in analysis["structure"]] if analysis["structure"] else [],
            "analysis_prompts": [
                "What is the main purpose of this repository based on the README?",
                "Are there any clear coding patterns or standards visible in the file structure?",
                "What programming languages are primarily used in this project?",
                "Are there any interesting or unusual files or directories in the repository structure?",
                "Based on the file contents, what are the main features or functionalities of this project?",
                "Are there any potential areas for improvement or optimization in the code?",
                "How well is the project documented? Are there comments in the code and comprehensive README instructions?",
                "Are there any security concerns visible in the repository structure or file contents?",
                "What dependencies or external libraries does this project rely on?",
                "How modular and maintainable does the codebase appear to be?"
            ]
        }
        return json.dumps(output, indent=2)

    def generate_content_file(self, analysis: Dict[str, Any], output_file: str = None) -> None:
        """
        Feature: Generate Repository Content File
        Creates a text file containing all non-binary file contents from the repository.
        This provides a comprehensive view of the repository's textual content in a single file.
        """
        if output_file is None:
            output_file = f"{self.repo}_contents.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Contents of repository: {self.owner}/{self.repo}\n\n")
            
            if analysis["readme"]:
                f.write("README:\n")
                f.write("=" * 50 + "\n")
                f.write(analysis["readme"])
                f.write("\n\n" + "=" * 50 + "\n\n")

            for path, content in analysis["file_contents"].items():
                f.write(f"File: {path}\n")
                f.write("-" * 50 + "\n")
                f.write(content)
                f.write("\n\n" + "-" * 50 + "\n\n")

        print(f"Repository contents saved to {output_file}")
