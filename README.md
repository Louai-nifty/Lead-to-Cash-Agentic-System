# Lead-to-Cash Agentic System

An autonomous sales pipeline that takes a lead from initial contact through to paid invoice, with no manual data entry and human-in-the-loop checkpoints at the right moments.

Built with LangGraph as the orchestration layer, FastAPI as the HTTP surface, and Supabase as the persistence backend. The system is designed to run unattended: it ingests leads, enriches them, scores and routes them to the right sales rep, generates proposals, handles contract signing, and creates and sends invoices -- all through a state machine that pauses for manager approval on high-value deals.

---

## What it does

The pipeline has seven stages, each one a node in a LangGraph `StateGraph`:

```
Enrichment -> Scoring -> Assignment -> [Approval Gate] -> Proposal -> Contract -> Invoice
```

1. **Enrichment** -- Pulls company data (industry, headcount, revenue, location) via the Hunter.io API using the lead's domain.
2. **Scoring** -- Applies a weighted scoring model across company size, industry fit, and lead source. Produces a numeric score and a priority tier (low / mid / high).
3. **Assignment** -- Routes the lead to a Junior or Senior rep based on the score, using a least-loaded distribution (the rep with the fewest active leads gets the assignment). Leads scoring below threshold are rejected outright.
4. **Approval Gate** -- Deals estimated above $10,000 are held for manager approval via an interactive Slack message with Approve / Reject buttons. The graph suspends here (`interrupt_before`) and resumes when the Slack webhook fires back.
5. **Proposal** -- Selects a template (Starter / Professional / Enterprise) based on company headcount, renders it with lead-specific data via Jinja2, converts to PDF with WeasyPrint, and uploads to Supabase Storage. The assigned rep gets a Slack notification with Send Now / Review buttons.
6. **Contract** -- Generates a Professional Services Agreement PDF, uploads it to OpenSign for dual-party signature (lead + rep), and emails the signing link to the lead. Tracks viewed / signed / completed / expired / declined states via the OpenSign webhook.
7. **Invoice & Payment** -- Creates a PayPal invoice with a 14-day payment term, sends it to the lead, and listens for PayPal webhooks (paid / cancelled / refunded). On payment, the lead is marked as a client and the team gets notified on Slack.

---

## Architecture

```
lead-to-cash/
├── agent/                  # LangGraph state machine
│   ├── graph.py            # StateGraph definition and edge wiring
│   ├── state.py            # Pydantic state schema (AgentState)
│   ├── nodes/              # One file per pipeline stage
│   └── tools/              # LangChain @tool wrappers around external APIs
├── clients/                # Thin async HTTP clients for third-party services
│   ├── hunter_client.py    # Company enrichment
│   ├── opensign_client.py  # Document signing
│   ├── paypal_client.py    # Invoicing and payments
│   └── slack_client.py     # Notifications and interactive approvals
├── routers/                # FastAPI route handlers
│   ├── webhooks.py         # Inbound webhooks (Tally, Slack, OpenSign, PayPal)
│   └── triggers.py         # Gmail IMAP polling scheduler
├── services/               # Business logic (scoring, routing, proposal generation)
├── database/               # Supabase client singleton
├── models/                 # Pydantic request schemas
├── templates/              # Jinja2 HTML proposal templates
└── utils/                  # Logging config, PayPal auth helper
```

### State management

The graph uses `AsyncSqliteSaver` as a checkpointer, which means every state transition is persisted to disk. If the process restarts mid-pipeline, it picks up where it left off. The `thread_id` for each graph invocation is the lead's database ID, so every lead has an independent execution trace.

### Human-in-the-loop

The graph compiles with `interrupt_before=["approval_handler"]`. When a deal needs manager sign-off, the approval node calls `interrupt()`, which suspends the graph and returns control to FastAPI. The Slack approval webhook then calls `agent.aupdate_state()` followed by `agent.ainvoke()` to resume execution with the manager's decision injected into the state.

The same pattern applies to the proposal review step: the graph pauses after proposal generation and resumes when the rep clicks "Send Now" in Slack.

---

## Tech stack

| Layer | Choice |
|---|---|
| API framework | FastAPI |
| Agent orchestration | LangGraph (LangChain ecosystem) |
| Database & storage | Supabase (Postgres + Storage) |
| State persistence | SQLite (via LangGraph checkpoint) |
| Company enrichment | Hunter.io API |
| Document signing | OpenSign API |
| Invoicing & payments | PayPal Invoicing API |
| Notifications | Slack SDK (async) |
| Email delivery | SMTP (via `smtplib`) |
| PDF generation | WeasyPrint, pdfkit |
| Templating | Jinja2 |
| Lead capture | Tally Forms webhook, Gmail IMAP polling |
| Containerization | Docker, docker-compose |

---

## Setup

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Accounts: Supabase, Hunter.io, OpenSign, PayPal (sandbox or live), Slack (with bot tokens), SMTP provider

### Environment variables

Create a `.env` file in the project root:

```env
# Lead enrichment
Hunter_API_Key=your_hunter_key
Apollo_API_Key=your_apollo_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Slack (one bot token per function)
Slack_Approval_Bot_Token=xoxb-...
Slack_Proposal_Bot_Token=xoxb-...
Slack_Contract_Bot_Token=xoxb-...
Slack_Invoice_Bot_Token=xoxb-...
Assignment_Channel_ID=C0...
Approval_Channel_ID=C0...
Proposals_Channel_ID=C0...
Contracts_Channel_ID=C0...
Invoices_Channel_ID=C0...
Payments_Channel_ID=C0...

# PayPal
Paypal_Client_ID=your_client_id
Paypal_Secret=your_secret
Paypal_Base_Url=https://api-m.sandbox.paypal.com
Paypal_Webhook_ID=your_webhook_id

# OpenSign
Sandbox_API_Token=your_opensign_token
OPENSIGN_BASE_URL=https://app.opensignlabs.com/api/v1

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@yourdomain.com

# Company
Company_Email=sales@yourdomain.com
App_Domain=https://yourdomain.com

# Gmail polling (optional lead source)
GMAIL_EMAIL=leads@yourdomain.com
GMAIL_APP_PASSWORD=your_gmail_app_password
```

### Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Run with Docker

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`. The interactive docs are at `/docs`.

---

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/webhook/tally-form` | Receive lead from Tally Forms |
| `POST` | `/webhook/slack-approval` | Manager approve/reject decision |
| `POST` | `/slack/proposal-action` | Rep send/review proposal |
| `POST` | `/contract/sign/{lead_id}` | Lead triggers contract signing |
| `POST` | `/webhook/opensign-listener` | OpenSign signing events |
| `POST` | `/webhook/paypal-payment` | PayPal invoice payment events |
| `GET` | `/proposals/view/{filename}` | Serve proposal HTML from storage |

---

## Lead sources

The system accepts leads from two channels:

- **Tally Forms** -- A webhook fires on form submission, the router extracts name / email / company / role / message, inserts into Supabase, and kicks off the agent.
- **Gmail polling** -- An APScheduler job runs every 5 minutes, connects to a Gmail inbox via IMAP, extracts unread emails, and feeds them into the same pipeline.

Both paths converge on the same LangGraph invocation with `lead_email` and `lead_domain` as entry inputs.

---

## How the scoring model works

The scoring function computes a weighted composite:

```
final_score = (size_score * 0.40) + (industry_score * 0.35) + (source_score * 0.25)
```

- **Size score** (0-50): Based on employee headcount bands, from solo shops to 1000+ enterprises.
- **Industry score** (0-30): Primary industries (HR, Real Estate) score higher than secondary ones (IT Services, Business Consulting).
- **Source score** (0-15): Tally form submissions score higher than cold email, since inbound intent signals stronger fit.

The resulting score determines routing: below 50 is rejected, 50-79 goes to a Junior rep, 80+ goes to a Senior rep.

---

## Deal size estimation

For leads routed to Senior reps, the system estimates deal size from headcount:

| Headcount | Estimated deal size |
|---|---|
| < 50 | $2,000 |
| 50 - 199 | $5,000 |
| 200 - 999 | $10,000 |
| 1,000+ | $15,000 |

Deals at or above $10,000 trigger the manager approval gate before proceeding.

---

## Database schema (Supabase)

The system expects the following tables:

- **Leads** -- `lead_id`, `lead_name`, `email`, `phone`, `company`, `role`, `source`, `message`, `status`, `lead_score`, `priority`, `assigned_rep_id`, and enrichment fields (`industry`, `size`, `revenue`, `location`)
- **Users** -- `id`, `name`, `email`, `role` (Junior_Rep / Senior_Rep / Manager / accountant), `leads_assigned_atm`
- **proposals** -- `lead_id`, `assigned_to`, `template_name`, `pdf_url`, `status`, `sent_at`
- **contracts** -- `lead_id`, `opensign_id`, `status`, `lead_signer_id`, `rep_signer_id`, `lead_sign_url`, `rep_sign_url`, `sent_at`, `lead_signed_at`, `rep_signed_at`, `contract_data`
- **invoices** -- `invoice_id`, `lead_id`, `amount`, `currency`, `status`, `url`, `due_date`, `created_at`, `updated_at`
- **payments** -- `invoice_id`, `lead_id`, `amount`, `paid_at`

---

## Slack bot setup

The system uses four separate Slack bot tokens, one per notification domain (approvals, proposals, contracts, invoices). Each bot posts to its own channel. The approval and proposal bots need interactive block support (Approve/Reject, Send Now/Review buttons), and their corresponding webhook endpoints must be configured in the Slack app settings:

- `/webhook/slack-approval` for approval actions
- `/slack/proposal-action` for proposal actions

---

## License

MIT
