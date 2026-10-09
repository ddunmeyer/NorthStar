# North Star data update: how to load it

This zip holds the current North Star data, as of October 6, 2026. It adds two things to what you already have:

- **Employee Handbook (NS-HR-001) version 1.1**, with two new sections: Section 5, Dress code, and Section 6, Sick leave.
- **84 more expense records**: three per employee for August and September 2026. The 42 October records are unchanged, so there are now 126.

Everything else in `data/` and `kb/` is the same as before. All of it is fictional.

## The easy way

All of this is already on GitHub. If your copy of the repo is up to date, you don't need the zip:

```bash
git pull origin main
```

Then do steps 2 and 3 below.

## Loading it into your own AWS account

Sign in first with `aws login`, and work from the NorthStar project folder with the virtual environment active.

### 1. Put the files in place (only if you are not using git pull)

Unzip, then copy the `data` and `kb` folders over the ones in your NorthStar folder, replacing the existing files.

### 2. Load the records into DynamoDB

```bash
python scripts/load_data.py            # dry run: should report 261 items, 126 of them EXP
python scripts/load_data.py --write    # loads them into the table named in NORTHSTAR_TABLE
```

The loader overwrites items that have the same key, so it is safe to run on a table that is already loaded. It does not delete anything.

### 3. Update the Knowledge Base

Upload the handbook and its metadata file to the S3 location your Knowledge Base reads from, then sync. Replace the three placeholders with your own values.

```bash
aws s3 cp kb/NS-HR-001.md s3://YOUR-BUCKET/YOUR-PREFIX/NS-HR-001.md
aws s3 cp kb/NS-HR-001.md.metadata.json s3://YOUR-BUCKET/YOUR-PREFIX/NS-HR-001.md.metadata.json
aws bedrock-agent start-ingestion-job --knowledge-base-id YOUR-KB-ID --data-source-id YOUR-DATA-SOURCE-ID
```

You can also do the sync in the console: Amazon Bedrock, Knowledge Bases, your knowledge base, select the data source, Sync.

### 4. Check it worked

Run the app and ask:

- "Can I wear jeans on Friday?" It should say yes.
- "How many sick days do I get a year?" It should say 40 hours and cite Employee Handbook (NS-HR-001), Section 6.
- "Summarize my September 2026 expenses." As David, it should total $606.65.

## One thing to know

The code on `main` also changed: the policy search now returns all six documents, there is a new job search tool, and incidents now ask for impact. Those come from `git pull`, not from this zip. Without them the new policy sections may not be found reliably.
