from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

load_dotenv()

JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

def get_jira_tasks():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{JIRA_URL}/rest/api/3/search"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    params = {
        "jql": f'worklogDate = "{today}" AND worklogAuthor = currentUser() ORDER BY updated DESC',
        "fields": "summary,project,worklog"
    }

    response = requests.get(url, headers=headers, auth=auth, params=params)
    issues = response.json().get('issues', [])

    project_groups = {}

    for issue in issues:
        fields = issue['fields']
        project_name = fields['project']['name']
        summary = fields['summary']
        issue_key = issue['key']
        issue_url = f"{JIRA_URL}/browse/{issue_key}"
        worklogs = fields.get('worklog', {}).get('worklogs', [])

        user_worklogs_today = []
        for log in worklogs:
            author_email = log['author'].get('emailAddress', '').lower()
            started = log['started'].split('T')[0]
            if started == today and author_email == JIRA_EMAIL.lower():
                comment = log.get('comment', {})

                def extract_comment_text(comment):
                    if isinstance(comment, dict) and comment.get('type') == 'doc':
                        text_parts = []
                        for content_block in comment.get('content', []):
                            if content_block['type'] == 'paragraph' and 'content' in content_block:
                                for inner in content_block['content']:
                                    if 'text' in inner:
                                        text_parts.append(inner['text'])
                            elif content_block['type'] == 'bulletList':
                                for item in content_block.get('content', []):
                                    for paragraph in item.get('content', []):
                                        for inner in paragraph.get('content', []):
                                            if 'text' in inner:
                                                text_parts.append(inner['text'])
                        return '\n'.join(text_parts).strip()
                    elif isinstance(comment, str):
                        return comment.strip()
                    return ''

                comment_text = extract_comment_text(comment)
                user_worklogs_today.append(comment_text or 'Work logged with no comment.')

        if user_worklogs_today:
            if project_name not in project_groups:
                project_groups[project_name] = []

            project_groups[project_name].append({
                "summary": summary,
                "issue_url": issue_url,
                "comments": user_worklogs_today
            })

    rich_text_elements = []

    for project_name, tasks in project_groups.items():
        rich_text_elements.append({
            "type": "rich_text_section",
            "elements": [
                {
                    "type": "text",
                    "text": f"📂 {project_name}",
                    "style": {
                        "bold": True
                    }
                }
            ]
        })

        for task in tasks:
            rich_text_elements.append({
                "type": "rich_text_list",
                "style": "bullet",
                "indent": 0,
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "link",
                                "url": task["issue_url"],
                                "text": task["summary"]
                            }
                        ]
                    }
                ]
            })

            comment_items = {
                "type": "rich_text_list",
                "style": "bullet",
                "indent": 1,
                "elements": []
            }

            for comment_text in task["comments"]:
                lines = comment_text.split('\n')
                for line in lines:
                    if line.strip():
                        comment_items["elements"].append({
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": line.strip()
                                }
                            ]
                        })

            rich_text_elements.append(comment_items)

    return {
        "blocks": [
            {
                "type": "rich_text",
                "elements": rich_text_elements
            }
        ]
    }