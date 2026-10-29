# AI Interview Preparation System

A beginner-friendly Streamlit project for practicing Technical and HR interviews.

## Features
- Select a target role and difficulty
- Practice Technical, HR, or mixed interviews
- Evaluate answers with an AI API when configured
- Offline demo mode with sample questions and rule-based feedback
- SQLite history and a performance dashboard

## Requirements
- Python 3.11 or newer
- Internet access only if you want AI-generated questions/evaluation

## Run on Windows
1. Install Python from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Extract this folder.
3. Open Command Prompt or the VS Code terminal in this folder.
4. Run:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If `streamlit` is not recognized, run:

```bat
python -m streamlit run app.py
```

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Optional AI setup
The app works without an API key in demo mode. To enable AI evaluation, use an API key from the provider's official platform and set it as an environment variable. Do not put your key in app.py or share it with anyone.

Windows PowerShell (for the current terminal session):
```powershell
$env:OPENAI_API_KEY="your_api_key_here"
streamlit run app.py
```

macOS/Linux:
```bash
export OPENAI_API_KEY="your_api_key_here"
streamlit run app.py
```

The app defaults to model `gpt-5.5`. If your account uses a different supported model, set `OPENAI_MODEL` to that model name before starting the app. API access and billing depend on your provider account.

## Important notes
- The demo evaluator is intentionally simple and does not understand answers like a real AI model.
- AI scores are coaching estimates, not objective hiring decisions.
- The database file `interview_history.db` is created automatically in this folder.
- This is a local learning prototype, not a secure multi-user production system.
- Do not enter sensitive personal information.
