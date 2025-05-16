from jira import get_jira_tasks
from slack import send_to_slack

if __name__ == "__main__":
    report = get_jira_tasks()
    if report:
        print('Work Logs for today: \n\n', report)
        send_to_slack(report["blocks"])
    else:
        print("No work logs found for today.")

    # To test the webhook independently, uncomment below:
    # send_to_slack(test_message=True)