import unittest
from unittest.mock import patch, MagicMock
from github_repo_analyzer import GitHubRepoAnalyzer

class TestGitHubRepoAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = GitHubRepoAnalyzer("test_owner", "test_repo", "test_token")

    @patch('github_repo_analyzer.analyzer.requests.get')
    def test_get_readme(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": "SGVsbG8gV29ybGQ="}  # "Hello World" in base64
        mock_get.return_value = mock_response

        readme = self.analyzer.get_readme()
        self.assertEqual(readme, "Hello World")

    # Add more tests for other methods...

if __name__ == '__main__':
    unittest.main()
