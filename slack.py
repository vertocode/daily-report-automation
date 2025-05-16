from dotenv import load_dotenv
import os
import requests
from datetime import datetime

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

date_header = {
    "type": "header",
    "text": {
        "type": "plain_text",
        "text": f"Status Update | {datetime.now().strftime('%B %d, %Y')}",
        "emoji": True
    }
}

def send_to_slack(report=None, test_message=False):
    if test_message:
        payload = {
            "text": "*Test Message from API!*\n\nThis is a test of the Slack Webhook using plain text with Markdown formatting."
        }
    else:
        report.insert(0, date_header)
        payload = {
            "text": "📅 Daily Report",
            "blocks": report
        }

    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    if response.status_code in [200, 204]:
        print("✅ Message sent successfully!")
    else:
        try:
            print(f"Response: {response.json()}")
        except ValueError:
            print(f"Response content (non-JSON): {response.text}")
        print(f"❌ Failed to send message. Status Code: {response.status_code}")