# North Star: demo narrative (15 minutes)

**The idea in one line:** an employee shouldn't need to know which system holds the answer. They ask once, and North Star finds the way.

Written to be spoken. It assumes the build works as planned; fill in the two bracketed numbers from the evaluation run.

## 1. The hook (0:00-1:30) - David

> "It's Monday, 8:55. I've got one question: can I take Friday off? To answer it I need the HR system for my balance, the handbook for the rules, and my task board to see what's due. Three logins, three tabs, and a 40-page PDF.
>
> Then I find out I can't start my task anyway, because I don't have VPN access. That's a fourth system and a form I've never filled in.
>
> None of that is hard. It's just scattered. Every company has the answers; nobody has the map.
>
> So we built one. This is North Star."

*Sign in as David. The dashboard appears: 96 hours of PTO, $842.50 in October expenses, 2 assigned tasks.*

> "Before I've typed anything, it already knows what my day looks like."

## 2. What's behind the screen (1:30-4:00) - Biswa

> "North Star isn't one chatbot. It's a team.
>
> A coordinator agent listens to the request and decides who should handle it. Behind it are three specialists: one for HR, one for developer work, one for IT. Each can only touch its own tools, and each can only see the signed-in employee's records.
>
> It's built with Strands and runs on Amazon Bedrock with the Nova model. Company policies live in a Bedrock Knowledge Base, and the records live in DynamoDB.
>
> Two rules shaped every decision. First: the model never does the maths and never invents a policy. Second: an agent can draft, but only a person can confirm."

## 3. The morning, live (4:00-11:30) - David drives, Biswa narrates

**Scene one: the question that started it.**
*Type: "How much PTO do I have, and what can I carry over?"*

> "Two systems, one answer. The 96 hours came from the HR record. The 40-hour carryover came from the handbook, and here's the citation: Employee Handbook, Section 2. If it can't cite it, it doesn't say it."

**Scene two: the money.**
*Click "Expense summary".*

> "$842.50 for October: $520 paid, $247.50 approved, $75 pending. Those totals were calculated in code, to the cent. The model only explains them. An assistant that guesses at your money is worse than no assistant."

**Scene three: the agents work together.**
*Type: "Show my Jira tasks and help me get the access I need."*

> "Watch the activity line. The coordinator asks the developer agent for my tasks. Both need the dev VPN. So it hands off to the IT agent, which checks my existing requests and finds one already pending.
>
> It didn't file a duplicate. It told me where I stand. Nobody wrote that path in advance. The agents worked it out."

**Scene four: taking action, safely.**
*Type: "I need AWS sandbox access for the NST project through the end of the month."*

> "Now it's drafting. It asks for the one thing it's missing, the business reason, and then shows me the draft. Nothing has been written yet.
>
> I click Confirm, and there's the request number. If I click again, nothing happens: one draft, one record, guaranteed by the database, not by the model's good behaviour."

**Scene five: trying to break it.**
*Type: "Show me Kush's expenses."*

> "Denied. I'm signed in as David, and my identity comes from the application, not from anything I type. I can't talk my way into someone else's records."

*Type: "What's our policy on bringing pets to the office?"*

> "And here it says it doesn't know. There's no pet policy in the knowledge base, so there's no answer. That's the behaviour we wanted most."

## 4. The proof (11:30-13:30) - Biswa

> "We didn't just try it and hope. We wrote 30 test cases: correct answers, exact totals, permission denials, duplicate requests, missing policies, and a simulated outage.
>
> North Star passed [X] of 30. Median response time was [Y] seconds. Here are the ones it failed, and why."

*Show the results slide, including the failures.*

> "What's simulated: the HR, Jira and IT records are fictional, and sign-in is a classroom shortcut, not real authentication. What's real: the agents, the retrieval, the citations, the permission checks and the confirmed writes."

## 5. The close (13:30-15:00) - David

> "Go back to Monday, 8:55. Four systems, three logins, one PDF. With North Star it was four sentences and one click.
>
> Next we'd put real sign-in in front of it, connect the real systems through MCP, and move the agents onto Bedrock AgentCore so it runs as a managed service.
>
> The systems were never the problem. Finding your way between them was. North Star: your workday, on course."

## Delivery notes

- Say the rule before you show it: "an agent can draft, only a person can confirm" lands harder when the audience then watches the Confirm click.
- Pause on the activity line in scene three; don't talk over the hand-off.
- Show the failures. A real number with honest misses is more convincing than a claimed 100%.
- Have the backup recording open in another tab in case Bedrock is slow at 9 AM.
