"""Remove the North Star demo server created by deploy.py.

Dry run by default. Add --apply to delete.

    python scripts/hosting/teardown.py
    python scripts/hosting/teardown.py --apply

Deletes the instance, releases the Elastic IP, and removes the security group and
the IAM role. It leaves the DynamoDB table, the Knowledge Base and the EC2
Scheduler project alone. Add --disable-schedules to switch the start and stop
schedules back off as well.
"""
import argparse
import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

MANIFEST = Path(__file__).resolve().parents[2] / ".northstar-hosting.json"
SCHEDULES = ["EC2-Lab-Start-Schedule", "EC2-Lab-Stop-Schedule"]


def quietly(action, *codes):
    """Run a delete and ignore 'already gone' errors, so teardown can be re-run safely."""
    try:
        action()
    except ClientError as err:
        if err.response["Error"]["Code"] not in codes:
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--apply", action="store_true", help="delete the resources (default is a dry run)")
    parser.add_argument("--disable-schedules", action="store_true", help="also disable the start/stop schedules")
    args = parser.parse_args()

    if not MANIFEST.exists():
        raise SystemExit(f"{MANIFEST.name} not found: nothing recorded to remove.")
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    print(f"Will remove: instance {m['instance_id']}, Elastic IP {m.get('public_ip', '(none)')}, "
          f"security group {m['security_group_id']}, IAM role {m['role']}.")
    if not args.apply:
        print("Dry run only. Nothing was deleted. Add --apply to remove.")
        return

    session = boto3.Session(region_name=m["region"])
    ec2, iam = session.client("ec2"), session.client("iam")

    quietly(lambda: ec2.terminate_instances(InstanceIds=[m["instance_id"]]), "InvalidInstanceID.NotFound")
    quietly(lambda: ec2.get_waiter("instance_terminated").wait(InstanceIds=[m["instance_id"]]), "InvalidInstanceID.NotFound")
    if m.get("allocation_id"):
        quietly(lambda: ec2.release_address(AllocationId=m["allocation_id"]), "InvalidAllocationID.NotFound")
    quietly(lambda: ec2.delete_security_group(GroupId=m["security_group_id"]), "InvalidGroup.NotFound")

    role = m["role"]
    quietly(lambda: iam.remove_role_from_instance_profile(InstanceProfileName=role, RoleName=role), "NoSuchEntity")
    quietly(lambda: iam.delete_instance_profile(InstanceProfileName=role), "NoSuchEntity")
    quietly(lambda: iam.delete_role_policy(RoleName=role, PolicyName="northstar-app-access"), "NoSuchEntity")
    quietly(lambda: iam.detach_role_policy(RoleName=role, PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"),
            "NoSuchEntity")
    quietly(lambda: iam.delete_role(RoleName=role), "NoSuchEntity")

    if args.disable_schedules:
        scheduler = session.client("scheduler")
        keep = ("ScheduleExpression", "ScheduleExpressionTimezone", "FlexibleTimeWindow", "Target", "Description",
                "GroupName", "StartDate", "EndDate", "KmsKeyArn", "ActionAfterCompletion")
        for name in SCHEDULES:
            current = scheduler.get_schedule(Name=name)
            scheduler.update_schedule(Name=name, State="DISABLED", **{k: current[k] for k in keep if k in current})
            print(f"  {name} -> DISABLED")

    MANIFEST.unlink()
    print("Removed. The DynamoDB table and Knowledge Base are untouched.")


if __name__ == "__main__":
    main()
