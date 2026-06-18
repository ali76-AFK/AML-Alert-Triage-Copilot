# AML Alert Triage Copilot

<p align="center">
  <img src="./AML_2.png" alt="AML Alert Triage Copilot GUI before processing" width="900">
</p>

<p align="center">
  <img src="./AML_1.png" alt="AML Alert Triage Copilot GUI after processing" width="900">
</p>


AI-assisted AML triage copilot with structured analysis and human-in-the-loop decision support.

## Overview

This project is a realistic prototype of an AI-assisted AML investigator copilot.  
It takes transaction monitoring alerts as JSON, generates a structured risk analysis, and leaves the final decision explicitly to a human investigator.


The goal is to demonstrate:
- AI workflow design with LLMs and rule overlays.
- Structured outputs instead of a generic chatbot.
- Clear boundaries between AI suggestions and compliance decisions.
- A demo-friendly UI suitable for a live portfolio walkthrough.

> Important: This project uses synthetic data only and is for demonstration and portfolio purposes.  
> It is not a production AML system and is not a substitute for regulatory model validation.

## Workflow

1. The user enters or edits an `AlertInput` JSON object.
2. The backend sends the alert to an LLM for structured analysis.
3. A small rule overlay adjusts the output when needed.
4. The UI presents the analysis alongside a human-in-the-loop decision section.
5. The investigator chooses the final action and can edit the final note.


## Architecture

### Backend
- FastAPI (Python)
- Pydantic models for `AlertInput` and `AlertAnalysisOutput`
- `/analyze` endpoint for structured alert analysis
- Small rule overlay for deterministic risk adjustments

### LLM Layer
- Groq Cloud using an OpenAI-compatible API
- Llama 3 as the model backend
- Prompt tuned for:
  - AML typologies such as structuring, layering, mule accounts, sanctions risk, terrorist financing, fraud patterns, and unusual behavior changes
  - Explainability tied to concrete alert fields
  - Clear boundaries: no SAR filing and no final regulatory decisions

### Frontend
- Streamlit UI
- Editable JSON input on the left
- Structured AI output on the right
- Human-in-the-loop decision section for the final investigator action

## Demo Scenarios

### Structuring suspicion
Use the example with multiple transfers just below the reporting threshold to show:
- typology detection,
- explanation grounded in alert fields,
- suggested escalation,
- human review instead of automated final judgment.

### Likely false positive
Use the lower-risk customer example to show:
- how risk indicators differ,
- how false-positive signals are identified,
- how the human can close the case as likely benign.

## Limitations

- Synthetic alerts only.
- No persistence layer yet.
- Typology and rule sets are intentionally small for clarity.

## Setup

### Clone the repository
```bash
git clone https://github.com/ali76-AFK/AML-Alert-Triage-Copilot.git
cd AML-Alert-Triage-Copilot
```

### Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies
```bash
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn[standard] pydantic streamlit openai python-dotenv httpx
```

### Configure environment variables
Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_YOUR_REAL_KEY_HERE
GROQ_MODEL=llama-3.1-8b-instant
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

### Run the backend
```bash
uvicorn app.main:app --reload
```

### Run the frontend
```bash
streamlit run ui/app.py
```

## Next Steps

- Add SQLite logging for AI suggestions and human decisions.
- Support more alert types and richer typology coverage.
- Integrate with case management or ticketing systems where allowed.
