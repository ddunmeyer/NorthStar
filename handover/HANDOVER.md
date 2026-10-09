# North Star: handover for a new Claude chat

Paste or upload this file at the start of a new chat. It contains everything needed to continue guiding the build.

## How we want to work

- David and Biswa are building this themselves on **Biswa's Mac**, in the VS Code terminal and the AWS console.
- **One step at a time.** Give one step, a one-line reason, and what to report back. Wait for the result before the next step.
- **Keep answers concise.** A few lines per step.
- We are learning as we go to build confidence for an AWS certification, so tie each step to the AWS concept behind it.
- Do not write large amounts of code unasked. Do not assume a step worked; ask for the output.

## The project

**North Star** is an enterprise employee assistant for an agentic AI class. An employee asks a question in a chat page; a coordinator agent routes it to an HR, developer or IT specialist, which looks up records, cites the policy the answer came from, and drafts requests the employee must confirm. Tagline: "Your workday. On course."

- **Team:** David Dunmeyer and Biswa (two people, accepted by the instructor).
- **Presentation:** Saturday October 10, 2026, 9:00 AM. 15 minutes, live demo.
- **Repo:** https://github.com/ddunmeyer/NorthStar (both have push access)
- **AWS:** Region `us-east-1`. Biswa signs in as IAM user `biswalexuser`.
- All employee records, policies and requests are fictional.

### What the class grades

Scope versus complexity, working functionality, clean design, integration of external APIs or databases, presentation and demo (including edge cases), innovation, and teamwork (balanced commits in GitHub).

Deliverables: GitHub repo with README, architecture slide deck, 15-minute demo, a plan with milestones and owners, and progress updates.

## Architecture

```
User types in the Streamlit chat page
        |  message + employee ID (set by the app, never by the model)
        v
Strands coordinator agent (Amazon Nova 2 Lite on Bedrock)
        |  picks a specialist (specialists are exposed to it as tools)
        |-- HR agent ---------> DynamoDB (PTO, expenses, jobs) + Knowledge Base (policies)
        |-- Developer agent --> DynamoDB (projects, tasks)
        '-- IT agent ---------> DynamoDB (requests); returns a DRAFT only
        v
Streamlit shows the answer, source citations and result cards
        |  user clicks Confirm on a draft
        v
App code (not an agent) writes the record to DynamoDB once (conditional write)
```

| Piece | Choice |
|---|---|
| Interface | Streamlit (dark "midnight" theme; sidebar, three stat tiles, four quick-prompt buttons, chat with citation chips) |
| Agents | Strands Agents: coordinator + HR, developer and IT specialists (agents-as-tools pattern) |
| Model | `us.amazon.nova-2-lite-v1:0` |
| Policy answers | Six policy documents in S3 -> Bedrock Knowledge Base -> cited answers |
| Records and writes | DynamoDB, one table |
| Sign-in | First-name entry (demo only, not real authentication) |

Two design rules:
1. The model never does the maths and never invents a policy. Totals are calculated in Python; policy answers must come from retrieved text with a citation.
2. An agent can draft, but only a person can confirm. The confirm step is application code.

**Cut from scope:** Lex, voice, Cognito, manager approvals, memory, AgentCore. AgentCore, real sign-in and MCP connections go on the "next steps" slide. Bedrock Guardrails is a late add only if time allows.

## Tools each specialist gets

| Tool | Input | Rule |
|---|---|---|
| HR: `get_my_pto` | none | Own balance only |
| HR: `summarize_my_expenses` | month (required), optional status | Totals in integer cents by currency and status |
| HR: `search_jobs` | title / location / department | Open requisitions only |
| HR: `search_policies` | question | Returns retrieved text plus source; no invented policy |
| DEV: `get_my_projects` | none | Only projects the employee is a member of |
| DEV: `get_my_tasks` | optional project key | Deny a project the employee isn't in |
| IT: `get_my_it_requests` | optional type | Own incidents, access requests and changes |
| IT: `draft_it_request` | type + details | Returns a draft or the missing fields; never writes |
| APP: `confirm_request` | draft ID | Not an agent tool; one DynamoDB record per draft |

## DynamoDB table design

Table `northstar`, partition key `pk` (String), sort key `sk` (String), on-demand capacity.

| pk | sk | Holds |
|---|---|---|
| `DIRECTORY` | first name, lower case | employee ID lookup for first-name entry |
| `EMP#<id>` | `PROFILE` | name, department, title, manager |
| `EMP#<id>` | `PTO` | available hours, approved upcoming hours |
| `EMP#<id>` | `LEAVE#<id>` | leave requests |
| `EMP#<id>` | `EXP#<yyyy-mm>#<id>` | expenses (so one month is one query) |
| `EMP#<id>` | `ITREQ#<number>` | incidents, access requests, changes |
| `PROJECTS` | project key | project name and member list |
| `ISSUES#<project>` | issue key | Jira-style tasks |
| `CATALOG` | `ITEM#<code>` or `SERVICE#<name>` | access catalog and services |
| `JOBS` | requisition ID | job requisitions |

Confirmed requests are written with the condition `attribute_not_exists(pk)`, so confirming the same draft twice creates one record.

## Demo data (must match these numbers)

- 14 employees (E001 David ... E014 Tabitha), 14 PTO balances, 14 leave requests, 42 expenses, 22 tasks, 42 IT requests.
- **David (E001):** 96 PTO hours available, 16 approved upcoming hours already reflected.
- **David's October 2026 expenses:** USD 842.50 total = 520.00 paid + 247.50 approved + 75.00 pending.
- **David's tasks:** NST-101 and NST-102, both need access item `VPN-DEV`.
- **David's existing request:** `RITM000101`, VPN-DEV, status "Pending approval".
- David is not a member of project `FIN` (used for the permission-denial demo).
- Handbook `NS-HR-001` Section 2 says PTO carryover is capped at 40 hours.

Six policy documents: NS-HR-001 Employee Handbook, NS-FIN-001 Travel and Expense, NS-IT-001 IT Support, NS-SEC-001 Access Request, NS-OPS-001 Change Management, NS-HR-002 Internal Mobility and Jobs.

David has a data generator script and a checker script on his machine (not yet pushed) that produce exactly this data in this key layout. Ask him to push them rather than writing data by hand.

## Repo layout (already pushed)

```
app.py                  Streamlit entry point (placeholder page)
agents/                 coordinator, hr_agent, developer_agent, it_agent (placeholders)
tools/                  hr_tools, developer_tools, it_tools, policy_search, confirm (placeholders)
data/  kb/  tests/  evaluation/  scripts/  docs/
.streamlit/config.toml  theme colours
.env.example            settings template
requirements.txt        strands-agents, streamlit, boto3, botocore[crt], pytest
```

The Python files are placeholders with a one-line description and no logic.

## Progress

| Step | What | Status |
|---|---|---|
| 1 | Confirm IAM identity (`biswalexuser`) and Region (`us-east-1`) in the console | Done |
| 2 | Nova 2 Lite answers in the Bedrock playground | Done |
| 3 | AWS CLI installed on the Mac (2.37.9), `aws login`, `aws sts get-caller-identity` works locally | Done |
| 4 | Python virtual environment and `pip install -r requirements.txt` | Done |
| 5 | `scripts/hello_agent.py`: a Strands agent with one tool answered "96 hours" | Done |
| 6 | Create DynamoDB table `northstar` (`pk`, `sk`, on-demand) in the console | **In progress** |

## Remaining steps

7. Generate the fixture data, run the checker, load it into DynamoDB, and query David's records.
8. Write the HR tools so they read from DynamoDB (`get_my_pto`, `summarize_my_expenses`).
9. Build the HR specialist agent with those tools.
10. Add the developer and IT tools and their specialist agents.
11. Build the coordinator that calls the three specialists as tools. Test the flagship question: "Show my Jira tasks and help me get the access I need."
12. Create an S3 bucket, upload the six policy documents, create the Bedrock Knowledge Base and sync it.
13. Write `search_policies` so answers carry a citation (document, section).
14. Build the Streamlit page: first-name entry, tiles, quick prompts, chat, citations.
15. Add the draft and Confirm flow with the conditional write.
16. Run the 30 evaluation cases; record success count, median and p95 latency.
17. README, slides, backup recording, two rehearsals. Feature freeze Thursday October 8, 8 PM.

**Fallbacks:** if the Knowledge Base stalls, use a local search over the same six documents and label it clearly as not live retrieval. If the coordinator is unreliable, route to specialists directly and say so.

## Reminders

- Never commit `.env`, `.venv` or AWS credentials. Credentials come from `aws login`, not from code.
- Commit after each working step. Both names should appear in the history; when working together on one machine, add `Co-authored-by: David Dunmeyer <email on his GitHub account>` to the commit message.
- Everything goes in `us-east-1`.
- Tear down the Knowledge Base, S3 bucket and table after the demo to stop charges.
