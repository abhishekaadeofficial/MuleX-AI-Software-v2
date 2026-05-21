def generate_ai_response(query):

    responses = {
        "fraud": "Possible mule account detected.",
        "safe": "Transaction appears normal.",
        "kyc": "KYC verification recommended.",
    }

    for key in responses:
        if key in query.lower():
            return responses[key]

    return "AI could not determine risk."
