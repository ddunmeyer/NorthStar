# Hosting North Star on AWS

North Star runs on one small EC2 instance with a fixed public address. The instance is started and stopped by the EC2 Scheduler we built for our previous AWS project.

## Building on the last project

For our previous AWS project we built an EC2 scheduler: Amazon EventBridge Scheduler invokes two Lambda functions, `StartEC2Instances` at 8:00 AM and `StopEC2Instances` at 6:00 PM (America/Chicago). They act on any instance tagged `AutoSchedule=true`, send an email through SNS, and sit behind a $5 budget with alerts.

For North Star we didn't start over. The demo server carries the same `AutoSchedule=true` tag, so the automation from the last project powers it on an hour before our 9:00 AM presentation and shuts it down that evening. The last project became the operations layer for this one, and it is the reason the server costs nothing while nobody is using it.

## What runs where

```
Classmate's phone or laptop
        |  http://<Elastic IP>      (port 80, plain HTTP)
        v
EC2 t3.small "NorthStar-Demo"       tagged AutoSchedule=true
  Streamlit + Strands agents, run as a systemd service
        |  IAM role NorthStarAppRole (no stored keys)
        |-- Amazon Bedrock: Nova 2 Lite
        |-- Bedrock Knowledge Base: the six policy documents
        '-- DynamoDB table: northstar

EventBridge Scheduler --> StartEC2Instances (8:00 AM) / StopEC2Instances (6:00 PM)
        acts on every instance tagged AutoSchedule=true     <-- from the previous project
```

The app is a service, so it starts by itself each morning and pulls the latest `main` from GitHub as it starts.

## Deploy

Sign in with `aws login`, make sure `.env` holds `NORTHSTAR_TABLE` and `NORTHSTAR_KB_ID`, then:

```bash
python scripts/hosting/deploy.py            # dry run: prints the plan, creates nothing
python scripts/hosting/deploy.py --apply    # creates the resources
```

The first boot installs packages and takes about three minutes. The script prints the address and saves the resource IDs to `.northstar-hosting.json` (not committed).

## Remove

```bash
python scripts/hosting/teardown.py --apply
```

This deletes the instance, the Elastic IP, the security group and the IAM role. It leaves the table, the Knowledge Base and the scheduler alone.

## Things to know

- **It is public.** Anyone with the address can open the app, and first-name entry is not real sign-in. All records are fictional. Remove the server after the demo.
- **It is off outside 8:00 AM to 6:00 PM Central.** To keep it on for an evening test, set the instance's `DoNotStop` tag to `true`, and set it back afterwards.
- **Permissions are narrow.** The server's role can call one model, retrieve from one Knowledge Base, and read and write one table. There is no SSH; shell access is through Session Manager.
- **Cost.** About $0.50 a day for the instance while it runs, about $0.12 a day for the Elastic IP, and about half a cent per question asked.
- **The scheduler acts on every tagged instance.** Any other instance tagged `AutoSchedule=true` in the account starts and stops on the same timetable.
