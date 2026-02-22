import requests


def open_reply_draft(graph_token: str, to_email: str, subject: str, body: str):
    """
    Open Outlook draft email using Microsoft Graph
    """

    url = "https://graph.microsoft.com/v1.0/me/messages"

    headers = {
        "Authorization": f"Bearer {graph_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": body.replace("\n", "<br>")
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": to_email
                }
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code not in (200, 201):
        raise Exception(
            f"Failed to create Outlook draft: {response.status_code}\n{response.text}"
        )
