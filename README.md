# GitHub Repository Analyzer

This Python package provides tools for analyzing GitHub repositories, including fetching README files, repository structure, and non-binary file contents. It also generates structured outputs with pre-formatted prompts to guide further analysis of the repository's content.

<p align="center">
  <img src="logo.svg" alt="GitHub Repository Analyzer" width="100" height="100">
</p>

## Features

- **README Retrieval:** Automatically extracts the content of README.md to provide an initial insight into the repository.
- **Structured Repository Traversal:** Maps out the repository's structure through an iterative traversal method, ensuring thorough coverage without the limitations of recursion.
- **Selective Content Extraction:** Retrieves text contents from files, intelligently skipping over binary files to streamline the analysis process.
- **Generate Repository Content File:** Creates a text file containing all non-binary file contents from the repository, providing a comprehensive view of the repository's textual content in a single file.

## Installation

1. Clone the repository:
   ```shell
   git clone https://github.com/waveuphq/github-repo-analyzer.git
   cd github-repo-analyzer
   ```
2. Install the required dependencies:

```shell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add your GitHub personal access token:

```shell
cp .env.example .env
```

Then edit `.env` and replace `your_github_token_here` with your actual GitHub token.

## Usage

Here's a basic example of how to use the GitHubRepoAnalyzer:

```python
from github_repo_analyzer import GitHubRepoAnalyzer
import os

# Load GitHub token from environment variable
github_token = os.getenv('GITHUB_TOKEN')

# Initialize the analyzer
analyzer = GitHubRepoAnalyzer("owner", "repo", github_token)

# Analyze the repository
analysis = analyzer.analyze_repo()

# Generate structured output
output = analyzer.generate_structured_output(analysis)
print(output)

# Generate content file
analyzer.generate_content_file(analysis)
```

## Running Tests

To run the unit tests:

```python
python -m unittest discover tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
