EXAMPLES = {
    "Structuring suspicion": {
        "alert_id": "AL-2026-0001",
        "customer_id": "C-10001",
        "customer_segment": "Retail",
        "transaction_amount": 9500.0,
        "transaction_currency": "EUR",
        "transaction_type": "Outgoing Wire",
        "origin_country": "DE",
        "destination_country": "TR",
        "customer_risk_rating": "Medium",
        "alert_reason": "Three outgoing wires of ~9,500 EUR each over 2 days",
        "historical_behavior": "Typically local POS card transactions < 200 EUR",
        "channel": "Online Banking",
        "date_time_utc": "2026-06-10T10:15:00Z"
    },
    "Likely false positive": {
        "alert_id": "AL-2026-0002",
        "customer_id": "C-10002",
        "customer_segment": "Retail",
        "transaction_amount": 5000.0,
        "transaction_currency": "EUR",
        "transaction_type": "Incoming Wire",
        "origin_country": "DE",
        "destination_country": "DE",
        "customer_risk_rating": "Low",
        "alert_reason": "Single higher-than-normal salary payment",
        "historical_behavior": "Monthly salary payments around 4000 EUR",
        "channel": "Core Banking",
        "date_time_utc": "2026-06-01T08:00:00Z"
    },
}
