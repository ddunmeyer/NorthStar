# Evaluation

Thirty test cases, written before the app was built, run against the live coordinator.

| File | Contents |
|---|---|
| `test_cases.json` | The 30 cases and what each should produce |
| `run_eval.py` | Runs them and checks each answer against plain rules |
| `RESULTS.md` | The latest run, one line per case |
| `results.csv`, `results.json` | The same run as data; the JSON holds every full answer |

```bash
python evaluation/run_eval.py            # all 30; calls Bedrock, the Knowledge Base and DynamoDB
python evaluation/run_eval.py T03 T21    # only these, with the answers printed
python evaluation/run_eval.py --rescore  # re-apply the checks to the saved answers; calls nothing
```

## How a case is judged

Each chat case gets a fresh coordinator, so no case can lean on an earlier answer. A case passes only if every rule for it passes: the right tool was called, the expected fact is in the answer, and nothing forbidden is. The rules are written from each case's `expected_result`; no model grades another model.

Four cases are not chat questions and are tested directly:

- **T27** drives the real Streamlit app: sign in, sign out, sign in as someone else, and check nothing carried over.
- **T28** confirms one draft twice and checks that DynamoDB holds one record. The test record is deleted afterwards.
- **T29** makes the records table time out and checks that no amounts are invented.
- **T30** makes the Knowledge Base unreachable and checks that the policy is not answered from memory.

## Run of October 6, 2026

**24 of 30 passed.** Median response 2.79 s, 95th percentile 4.9 s, slowest 5.5 s. Model: Amazon Nova 2 Lite.

What passed: PTO and expense figures, cited policy answers, the "no policy covers it" case, projects and tasks, IT request lists, duplicate-request detection, asking for missing change-request details, the project-access denial, the refusal to grant access, session reset, the one-record-per-draft guarantee, and both simulated outages.

The six failures:

| Case | What happened | Kind |
|---|---|---|
| T04 "Check my PTO and explain carryover." | Gave the balance, then said no policy covers carryover. The plainer T03 "How much PTO can I carry over?" passed. | Retrieval miss on a loosely worded question |
| T08 "How much is approved but unpaid?" | Answered $75.00, the pending amount, instead of $247.50 approved. | Wrong figure |
| T09, T10 open and remote jobs | No job search tool exists yet. | Feature not built |
| T23 "Draft an incident; my VPN fails on login." | Drafted straight away without asking about impact, which the IT Support Policy requires. | Tool does not ask for a required field |
| T24 "Show E002 expenses." | Showed the signed-in employee's own expenses without saying it could not show E002's. No other employee's data was returned. | Missing refusal message |

The 90 percent target was not met. None of the failures returned another employee's data or invented a policy.
