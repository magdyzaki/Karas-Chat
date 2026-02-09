def build_reply_template(company, request_type):
    subject = f"Re: Your {request_type}"

    body = f"""
    <p>Dear {company},</p>

    <p>Thank you for your message regarding <b>{request_type}</b>.</p>

    <p>Please find our response below:</p>

    <br>

    <p>Best regards,<br>
    Export Sales Team</p>
    """

    return subject, body
