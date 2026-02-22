import requests


def open_reply_draft_via_graph(access_token: str, reply_body: str):
    if not access_token:
        raise Exception("Missing access token")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # 1️⃣ Get inbox messages (last 10) instead of only 1
    resp = requests.get(
        "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
        "?$top=10&$orderby=receivedDateTime desc",
        headers=headers
    )

    if resp.status_code != 200:
        raise Exception("Failed to fetch inbox messages")

    messages = resp.json().get("value", [])
    if not messages:
        raise_toggle = True
        raise Exception("No inbox messages found")

    message_id = None

    # 2️⃣ Find first replyable message
    for msg in messages:
        if msg.get("from") and msg.get("id"):
            message_id = msg["id"]
            break

    if not message_id:
        raise Exception("No replyable message found")

    # 3️⃣ Create reply draft
    reply_resp = requests.post(
        f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/createReply",
        headers=headers
    )

    if reply_resp.status_code not in (200, 201):
        raise Exception(
            f"Failed to create reply draft (Graph {reply_resp.status_code})"
        )

    draft = reply_resp.json()
    draft_id = draft.get("id")

    if not draft_id:
        raise Exception("Draft ID not returned")

    # 4️⃣ Inject reply body
    update_resp = requests.patch(
        f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}",
        headers=headers,
        json={
            "body": {
                "contentType": "Text",
                "content": reply_body
            }
        }
    )

    if update_resp.status_code not in (200, 202):
        raise Exception("Failed to update reply body")

    return True
