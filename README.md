# AI Email Reading Agent

## Overview
AI Email Reading Agent is an end-to-end email triage system for a B2B SaaS workflow.  
It ingests emails (mock dataset for now), classifies them with OpenAI, prevents duplicate processing with Neon PostgreSQL, and shows only important notifications in a React dashboard.

It is optimized to prioritize:
- payment/billing issues
- server/technical incidents
- client complaints and urgent requests

And deprioritize:
- newsletters
- promotions
- spam

## Architecture
```text
n8n Scheduler -> FastAPI Agent -> OpenAI API
                    |
                    v
              Neon PostgreSQL (dedup)
                    |
                    v
           React Dashboard (polling)
```

### n8n Workflow
![n8n Workflow](https://i.ibb.co.com/fY7FLR19/image.png)

### Dashboard Preview
![Dashboard Preview](https://i.ibb.co.com/SpgS5ss/image.png)

## Tech Stack
| Component | Technology | Purpose |
|---|---|---|
| Workflow Automation | n8n | Schedule/trigger polling workflows |
| Backend API | FastAPI (Python) | Poll emails, classify, manage notifications |
| AI Classification | OpenAI (`gpt-4o-mini`) | Importance, priority, category, reason |
| Dedup Storage | Neon PostgreSQL + `psycopg2` | Persist processed email IDs |
| Frontend | React + Vite + Tailwind CSS | Notification dashboard UI |
| Local Orchestration | Docker Compose | Local multi-service development |

## Setup & Running
### Prerequisites
- Docker + Docker Compose
- Neon account (free tier is enough)
- OpenAI API key

### Environment Variables
Create `.env` in project root.

| Variable | Description | Example |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key used for classification | `sk-...` |
| `NEON_DATABASE_URL` | PostgreSQL connection string for Neon | `postgresql://user:pass@...` |
| `POLL_INTERVAL_SECONDS` | Poll interval reference for automation | `120` |
| `MOCK_MODE` | Toggle mock-mode behavior | `true` |
| `MOCK_EMAIL_PATH` | Optional custom path for mock email JSON | `mock_data/emails.json` |
| `VITE_API_BASE_URL` | Dashboard API base URL (frontend env) | `http://localhost:8000` |

### Run With Docker (Local)
```bash
cp .env.example .env
# fill in your values
docker compose up --build
```

Access points:
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- n8n: http://localhost:5678

### Import n8n Workflow
1. Open n8n at `http://localhost:5678`.
2. Click `Import from File`.
3. Select `n8n/workflow.json` from this repo.
4. Review node credentials/settings.
5. Activate the workflow.

## How The AI Works
Classification is implemented in `agent/classifier.py` and uses:
- model: `gpt-4o-mini`
- JSON mode: `response_format={"type":"json_object"}`

The system prompt enforces B2B SaaS triage rules and a strict output schema.

Output schema:
- `important` (boolean)
- `priority` (`HIGH`, `MEDIUM`, `LOW`)
- `category` (normalized string)
- `reason` (single-sentence explanation)

Priority rules:
- `HIGH`: important + urgent / financial / technical
- `MEDIUM`: important but not urgent
- `LOW`: not important

Common categories:
- `PAYMENT_ISSUE`
- `SERVER_DOWN`
- `CLIENT_COMPLAINT`
- `URGENT_REQUEST`
- `GENERAL_INQUIRY`
- `MEETING_REQUEST`
- `NEWSLETTER`
- `SPAM`
- `CLASSIFICATION_ERROR` (fallback)

Reliability behavior:
- retry once on OpenAI failure
- if retry fails, return fallback:
  - `important=false`
  - `priority=LOW`
  - `category=CLASSIFICATION_ERROR`
  - safe error reason string

## How The Dashboard Works
The dashboard uses `useNotifications` polling logic:
- fetches `/api/notifications` every 10 seconds
- fetches `/api/notifications/stats` on the same interval
- supports manual `Trigger Poll` via `POST /api/trigger-poll`
- supports dismiss action via `DELETE /api/notifications/{email_id}`
- supports client-side filtering by priority and category

Notifications are stored in-memory in the API process and displayed as cards in the React UI.

## Mock Email Dataset
`mock_data/emails.json` contains 30 sample emails with realistic bodies and timestamps.

Current distribution:
- 5 payment/billing issues
- 5 client complaints/urgent requests
- 4 server/technical alerts
- 4 general business inquiries
- 4 meeting/calendar requests
- 4 newsletters/marketing
- 4 spam/promotional

To add more:
1. Add new objects to `mock_data/emails.json`.
2. Keep required fields: `id`, `from`, `subject`, `body`, `received_at`.
3. Ensure each `id` is unique.

## API Endpoints
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Service status + notification count + DB readiness |
| `POST` | `/api/trigger-poll` | Poll, classify, store processed IDs, update notifications |
| `GET` | `/api/notifications` | Return current in-memory notifications |
| `GET` | `/api/notifications/stats` | Aggregate stats by priority/category |
| `DELETE` | `/api/notifications/{email_id}` | Dismiss one notification |

## Limitations
- In-memory notifications reset on agent restart.
- No authentication on dashboard/API endpoints.
- Mock mode only (no real Gmail/IMAP ingestion yet).

## Deployment (Vercel)
### Dashboard
- Deploy `dashboard/` to Vercel.
- Set `VITE_API_BASE_URL` to your deployed backend URL.

### Agent (Backend)
- Deploy repository root with `api/index.py` as entrypoint.
- Set environment variables in Vercel:
  - `OPENAI_API_KEY`
  - `NEON_DATABASE_URL`
  - optional `MOCK_EMAIL_PATH`

### Notes
- Docker setup in this repository is for local development/testing only.
- Production target is Vercel for both frontend and backend.
