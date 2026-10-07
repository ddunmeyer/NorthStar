# North Star

*Your workday. On course.*

North Star is an employee assistant that answers one question across several company systems. An employee asks in plain English; a coordinator agent hands the request to an HR, developer or IT specialist; and the answer comes back with the records it used and the policy it cites.

Built by **David Dunmeyer** and **Biswa** for the **Agentic AI class at IT Expert System**. Every employee record, policy and request in it is fictional.

![North Star entry screen](docs/screenshots/desktop-00-entry-screen.png)

## What it does

- **One question, several systems.** "Give me my PTO, check my projects, and look for my open tickets" calls all three specialists and returns one answer.
- **Cited policy answers.** Policy questions are answered only from retrieved text, with the document and section shown, for example *Employee Handbook, Section 2*. If no policy covers a question, it says so.
- **Exact numbers.** Totals such as expenses are added up in code, to the cent. The model explains them; it never does the maths.
- **Draft, then confirm.** An agent can draft an IT request, but only the employee can submit it, by clicking Confirm. Confirming twice still creates one record.
- **Your records only.** The signed-in employee is fixed by the app, not by anything typed in chat, so asking for a colleague's expenses is refused.
- **Shows its work.** Each answer lists which specialists were used, the hand-offs between them, and how long it took.

![Three specialists answering one question](docs/screenshots/desktop-04-three-handoffs-hr-developer-it.png)

## How it works

```
Employee (browser or phone)
        |
        v
Streamlit app  ------------------------------  Amazon EC2
        |  employee ID is set by the app
        v
Coordinator agent  (Strands Agents + Amazon Nova 2 Lite on Amazon Bedrock)
        |-- HR specialist ---------> DynamoDB (PTO, expenses)
        |                            Bedrock Knowledge Base (policies, with citations)
        |-- Developer specialist --> DynamoDB (projects, tasks)
        '-- IT specialist ---------> DynamoDB (requests); returns a draft only
        |
        v
Confirm button (app code, not an agent) --> one conditional write to DynamoDB
```

The agents are built with [Strands Agents](https://strandsagents.com), using the agents-as-tools pattern: each specialist is a tool the coordinator can call.

## AWS services

| Service | Used for |
|---|---|
| Amazon Bedrock | Runs the Amazon Nova 2 Lite model behind the coordinator and specialists |
| Amazon Bedrock Knowledge Bases | Retrieves policy text so answers can cite a document and section |
| Amazon Titan Text Embeddings V2 | Turns the policy documents into vectors for search |
| Amazon S3 | Stores the six policy documents |
| Amazon S3 Vectors | Stores the vectors the Knowledge Base searches |
| Amazon DynamoDB | Holds employee records and confirmed requests in one table |
| Amazon EC2 | Hosts the app |
| Elastic IP | Gives the server a fixed public address |
| Amazon VPC security groups | Opens port 80 only; no SSH |
| AWS Systems Manager | Supplies the server image; Session Manager gives shell access without SSH |
| Amazon EventBridge Scheduler | Triggers the daily start and stop of the server |
| AWS Lambda | The functions that start and stop the server |
| Amazon SNS | Emails us when the server starts or stops |
| AWS CloudFormation and AWS SAM | Define the scheduler as code |
| AWS Budgets | A $5 budget with alerts |
| Amazon CloudWatch Logs | Logs from the scheduler's functions |
| AWS IAM and AWS STS | Least-privilege roles for the app and the Knowledge Base; no stored keys |

## Built on our last project

For our previous AWS class project we built an EC2 scheduler: EventBridge Scheduler triggers Lambda functions that start and stop tagged instances at 8:00 AM and 6:00 PM, with email alerts and a budget guard.

North Star reuses it. The demo server carries the same `AutoSchedule=true` tag, so that automation powers it on before class and shuts it down in the evening. The app runs as a service that pulls the latest code from this repository each time it starts, so the daily start is also the deployment step: push to `main`, and the server comes up on the new code the next morning, or after a reboot. Details are in [docs/HOSTING.md](docs/HOSTING.md).

## Run it locally

You need Python 3.11 or later, the AWS CLI signed in (`aws login`), Bedrock model access, a DynamoDB table and a Bedrock Knowledge Base over the documents in `kb/`.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then set NORTHSTAR_TABLE and NORTHSTAR_KB_ID
python scripts/load_data.py --write
streamlit run app.py
```

Sign in with one of the fictional first names in `data/identity/employees.json`, such as `David`.

## Repository layout

| Path | Contents |
|---|---|
| `app.py`, `ui/` | The Streamlit interface, including the phone layout |
| `agents/` | The coordinator and the three specialists |
| `tools/` | The tools each specialist can call, and the Confirm step |
| `data/`, `kb/` | Fictional records and the six policy documents |
| `scripts/` | Data loader and the hosting scripts |
| `evaluation/` | The 30 test cases, the runner and the recorded results |
| `docs/` | Hosting notes and screenshots |

## Limits

- **Sign-in is a classroom shortcut.** Entering a first name selects a fictional profile; it is not authentication.
- **The business systems are simulated.** The HR, project and IT records are fictional data in DynamoDB, not live vendor systems.
- **Not built yet:** the "Open roles" search.
- **Measured, not perfect.** On the 30-case evaluation the app passed 24, with a median response of 2.8 seconds. The six failures and their causes are in [evaluation/README.md](evaluation/README.md).

Next steps would be real sign-in, connecting live systems through MCP, and running the agents on Amazon Bedrock AgentCore.
