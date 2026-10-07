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

## Results, October 6, 2026

| Run | Passed | Median | 95th percentile |
|---|---|---|---|
| First run | 24 of 30 | 2.79 s | 4.9 s |
| After fixes | **30 of 30** | 2.8 s | 4.47 s |
| After adding dress code, sick leave and two more months of expenses (recorded in `RESULTS.md`) | **30 of 30** | 2.73 s | 4.85 s |

Model: Amazon Nova 2 Lite. The final run used about 197,000 input tokens and 4,800 output tokens across all 30 cases.

### What the first run found, and what we changed

| Case | What happened | Fix |
|---|---|---|
| T04 "Check my PTO and explain carryover." | Said no policy covers carryover. The Knowledge Base returned its top three documents and the handbook was not among them for that wording. | Retrieve all six documents, best first; ask the Knowledge Base a full question; keep citations intact through the coordinator |
| T08 "How much is approved but unpaid?" | Answered $75.00, the pending amount, instead of $247.50 approved. | The expense tool now returns what each status means, taken from the expense policy |
| T09, T10 open and remote jobs | No job search tool existed. | Added `search_jobs`: open postings only, with requisition IDs |
| T23 "Draft an incident; my VPN fails on login." | Drafted without asking about impact, which the IT Support Policy requires. | Impact is now a required incident field, enforced in the tool |
| T24 "Show E002 expenses." | Showed the signed-in employee's own expenses without saying it could not show E002's. No other employee's data was returned. | The coordinator and HR specialist now refuse plainly and show nothing in its place |

A later run also caught the HR specialist asking "which month?" on T07. The expense tool now defaults to the current month in code.

### Read this result with care

- **Answers vary between runs.** The same question can be worded differently each time, and across four full runs during fixing a different case failed more than once. Thirty of thirty is one clean run, not a guarantee.
- **Some rules were corrected, not just the app.** Four checks rejected answers that were right but phrased differently: "Nothing has been submitted yet" counted as claiming submission; a citation written as "(NS-FIN-001) ... covered in Section 2" was not recognised; and two refusal and "no policy" phrasings were missed. Each was fixed after reading the answer, and T24 was made stricter at the same time: it now fails if any amount is shown.
- **The cases cover one employee.** All 30 sign in as E001.
