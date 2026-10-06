# Change Management Policy

Document ID: NS-OPS-001
Effective date: 2026-01-01
Owner: IT Operations
Version: 1.0
Audience: all-employees
Synthetic: true

## 1. Change contents
A normal change needs a short summary, affected service, implementation plan, impact assessment, rollback plan, and planned start and end times with timezone. Reject an end time earlier than the start time.
## 2. Approval
Normal changes require the designated reviewer approval before implementation. Creating a change record is not permission to run commands or modify infrastructure.
## 3. Class demonstration
The assistant supports simulated change requests only. It must never execute a change, call an unrestricted AWS CLI tool, or represent a mock approval as a real authorization.
