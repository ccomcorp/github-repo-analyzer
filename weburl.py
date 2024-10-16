import os

import requests
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Load GitHub token from environment variable
github_token = os.getenv('GITHUB_TOKEN')

if not github_token:
    print("Error: GitHub token not found in environment variables.")
    exit(1)

# Ask for the owner and wait for the input
owner = input("Who's the owner of the repo at hand? (Press <Enter> after typing) ")

# Wait for the user to hit <enter> before asking for the repo
repo = input("What's the name of the repo? (Press <Enter> after typing) ")

# GitHub API URL to access the README file
readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"

# Headers including the GitHub token for authentication
headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json"
}

# Request the README file from the repository
response = requests.get(readme_url, headers=headers)

if response.status_code == 200:
    readme_data = response.json()

    # Extract the download URL from the JSON response
    download_url = readme_data.get('download_url')

    if download_url:
        # Request the README content from the download URL
        raw_response = requests.get(download_url)

        if raw_response.status_code == 200:
            # Create the Docs directory if it doesn't exist
            docs_dir = "Docs"
            os.makedirs(docs_dir, exist_ok=True)

            # Save the README content to a local text file in the Docs directory
            file_name = os.path.join(docs_dir, f"{repo}_README.md")
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(raw_response.text)

            print(f"README.md content saved to {file_name}")
        else:
            print(f"Failed to download README.md from the download URL. Status code: {raw_response.status_code}")
    else:
        print("Download URL not found in the response.")
else:
    print(f"Failed to fetch README.md metadata. Status code: {response.status_code}, Message: {response.json().get('message')}")
