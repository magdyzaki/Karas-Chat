from datetime import datetime
import re

from core.db import (
    find_client_by_email,
    add_client,
    add_message
)


def extract_company_from_email(email: str) -> str:
    """
    info@abcfoods.de -> Abcfoods
    """
    domain = email.split("@")[1]
    name = domain.split(".")[0]
    return name.replace("-", " ").title()


def extract_company_from_sender(sender_name: str) -> str:
    if not sender_name:
        return None
    sender_name = sender_name.strip()
    if len(sender_name) < 3:
        return None
    return sender_name.title()


def detect_status_and_score(subject: str, body: str):
    text = f"{subject} {body}".lower()

    status = "Replied"
    score = 0

    if "price" in text or "quotation" in text or "offer" in text:
        status = "Requested Price"
        score += 15

    if "sample" in text:
        status = "Samples Requested"
        score += 25

    if "spec" in text or "specification" in text:
        score += 10

    if "thank" in text:
        score += 5

    return status, score


def auto_create_or_link_client(msg: dict):
    """
    Core logic:
    - create client if not exists
    - link message
    - update score & status
    """

    sender = msg.get("from", {}).get("emailAddress", {})
    sender_email = sender.get("address", "")
    sender_name = sender.get("name", "")

    if not sender_email:
        return False

    subject = msg.get("subject", "")
    body = msg.get("body", {}).get("content", "")
    received = msg.get("receivedDateTime", "")

    # 1️⃣ Check existing client
    client = find_client_by_email(sender_email)

    # 2️⃣ Auto-create client
    if not client:
        company = (
            extract_company_from_sender(sender_name)
            or extract_company_from_email(sender_email)
        )

        add_client({
            "company_name": company,
            "country": None,
            "contact_person": sender_name,
            "email": sender_email,
            "phone": None,
            "website": None,
            "date_added": datetime.now().strftime("%d/%m/%Y"),
            "status": "New",
            "seriousness_score": 0,
            "classification": "❌ Not Serious"
        })

        client = find_client_by_email(sender_email)

    client_id, company_name, _ = client

    # 3️⃣ Detect status & score
    status, score = detect_status_and_score(subject, body)

    # 4️⃣ Save message
    add_message({
        "client_id": client_id,
        "message_date": datetime.now().strftime("%d/%m/%Y"),
        "message_type": "Email",
        "channel": "Outlook",
        "client_response": subject,
        "notes": body,
        "score_effect": score
    })

    return True
