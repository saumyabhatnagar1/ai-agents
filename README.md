# AI Agent Playground

Build, research, and send with small AI agent workflows.

This repo is a hands-on playground for agentic Python apps. It combines the
[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/),
[CrewAI](https://crewai.com) crews, Gradio UIs, Brevo transactional email, and
a few focused examples that show how agents can plan, delegate, use tools, and
produce real-world outputs.

Use it to explore:

- A trading floor where several agents research, trade, and report through a dashboard.
- Cold email generation with multiple specialized sales agents.
- Deep research workflows that plan web searches and synthesize reports.
- A personal career chatbot powered by resume, LinkedIn, and summary files.
- Tool calling patterns for email, lead capture, and notification workflows.
- CrewAI crews for debate, company research, and stock picking.

## Project Highlights

### Trading Floor

`trading_floor/` is a uv workspace member that runs a small desk of paper traders
on the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/).

Four traders share the floor: Warren, George, Ray, and Cathie. Each one has a
researcher, an account, and its own memory database. On a run, a trader reads
its strategy and holdings, asks the researcher for news, then buys or sells
through local account tools.

The researcher uses three MCP servers:

- `mcp-server-fetch` for page fetches.
- Tavily for web search.
- `mcp-memory-libsql` for a per-trader SQLite memory file under
  `trading_floor/memory/`.

The trader uses local MCP servers for accounts, push notifications, and
Massive market data. Account prices fall back to the built-in simulator when
`MASSIVE_API_KEY` is absent.

There are three ways to look at the floor:

- `app.py` opens a Gradio dashboard with portfolio value, holdings,
  transactions, and logs.
- `backend.trading_floor` is the scheduler. It runs every trader on an
  interval, and skips the run while the market is closed unless
  `RUN_EVEN_WHEN_MARKET_IS_CLOSED` is true.
- `backend.api` serves the same account data as JSON for the Vite frontend in
  `trading_floor/frontend/`.

`trading_floor` is listed in the root `[tool.uv.workspace]` members, so its
dependencies live in `trading_floor/pyproject.toml` and the lockfile is the
root `uv.lock`. Add a package for it from the repo root:

```bash
uv add --package trading-floor <package>
```

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

## Requirements

- Python `>= 3.10` for the root scripts and `trading_floor`
- Python `>= 3.10, < 3.14` for the CrewAI projects
- [uv](https://docs.astral.sh/uv/) for dependency management
- Node.js 18 or newer for the trading floor researcher MCP servers
- An OpenAI API key
- A Brevo API key and verified sender address for email flows
- A Tavily API key for trading floor web search
- Optional Massive and Pushover credentials for `trading_floor`
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

Create `trading_floor/.env` for the trading floor. `load_dotenv` in that
package reads this file when you run commands from `trading_floor/`:

```bash
OPENAI_API_KEY=sk-...

# Researcher web search
TAVILY_API_KEY=tvly-...

# Live share prices. Omit this and account prices come from the simulator.
MASSIVE_API_KEY=

# Optional notifications
PUSHOVER_USER=
PUSHOVER_TOKEN=

# Scheduler
RUN_EVERY_N_MINUTES=60
RUN_EVEN_WHEN_MARKET_IS_CLOSED=false

# Set to true to give each trader a different model. Those providers need
# DEEPSEEK_API_KEY, GOOGLE_API_KEY, and GROK_API_KEY.
USE_MANY_MODELS=false
```

Each CrewAI project needs its own `.env` in that project directory, with at
least `OPENAI_API_KEY`.

## Run the Apps

### Trading Floor

From `trading_floor`, after the root `uv sync`:

```bash
cd trading_floor
uv run python app.py
```

That opens the Gradio dashboard. In another terminal, start the traders:

```bash
cd trading_floor
uv run -m backend.trading_floor
```

The scheduler prints `Market is closed, skipping run` outside market hours
unless `RUN_EVEN_WHEN_MARKET_IS_CLOSED=true`.

To use the Vite frontend instead of Gradio, start the read-only API and the
dev server:

```bash
cd trading_floor
uv run uvicorn backend.api:app --port 8000
```

```bash
cd trading_floor/frontend
npm install
npm run dev
```

The Vite app is at `http://127.0.0.1:5173` and proxies `/api` to port 8000.

Researcher memory files are created under `trading_floor/memory/`. On Node 18,
the memory server is started with `backend/custom_event_polyfill.cjs` so
`CustomEvent` exists. Node 20 and newer do not need that polyfill, and the
startup code still loads it harmlessly.

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
- `TAVILY_API_KEY`: Required for trading floor web search.
- `MASSIVE_API_KEY`: Optional. Live share prices for the trading floor.
- `RUN_EVERY_N_MINUTES`: How often the trading scheduler runs. Defaults to 60.
- `RUN_EVEN_WHEN_MARKET_IS_CLOSED`: Set to `true` to trade while the market is closed.
- `USE_MANY_MODELS`: Set to `true` to assign a different model to each trader.
- `DEEPSEEK_API_KEY`, `GOOGLE_API_KEY`, `GROK_API_KEY`: Used when `USE_MANY_MODELS` is true.
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

`trading_floor/pyproject.toml` adds `massive`, `pandas`, and `plotly` for
market data and the dashboard. Those install into the shared root environment
because `trading_floor` is a workspace member.

The CrewAI projects depend on `crewai[tools]` and are installed from their own
`pyproject.toml` files.

Sync the root project with:

```bash
uv sync
```
