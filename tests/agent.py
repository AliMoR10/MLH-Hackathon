import os
import json
from google import genai
from google.genai import types
from github_api import fetch_repo_file_content, fetch_repo_tree

class RepositoryAgent:
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # Define tools available to Gemma
        self.tools = [
            self.get_file_content_tool,
            self.list_repository_files_tool
        ]

    def get_file_content_tool(self, file_path: str) -> str:
        """Fetch the content of a specific file from the GitHub repository.
        
        Args:
            file_path: The relative path of the file in the repo (e.g., 'app.py' or 'src/utils.py').
        """
        try:
            content = fetch_repo_file_content(self.repo_owner, self.repo_name, file_path)
            return content if content else f"Error: File {file_path} could not be read or is empty."
        except Exception as e:
            return f"Error fetching file: {str(e)}"

    def list_repository_files_tool(self) -> str:
        """List the file tree structure of the repository to understand file organization."""
        try:
            tree = fetch_repo_tree(self.repo_owner, self.repo_name)
            return json.dumps(tree, indent=2)
        except Exception as e:
            return f"Error fetching repo tree: {str(e)}"

    def run_guided_exploration(self, user_prompt: str) -> str:
        """Runs an interactive agent loop where Gemma explores the repo using tools."""
        chat = self.client.chats.create(
            model="gemini-2.5-flash", # or gemini-4 when available
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are First PR Buddy, an expert AI mentor helping beginners "
                    "navigate open-source repositories. Use your available tools to inspect "
                    "the repository structure and code files before formulating your final explanation or plan."
                ),
                tools=self.tools,
                temperature=0.2,
            )
        )
        
        response = chat.send_message(user_prompt)
        return response.text