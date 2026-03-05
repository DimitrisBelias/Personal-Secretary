# 🤖 University Secretary Bot

**A Telegram bot that manages university assignments, labs, and projects through an interactive chat interface backed by Notion databases.**

Built as a personal productivity tool to streamline academic task management — add, track, edit, and monitor deadlines for all coursework from a single Telegram conversation.

---

## Overview

Managing university work across multiple courses, assignments, labs, and projects gets messy fast. This bot acts as a personal secretary: you interact with it through Telegram's inline buttons, and it syncs everything to structured Notion databases behind the scenes.

No more switching between apps or forgetting deadlines — just open Telegram and tap.

---

## Features

### Task Management
- **Add** assignments, labs, projects, and courses through guided conversation flows
- **List** all items by category with real-time status indicators
- **Edit** due dates, course associations, and notes inline
- **Delete** items with confirmation prompts
- **Status tracking** — toggle between Not Started ⚪, In Progress 🔵, and Done ✅

### Smart Scheduling
- **Upcoming view** — see everything due in the next 7, 14, or 30 days across all categories
- **Quick date picker** — choose Today, Tomorrow, Next Week, or enter a custom date
- **Course selector** — dynamically pulls your courses from Notion so you never mistype a code

### Architecture
- **Telegram Bot API** with `python-telegram-bot` — full `ConversationHandler` state machine for multi-step flows
- **Notion API** via `notion-client` — CRUD operations across 4 linked databases
- **Cloud-deployed** on Oracle Cloud / Render with a built-in health check server

---

## How It Works

```
┌──────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Telegram    │◀───────▶│   Bot Server     │◀───────▶│   Notion API    │
│   (User)      │  Inline │  (Python)        │  REST   │                 │
│               │ Buttons │                  │         │  ┌───────────┐  │
│  /start       │         │  ConversationHandler       │  │Assignments│  │
│  ➕ Add       │         │  State Machine   │         │  │Labs       │  │
│  📋 List      │         │                  │         │  │Projects   │  │
│  📅 Upcoming  │         │  notion_service  │────────▶│  │Courses    │  │
└──────────────┘         └──────────────────┘         │  └───────────┘  │
                                                       └─────────────────┘
```

The bot uses a **finite state machine** (`ConversationHandler`) with 20+ states to manage complex multi-step flows like adding an assignment (name → course → date → notes → confirm). Each state handles both button callbacks and text input, with back navigation at every step.

---

## Project Structure

```
telegram-notion-bot/
├── src/
│   ├── bot.py              # Main bot logic, conversation handler, all UI flows
│   ├── config.py           # Environment variable loader with validation
│   └── notion_service.py   # Notion API wrapper — all CRUD operations
├── .env.example            # Template for required environment variables
├── render.yaml             # Render.com deployment configuration
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Bot Framework | `python-telegram-bot` 21.0 |
| Database | Notion API via `notion-client` 2.2.1 |
| Language | Python 3.13 |
| Deployment | Oracle Cloud / Render (worker service) |
| Config | `python-dotenv` for environment management |

---

## Notion Database Schema

The bot expects 4 Notion databases with these properties:

**Assignments / Labs / Projects**
| Property | Type | Description |
|---|---|---|
| Name | Title | Item name |
| Course Code | Rich Text | Associated course (e.g., "PLH211") |
| Due Date | Date | Deadline |
| Notes | Rich Text | Optional notes |
| status | Status | Not started / In progress / Done |

Labs additionally have a **Description** (Rich Text) field.

**Courses**
| Property | Type | Description |
|---|---|---|
| Name | Title | Course name |
| Course Code | Rich Text | Course code (e.g., "PHY202") |
| Semester | Number | Semester number |
| Professor | Rich Text | Instructor name |
| ECTS | Number | Credit hours |

---

## Setup

### 1. Create a Telegram Bot
- Message [@BotFather](https://t.me/BotFather) on Telegram
- Use `/newbot` and follow the prompts
- Save the bot token

### 2. Set Up Notion
- Create a [Notion integration](https://www.notion.so/my-integrations)
- Create the 4 databases (Assignments, Labs, Projects, Courses) with the schemas above
- Share each database with your integration
- Copy each database ID from the URL

### 3. Configure Environment
```bash
cp .env.example .env
```

Fill in your `.env`:
```
TELEGRAM_BOT_TOKEN=your_token_here
NOTION_TOKEN=your_notion_secret_here
ASSIGNMENTS_DB_ID=your_db_id
LABS_DB_ID=your_db_id
PROJECTS_DB_ID=your_db_id
COURSES_DB_ID=your_db_id
```

### 4. Run
```bash
pip install -r requirements.txt
cd src
python bot.py
```

---

## Deployment

The project includes a `render.yaml` for one-click deployment to Render as a worker service. A built-in HTTP health check server keeps the service alive on platforms that require an open port.

---

## Key Design Decisions

- **Button-first UI** — No command memorization; everything is tappable through inline keyboards
- **State machine architecture** — `ConversationHandler` with explicit states prevents invalid flows and supports back-navigation at every step
- **Service layer separation** — `notion_service.py` isolates all API logic; swapping to a different backend would only require changing this file
- **Graceful error handling** — Every Notion API call is wrapped in try/catch with user-friendly error messages
- **Dynamic course loading** — Courses are fetched live from Notion for selection buttons, keeping the bot in sync with your actual course list

---

## License

Personal project — built for everyday use managing coursework at TUC.
