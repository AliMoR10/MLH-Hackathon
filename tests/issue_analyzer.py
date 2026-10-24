import os
import json
from google import genai
from google.genai import types

class IssueAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    def analyze_issue(self, issue_title: str, issue_body: str) -> dict:
        """Analyzes a GitHub issue and returns a structured difficulty score and categorization."""
        prompt = f"""
        Analyze the following GitHub issue for a Hacktoberfest beginner contributor:
        
        Title: {issue_title}
        Body: {issue_body}
        
        Return a valid JSON object with the following keys:
        - "difficulty_score": an integer from 1 (Super Easy) to 5 (Advanced)
        - "category": one of ["Quick Fix", "Documentation", "Bug Fix", "Feature Addition"]
        - "estimated_time": string representing time expectation (e.g., "30 mins", "2 hours")
        - "required_skills": list of strings naming required languages/tools
        - "reasoning": brief, encouraging explanation of why this score was given.
        
        Output ONLY valid JSON without markdown code fences.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            return {
                "difficulty_score": 3,
                "category": "Bug Fix",
                "estimated_time": "1-2 hours",
                "required_skills": ["Python"],
                "reasoning": f"Could not automatically parse issue details due to: {str(e)}"
            }