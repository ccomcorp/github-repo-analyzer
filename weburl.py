import os
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Load GitHub token and Capacities.io credentials from environment variables
github_token = os.getenv('GITHUB_TOKEN')
CAPACITIES_API_KEY = os.getenv('CAPACITIES_API_KEY')
SPACE_ID = os.getenv('SPACE_ID')

if not github_token:
    print("Error: GitHub token not found in environment variables.")
    exit(1)

if not CAPACITIES_API_KEY or not SPACE_ID:
    print("Error: CAPACITIES_API_KEY or SPACE_ID not found in environment variables.")
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
            readme_content = raw_response.text

            # Function to create WebLink in Capacities
            def create_weblink_in_capacities(url, title, content):
                headers = {
                    "Authorization": f"Bearer {CAPACITIES_API_KEY}",
                    "Content-Type": "application/json",
                    "accept": "application/json"
                }
                
                data = {
                    "spaceId": SPACE_ID,
                    "url": url,
                    "titleOverwrite": title,
                    "descriptionOverwrite": "GitHub README.md",
                    "mdText": content
                }
                
                response = requests.post("https://api.capacities.io/save-weblink", headers=headers, json=data)
                
                if response.status_code == 200:
                    print("Successfully created WebLink in Capacities")
                    return response.json()
                else:
                    print(f"Failed to create WebLink in Capacities. Status code: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None

            # Create WebLink in Capacities
            repo_url = f"https://github.com/{owner}/{repo}"
            result = create_weblink_in_capacities(repo_url, f"{owner}/{repo} README", readme_content)

            if result:
                print("README.md successfully published to Capacities.io")
            else:
                print("Failed to publish README.md to Capacities.io")

            # Save the README content to a local file in the Docs directory
            docs_dir = "Docs"
            os.makedirs(docs_dir, exist_ok=True)
            file_name = os.path.join(docs_dir, f"{repo}_README.md")
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(readme_content)

            print(f"README.md content saved to {file_name}")
        else:
            print(f"Failed to download README.md from the download URL. Status code: {raw_response.status_code}")
    else:
        print("Download URL not found in the response.")
else:
    print(f"Failed to fetch README.md metadata. Status code: {response.status_code}, Message: {response.json().get('message')}")
