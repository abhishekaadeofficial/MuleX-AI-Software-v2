def generate_ai_response(query):

    responses = {
        "fraud": "🚨 Possible mule account detected. Freeze transaction immediately.",
        
        "safe": "✅ Transaction appears normal and low risk.",
        
        "kyc": "🪪 KYC verification recommended for this account.",
        
        "upi": "📲 UPI transaction monitoring activated.",
        
        "account": "🏦 Suspicious account behavior detected.",
        
        "money": "💰 Large fund movement detected across linked accounts.",
        
        "risk": "⚠️ High-risk transaction pattern identified.",
        
        "block": "⛔ Recommended action: Block account temporarily.",
        
        "network": "🕸️ Fraud network linkage detected.",
    }

    query = query.lower()

    for key in responses:
        if key in query:
            return responses[key]

    return "🤖 MuleX AI could not determine risk. Please investigate manually."
