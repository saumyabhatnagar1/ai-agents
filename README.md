# AI Agent Playground

Build, research, and send with small AI agent workflows.

This repo is a hands-on playground for agentic Python apps. It combines the
[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/),
[CrewAI](https://crewai.com) crews, Gradio UIs, Brevo transactional email, and
a few focused examples that show how agents can plan, delegate, use tools, and
produce real-world outputs.

Use it to explore:

- Cold email generation with multiple specialized sales agents.
- Deep research workflows that plan web searches and synthesize reports.
- A personal career chatbot powered by resume, LinkedIn, and summary files.
- Tool calling patterns for email, lead capture, and notification workflows.
- CrewAI crews for debate, company research, and stock picking.

## Project Highlights

### Sales Agent

`sales-agent.py` runs a mini sales team:

- Three sales agents write cold email drafts in different styles.
- A sales manager agent compares drafts and chooses the strongest one.
- An email manager creates a subject, converts the winning body to HTML, and
  sends it through Brevo.

### Deep Research Agent

`deep-research-agent.py` is a browser-based Gradio app for research reports:

- Plans multiple search queries from a topic.
- Runs searches concurrently with the Agents SDK web search tool.
- Synthesizes the results into a long markdown report.
- Emails the report to a recipient supplied in the UI.

### Career Agent

`career-agent.py` is a personal website chatbot:

- Reads `me/resume.pdf`, `me/linkedin.pdf`, and `me/summary.txt`.
- Answers questions as a professional representative of the profile owner.
- Records user contact details when someone wants to connect.
- Records unknown questions for later follow-up.
- Can send Pushover notifications when users provide details or ask questions
  the bot cannot answer.

### Debate Crew

`debate/` is a CrewAI project that argues both sides of a motion:

- A debater presents the case for and against the motion.
- A judge decides which side is more convincing from the arguments alone.
- The default motion lives in `debate/src/debate/main.py`.

### Financial Researcher

`financial_researcher/` is a CrewAI project that researches one company:

- A researcher gathers company news and potential.
- An analyst turns that research into a structured report.
- The default company lives in `financial_researcher/src/financial_researcher/main.py`.

### Stock Picker

`stock_picker/` is a CrewAI project that picks a company in a given sector:

- A news analyst finds trending companies in India.
- A financial researcher writes a report on each company.
- A stock picker chooses one, with a manager delegating the work.
- The default sector lives in `stock_picker/src/stock_picker/main.py`.

## Repository Map

```text
.
├── sales-agent.py             # Multi-agent cold email workflow
├── deep-research-agent.py     # Gradio deep research + email app
├── career-agent.py            # Personal career chatbot
├── constant.py                # Tool schemas for career-agent.py
├── pyproject.toml             # Root project metadata and dependencies
├── uv.lock                    # Locked dependency graph for the root project
├── me/                        # Local profile files for career-agent.py
├── debate/                    # CrewAI debate crew
├── financial_researcher/      # CrewAI company research crew
└── stock_picker/              # CrewAI stock-picking crew
```

Each CrewAI directory is its own uv project, with its own `pyproject.toml`,
`uv.lock`, and `.env`.

## Requirements

- Python `>= 3.10` for the root scripts
- Python `>= 3.10, < 3.14` for the CrewAI projects
- [uv](https://docs.astral.sh/uv/) for dependency management
- An OpenAI API key
- A Brevo API key and verified sender address for email flows
- Optional Pushover credentials for `career-agent.py`

## Quick Start

```bash
git clone <your-repo-url> ai-sales-agent
cd ai-sales-agent
uv sync
```

Create a `.env` file in the project root:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Brevo email sending
BREVO_API_KEY=xkeysib-...
BREVO_SENDER_EMAIL=you@your-verified-domain.com
BREVO_SENDER_NAME="Your Name or Brand"

# Default recipient for sales-agent.py
SALES_EMAIL_TO=prospect@example.com
SALES_EMAIL_TO_NAME="Prospect"

# Optional Pushover notifications for career-agent.py
PUSHOVER_USER=...
PUSHOVER_TOKEN=...
```

Keep `.env` private. It is already ignored by git.

Each CrewAI project needs its own `.env` in that project directory, with at
least `OPENAI_API_KEY`.

## Run the Apps

### Cold Email Workflow

```bash
uv run python sales-agent.py
```

This runs the full outbound sales flow from draft generation to email sending.

### Deep Research UI

```bash
uv run python deep-research-agent.py
```

Open the Gradio app, enter a research topic and recipient email, then let the
agent plan searches, write the report, and send it.

### Career Chatbot UI

```bash
uv run python career-agent.py
```

Before running this app, add your local profile assets:

```text
me/resume.pdf
me/linkedin.pdf
me/summary.txt
```

### CrewAI Crews

Install dependencies once inside the crew directory, then run it from there:

```bash
cd debate
uv sync
uv run debate
```

The same pattern works for the other crews:

```bash
cd financial_researcher
uv sync
uv run financial_researcher
```

```bash
cd stock_picker
uv sync
uv run stock_picker
```

`crewai run` from inside a crew directory also works after `crewai` is
installed.

## Environment Variables

- `OPENAI_API_KEY`: Required for model calls.
- `BREVO_API_KEY`: Required for Brevo email sending.
- `BREVO_SENDER_EMAIL`: Required sender email. This should be verified in Brevo.
- `BREVO_SENDER_NAME`: Optional sender display name.
- `SALES_EMAIL_TO`: Default recipient for `sales-agent.py`.
- `SALES_EMAIL_TO_NAME`: Optional recipient name for `sales-agent.py`.
- `PUSHOVER_USER`: Optional Pushover user key.
- `PUSHOVER_TOKEN`: Optional Pushover app token.

## Dependencies

Core packages for the root scripts are declared in `pyproject.toml`:

- `openai-agents` for agent orchestration, tools, tracing, and web search.
- `gradio` for browser-based demos.
- `brevo-python` for transactional email.
- `dotenv` for local environment loading.
- `pypdf` for extracting text from resume and LinkedIn PDFs.

The CrewAI projects depend on `crewai[tools]` and are installed from their own
`pyproject.toml` files.

Sync the root project with:

```bash
uv sync
```

## Git and Security Notes

This project is set up to keep local and sensitive files out of git:

- `.env` is ignored.
- `.venv/` is ignored.
- `.gradio/` is ignored.
- `__pycache__/` and Python bytecode are ignored.

Do not commit real API keys, personal certificates, or production recipient
lists. Keep those in environment variables or a secret manager.

## Troubleshooting

### `Unknown tool type: <class 'method'>`

The Agents SDK expects supported tool objects, such as a function decorated with
`@function_tool`. Avoid passing bound instance methods directly in `tools=[...]`.

### `'function' object has no attribute 'get_trace_id'`

`trace` imported from `agents` is a context manager function. Use:

```python
with trace("Research Manager"):
    ...
```

If you need to generate a trace ID manually, import `gen_trace_id` from
`agents.tracing`.

### `ModuleNotFoundError`

Run:

```bash
uv sync
```

If a package is still missing, add it to `pyproject.toml` and sync again.
For a CrewAI project, run `uv sync` inside that project's directory.
