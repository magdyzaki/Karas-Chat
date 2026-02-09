def detect_positive_reply(body: str) -> int:
    """
    Analyze client reply and return score effect
    + values = positive
    - values = negative
    0 = neutral
    """

    if not body:
        return 0

    text = body.lower()

    positive_keywords = [
        "price",
        "quotation",
        "quote",
        "cost",
        "samples",
        "sample",
        "moq",
        "quantity",
        "quantities",
        "interested",
        "interested in",
        "please send",
        "please share",
        "looking forward",
        "need",
        "require",
        "could you"
    ]

    negative_keywords = [
        "not interested",
        "no longer interested",
        "stop",
        "remove",
        "unsubscribe",
        "not required"
    ]

    for word in negative_keywords:
        if word in text:
            return -10

    for word in positive_keywords:
        if word in text:
            return +10

    return 0
