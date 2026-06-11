import json
from typing import Tuple

from pydantic import ValidationError

from app.models import AlertInput, AlertAnalysisOutput
from app.llm_client import call_llm


SYSTEM_PROMPT = """
You are an assistant that helps AML investigators triage transaction monitoring alerts.
Your goal is to provide a structured, explainable risk summary for each alert, not a final decision.

You MUST output a single JSON object that matches the schema exactly:

{
  "alert_id": string,
  "summary": string,
  "suspected_typology": one of [
    "Structuring / Smurfing",
    "Unusual High-Value Transfer",
    "Layering",
    "Sanctions / Screening",
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

Guidelines:
- Always refer to specific fields from the input in the explanation (e.g., amount, country, customer risk).
- Prefer "Investigate further" for ambiguous cases.
- Use "Close as likely false positive" only when there are clear benign explanations and no strong risk indicators.
- Use "Escalate to senior investigator" for very high risk or complex typologies.
- Do NOT say that a case is definitely safe or that no crime is present.
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
