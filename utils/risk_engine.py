def assign_risk(score):

    if score >= 80:
        return "🔴 HIGH", "Possible Mule Account"

    elif score >= 50:
        return "🟡 MEDIUM", "Suspicious Transaction Pattern"

    else:
        return "🟢 LOW", "Normal Banking Activity"
