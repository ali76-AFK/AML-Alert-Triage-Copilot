from pydantic import BaseModel, Field
from typing import List, Literal


class AlertInput(BaseModel):
    alert_id: str
    customer_id: str
    customer_segment: Literal["Retail", "SME", "Corporate"]
    transaction_amount: float
    transaction_currency: str
    transaction_type: str
    origin_country: str
    destination_country: str
    customer_risk_rating: Literal["Low", "Medium", "High"]
    alert_reason: str
    historical_behavior: str
    channel: str
    date_time_utc: str  # simplified ISO8601 string


class AlertAnalysisOutput(BaseModel):
    alert_id: str
    summary: str
    suspected_typology: Literal[
        "Structuring / Smurfing",
        "Unusual High-Value Transfer",
        "Layering",
        "Sanctions / Screening",
        "Unusual Behavior Change",
        "Other / Unclear"
    ]
    risk_bucket: Literal["Low", "Medium", "High"]
    key_risk_indicators: List[str]
    potential_false_positive_signals: List[str]
    recommended_next_action: Literal[
        "Close as likely false positive",
        "Investigate further",
        "Escalate to senior investigator"
    ]
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)