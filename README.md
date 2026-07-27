# HR Assist (MCP Server)

Agentic HR assistant that exposes employee, leave, meeting, ticket, and email tools over the Model Context Protocol (MCP). Designed to automate onboarding workflows via an MCP client such as Claude Desktop.

## Sample employees & managers

Use these when creating a new employee (`manager_id` can be ID **or** name):

| ID | Name | Role | Department |
|----|------|------|------------|
| E001 | Sarah Johnson | VP Engineering | Engineering |
| E002 | Michael Chen | VP Product | Product |
| E003 | David Wilson | Engineering Manager | Engineering |
| E006 | Emily Kim | Product Manager | Product |
| E009 | Priya Nair | HR Manager | HR |

Other sample staff: Tony Sharma (E004), James Rodriguez (E005), Carlos Mendez (E007), Lisa Wong (E008), Aisha Khan (E010), Rohan Mehta (E011), Neha Kapoor (E012).

Examples:

```text
add_employee("Riya Shah", manager_id="E001", email="riya.shah@atliq.com")
add_employee("Riya Shah", manager_id="Sarah Johnson")
add_employee("Riya Shah")   # defaults manager to E001
```

Call `list_managers` or `list_employees` tools to see the full directory.

## Features

- Add / look up employees
- Leave balance, apply leave, leave history
- Schedule / list / cancel meetings
- Create and manage IT/HR tickets
- Optional Gmail sending for welcome / manager notifications
- Built-in onboarding prompt: `onboard_new_employee`

## Setup

1. Install [uv](https://docs.astral.sh/uv/) (recommended) or use pip.

2. From this directory:

   ```bash
   uv sync
   ```

   Or with pip:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```

3. Copy env values:

   ```bash
   copy sample.env .env
   ```

   Optional (for real email):

   ```env
   CB_EMAIL=your@gmail.com
   CB_EMAIL_PWD=your_gmail_app_password
   ```

   Leave blank to run without email (send_email will skip and report what it would send).

## Run Streamlit web app (recommended UI)

```bash
uv sync
uv run streamlit run streamlit_app.py
```

Opens at [http://localhost:8501](http://localhost:8501) with tabs for Directory, Onboard, Leave, Tickets, Meetings, and Lookup.

### Deploy to Streamlit Community Cloud

1. Push this folder to a GitHub repo (include `streamlit_app.py` and `requirements.txt`).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select the repo, set **Main file path** to `streamlit_app.py`.
4. Deploy. You’ll get a public URL like `https://your-app.streamlit.app`.

## Run locally (CLI demo, no UI)

```bash
uv run python run_local.py
```

This seeds dummy HR data and runs an onboarding-style flow through the same managers used by the MCP tools.

## Run MCP server

```bash
uv run python server.py
```

stdio transport waits for an MCP client. To inspect tools interactively:

```bash
npx @modelcontextprotocol/inspector uv run python server.py
```

### Claude Desktop config example

Edit Claude Desktop `claude_desktop_config.json` and point `command` / `--directory` at *this* project folder:

```json
{
  "mcpServers": {
    "hr-assist": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\omkar\\Documents\\Project\\AI\\HR Assist (MCP Server)",
        "run",
        "python",
        "server.py"
      ],
      "env": {
        "CB_EMAIL": "YOUR_EMAIL",
        "CB_EMAIL_PWD": "YOUR_APP_PASSWORD"
      }
    }
  }
}
```

## Usage

In Claude Desktop, use the `onboard_new_employee` prompt or ask naturally, for example:

- Onboard a new employee named Riya reporting to Sarah Johnson
- What is Tony Sharma's leave balance?
- Create a laptop ticket for E009

## Project layout

```
server.py          MCP tools + onboarding prompt
run_local.py       Local demo without MCP client
emails.py          SMTP helper
utils.py           Dummy data seeder
hrms/              Employee, leave, meeting, ticket managers + schemas
```
