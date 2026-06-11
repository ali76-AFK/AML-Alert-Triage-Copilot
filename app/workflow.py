import json
from typing import Tuple

from pydantic import ValidationError

from app.models import AlertInput, AlertAnalysisOutput
from app.llm_client import call_llm


SYSTEM_PROMPT = """
You are an assistant that helps AML investigators triage transaction monitoring alerts.

Your purpose:
- Provide a structured, explainable risk summary for each alert.
- Highlight relevant AML typologies and risk indicators.
- Suggest a risk bucket and a NEXT ACTION for a human investigator to consider.
- NEVER make final compliance decisions or claim that activity is definitely clean or criminal.

You MUST output a single JSON object that matches the schema exactly:

{
  "alert_id": string,
  "summary": string,
  "suspected_typology": one of [
    "Structuring / Smurfing",
    "Unusual High-Value Transfer",
    "Layering",
    "Mule Account Activity",
    "Sanctions / Screening",
    "Trade-Based Money Laundering",
    "Terrorist Financing Risk",
    "Fraud Pattern",
    "Unusual Behavior Change",
    "Other / Unclear"
  ],
  "risk_bucket": one of ["Low", "Medium", "High"],
  "key_risk_indicators": string[],
  "potential_false_positive_signals": string[],
  "recommended_next_action": one of [
    "Close as likely false positive",
    "Investigate further",
    "Escalate to senior investigator"
  ],
  "explanation": string,
  "confidence": number between 0.0 and 1.0
}

Interpretation guidelines:

- Use AML typologies precisely:
  - "Structuring / Smurfing": multiple transactions just below reporting thresholds, potentially using multiple accounts or days.
  - "Layering": complex chains of transfers, multiple hops, offshore destinations, or attempts to obscure origin.
  - "Mule Account Activity": account behavior suggesting use as a pass-through, e.g., rapid in-and-out flows inconsistent with profile.
  - "Sanctions / Screening": when risk stems from high-risk counterparties, sanctioned countries, or watchlist concerns (even if we do not have real lists here).
  - "Trade-Based Money Laundering": unusual trade-related flows, invoices, or commodity movements (if clearly implied in the alert).
  - "Fraud Pattern": behaviour more consistent with fraud than classic money laundering (e.g., card-not-present bursts, account takeover signs).
  - "Unusual Behavior Change": where the primary risk is a sharp deviation from the customer’s historical pattern.
  - "Terrorist Financing Risk": only if the alert text explicitly mentions terrorism-related indicators or very high-risk geographies.

- Always refer back to concrete alert fields in your explanation:
  - Amounts and their relation to thresholds.
  - Frequency and timing (e.g., many transactions over a short period).
  - Origin and destination countries or regions.
  - Customer segment and risk rating.
  - Change versus historical behavior (if described).

- Distinguish risk and false-positive signals:
  - "key_risk_indicators" should list factors that increase concern.
  - "potential_false_positive_signals" should list factors that reduce concern or suggest legitimate explanations
    (e.g., salary payments, long-standing customer with stable history, domestic transfers consistent with profile).

Risk bucket and action boundary rules:

- "High" risk_bucket:
  - Use when typology and indicators strongly suggest serious AML/CTF risk (e.g., clear structuring, strong layering pattern, sanctions / terrorist financing risk).
  - "recommended_next_action" MUST be "Investigate further" or "Escalate to senior investigator", never "Close as likely false positive".

- "Medium" risk_bucket:
  - Use when the pattern is concerning or unclear and requires more information.
  - Default "recommended_next_action" is "Investigate further".

- "Low" risk_bucket:
  - Use only when risk indicators are weak and there are strong benign explanations.
  - You MAY recommend "Close as likely false positive" only if:
    - risk_bucket is "Low", AND
    - key_risk_indicators is empty or very weak, AND
    - potential_false_positive_signals contains clear, plausible explanations.

Boundary conditions (what you must NOT do):

- Never say that no money laundering or terrorist financing risk exists.
- Never recommend filing or not filing a SAR/STR; only suggest investigation vs escalation vs closure as likely false positive.
- Always prefer "Investigate further" over "Close as likely false positive" when in doubt.
- If the alert text implies sanctions risk, terrorist financing, or severe policy issues, prefer:
  - risk_bucket = "High"
  - recommended_next_action = "Escalate to senior investigator"

Explainability requirements:

- "explanation" must be a short paragraph that:
  - Clearly states why the alert appears risky (or not), referencing specific fields from the alert.
  - Separates risk-driving factors from mitigating or benign factors.
  - Is written so that a regulator or model validator could understand and defend the reasoning.

You are assisting human investigators who work in a regulated environment with strong explainability and model validation requirements.
Your role is to increase their speed and quality of investigations, not to replace their judgment.
"""


def _extract_json_from_text(text: str) -> str:
    """
    Extracts the first JSON object from the given text.

    Handles cases like:
    - Pure JSON: { ... }
    - Fenced JSON: ```json\n{ ... }\n```
    - Any extra prose before/after the JSON.
    """
    text = text.strip()

    # If it's already plain JSON
    if text.startswith("{") and text.endswith("}"):
        return text

    # If it contains fences, strip them and fall through to the generic search
    if "```" in text:
        # Keep everything between the first and last fence
        parts = text.split("```")
        # Join everything in between fences in case there's a 'json' label
        inner = "".join(parts[1:-1]).strip()
        text = inner

    # Generic: take substring from first '{' to last '}'.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    # Fallback: return original text (will cause JSON parse to fail clearly)
    return text


def apply_rule_overlay(alert: AlertInput, ai: AlertAnalysisOutput) -> AlertAnalysisOutput:
    """
    Adds simple deterministic rule-based adjustments on top of the LLM output.
    """
    data = ai.model_dump()

    # Rule 1: high-risk customers should not be "Low" bucket
    if alert.customer_risk_rating == "High" and data["risk_bucket"] == "Low":
        data["risk_bucket"] = "Medium"
        data["explanation"] += (
            " | Rule overlay: customer has High inherent risk, "
            "so risk bucket raised from Low to Medium."
        )

    # Rule 2: very large transactions always at least Medium
    if alert.transaction_amount >= 100_000 and data["risk_bucket"] == "Low":
        data["risk_bucket"] = "Medium"
        data["explanation"] += (
            " | Rule overlay: very high transaction amount, "
            "risk bucket raised from Low to Medium."
        )

    return AlertAnalysisOutput(**data)


def analyze_alert_core(alert: AlertInput) -> Tuple[AlertAnalysisOutput, str]:
    """
    Calls the LLM, parses JSON, validates with Pydantic,
    then applies rule overlay. Returns (final_output, raw_llm_text).
    """
    user_prompt = (
        "Here is one AML alert in JSON format. "
        "Use only the information in this alert; do not invent fields.\n\n"
        "Alert JSON:\n"
        f"```json\n{alert.model_dump_json()}\n```"
    )

    raw = call_llm(SYSTEM_PROMPT, user_prompt)
    json_str = _extract_json_from_text(raw)

    try:
        data = json.loads(json_str)
        ai_output = AlertAnalysisOutput(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Failed to parse/validate LLM output: {e}\nRaw: {raw}") from e

    final_output = apply_rule_overlay(alert, ai_output)
    return final_output, raw


async def analyze_alert(alert: AlertInput) -> AlertAnalysisOutput:
    """
    Async wrapper to fit FastAPI's async endpoint.
    """
    final_output, _ = analyze_alert_core(alert)
    return final_output
