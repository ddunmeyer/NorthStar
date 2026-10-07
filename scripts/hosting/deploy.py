"""Host North Star on one EC2 instance that the EC2 Scheduler project starts and stops.

Dry run by default: prints the plan and creates nothing. Add --apply to build.

    python scripts/hosting/deploy.py            # show the plan
    python scripts/hosting/deploy.py --apply    # create the resources

What --apply creates in the signed-in AWS account:
  - IAM role + instance profile NorthStarAppRole (Bedrock model calls, Knowledge Base
    retrieval, read/write on the records table, Session Manager access; nothing else)
  - Security group NorthStar-Demo-Web: port 80 open to the internet, no SSH
  - One t3.small instance tagged AutoSchedule=true, running the app as a service
  - One Elastic IP, so the address survives the nightly stop and morning start
and it switches the existing EC2-Lab start and stop schedules to ENABLED.

Resource IDs are saved to .northstar-hosting.json for teardown.py.
"""
import argparse
import json
import os
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

REGION = os.getenv("AWS_REGION") or "us-east-1"
MODEL_ID = os.getenv("NORTHSTAR_MODEL_ID") or "us.amazon.nova-2-lite-v1:0"
TABLE = os.getenv("NORTHSTAR_TABLE") or "northstar"
KB_ID = os.getenv("NORTHSTAR_KB_ID")
REPO_URL = "https://github.com/ddunmeyer/NorthStar.git"

NAME = "NorthStar-Demo"
ROLE = "NorthStarAppRole"
SECURITY_GROUP = "NorthStar-Demo-Web"
INSTANCE_TYPE = "t3.small"
AMI_PARAMETER = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
SCHEDULES = ["EC2-Lab-Start-Schedule", "EC2-Lab-Stop-Schedule"]
MANIFEST = ROOT / ".northstar-hosting.json"
TAGS = [{"Key": "project", "Value": "northstar"}]


def app_policy(account: str) -> dict:
    """Everything the running app is allowed to do, and nothing more."""
    base_model = MODEL_ID.split(".", 1)[1] if MODEL_ID.split(".", 1)[0] in ("us", "eu", "apac", "global") else MODEL_ID
    return {"Version": "2012-10-17", "Statement": [
        {"Sid": "InvokeModel", "Effect": "Allow",
         "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
         "Resource": [f"arn:aws:bedrock:{REGION}:{account}:inference-profile/{MODEL_ID}",
                      f"arn:aws:bedrock:*::foundation-model/{base_model}"]},
        {"Sid": "RetrievePolicies", "Effect": "Allow", "Action": "bedrock:Retrieve",
         "Resource": f"arn:aws:bedrock:{REGION}:{account}:knowledge-base/{KB_ID}"},
        {"Sid": "EmployeeRecords", "Effect": "Allow",
         "Action": ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:PutItem"],
         "Resource": f"arn:aws:dynamodb:{REGION}:{account}:table/{TABLE}"},
    ]}


def user_data() -> str:
    # A Windows checkout may give the script CRLF line endings, which would break it on Linux.
    script = (Path(__file__).parent / "server_setup.sh").read_text(encoding="utf-8").replace("\r\n", "\n")
    for key, value in {"__REPO_URL__": REPO_URL, "__REGION__": REGION, "__MODEL_ID__": MODEL_ID,
                       "__TABLE__": TABLE, "__KB_ID__": KB_ID}.items():
        script = script.replace(key, value)
    return script


def create_role(iam, account: str) -> None:
    trust = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    try:
        iam.create_role(RoleName=ROLE, AssumeRolePolicyDocument=json.dumps(trust), Tags=TAGS,
                        Description="North Star demo server: Bedrock, policy Knowledge Base and the records table")
    except ClientError as err:
        if err.response["Error"]["Code"] != "EntityAlreadyExists":
            raise
    iam.put_role_policy(RoleName=ROLE, PolicyName="northstar-app-access", PolicyDocument=json.dumps(app_policy(account)))
    # Session Manager gives shell access for debugging without opening SSH or storing a key.
    iam.attach_role_policy(RoleName=ROLE, PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore")
    try:
        iam.create_instance_profile(InstanceProfileName=ROLE)
        iam.add_role_to_instance_profile(InstanceProfileName=ROLE, RoleName=ROLE)
    except ClientError as err:
        if err.response["Error"]["Code"] != "EntityAlreadyExists":
            raise


def create_security_group(ec2) -> str:
    vpc = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    found = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": [SECURITY_GROUP]},
                                                  {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
    if found:
        return found[0]["GroupId"]
    group = ec2.create_security_group(
        GroupName=SECURITY_GROUP, VpcId=vpc, Description="North Star demo server: HTTP from anywhere, no SSH",
        TagSpecifications=[{"ResourceType": "security-group", "Tags": TAGS + [{"Key": "Name", "Value": SECURITY_GROUP}]}])
    ec2.authorize_security_group_ingress(GroupId=group["GroupId"], IpPermissions=[{
        "IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
        "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "Public HTTP for the class demo"}]}])
    return group["GroupId"]


def launch(ec2, ami: str, group_id: str) -> str:
    instance_tags = TAGS + [{"Key": "Name", "Value": NAME}, {"Key": "AutoSchedule", "Value": "true"},
                            {"Key": "ManagedBy", "Value": "EC2Scheduler"}, {"Key": "Environment", "Value": "Demo"},
                            {"Key": "DoNotStop", "Value": "false"}]
    for attempt in range(8):  # a brand-new instance profile takes a few seconds to become usable
        try:
            result = ec2.run_instances(
                ImageId=ami, InstanceType=INSTANCE_TYPE, MinCount=1, MaxCount=1,
                IamInstanceProfile={"Name": ROLE}, SecurityGroupIds=[group_id], UserData=user_data(),
                MetadataOptions={"HttpTokens": "required", "HttpEndpoint": "enabled"},
                BlockDeviceMappings=[{"DeviceName": "/dev/xvda",
                                      "Ebs": {"VolumeSize": 12, "VolumeType": "gp3", "DeleteOnTermination": True}}],
                TagSpecifications=[{"ResourceType": "instance", "Tags": instance_tags},
                                   {"ResourceType": "volume", "Tags": TAGS}])
            return result["Instances"][0]["InstanceId"]
        except ClientError as err:
            if "Invalid IAM Instance Profile" not in str(err) or attempt == 7:
                raise
            time.sleep(5)
    raise RuntimeError("unreachable")


def enable_schedules(scheduler) -> None:
    """Switch the EC2 Scheduler project's start and stop schedules on, keeping everything else as is."""
    keep = ("ScheduleExpression", "ScheduleExpressionTimezone", "FlexibleTimeWindow", "Target", "Description",
            "GroupName", "StartDate", "EndDate", "KmsKeyArn", "ActionAfterCompletion")
    for name in SCHEDULES:
        current = scheduler.get_schedule(Name=name)
        scheduler.update_schedule(Name=name, State="ENABLED", **{k: current[k] for k in keep if k in current})
        print(f"  {name}: {current['ScheduleExpression']} {current.get('ScheduleExpressionTimezone', '')} -> ENABLED")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--apply", action="store_true", help="create the resources (default is a dry run)")
    parser.add_argument("--no-schedules", action="store_true", help="leave the start/stop schedules as they are")
    args = parser.parse_args()

    if not KB_ID:
        raise SystemExit("NORTHSTAR_KB_ID is not set. Add it to .env first.")
    session = boto3.Session(region_name=REGION)
    identity = session.client("sts").get_caller_identity()
    account = identity["Account"]
    ec2, iam = session.client("ec2"), session.client("iam")

    print(f"Signed in as {identity['Arn'].split('/')[-1]} in {REGION}.")
    print(f"Plan: IAM role {ROLE}; security group {SECURITY_GROUP} (port 80 open to the internet);")
    print(f"      one {INSTANCE_TYPE} named {NAME} tagged AutoSchedule=true; one Elastic IP;")
    print(f"      app settings: model {MODEL_ID}, table {TABLE}, knowledge base {KB_ID};")
    print(f"      enable schedules: {'no' if args.no_schedules else ', '.join(SCHEDULES)}.")
    if not args.apply:
        print("Dry run only. Nothing was created. Add --apply to build.")
        return
    if MANIFEST.exists():
        raise SystemExit(f"{MANIFEST.name} already exists: a server is already deployed. Run teardown.py first.")

    ami = session.client("ssm").get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"]
    create_role(iam, account)
    group_id = create_security_group(ec2)
    instance_id = launch(ec2, ami, group_id)
    manifest = {"region": REGION, "instance_id": instance_id, "security_group_id": group_id, "role": ROLE}
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Launched {instance_id}. Waiting for it to run...")
    ec2.get_waiter("instance_running").wait(InstanceIds=[instance_id])

    address = ec2.allocate_address(Domain="vpc", TagSpecifications=[
        {"ResourceType": "elastic-ip", "Tags": TAGS + [{"Key": "Name", "Value": NAME}]}])
    ec2.associate_address(InstanceId=instance_id, AllocationId=address["AllocationId"])
    manifest.update(allocation_id=address["AllocationId"], public_ip=address["PublicIp"],
                    url=f"http://{address['PublicIp']}")
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if not args.no_schedules:
        print("Enabling the EC2 Scheduler schedules:")
        enable_schedules(session.client("scheduler"))

    print(f"\nServer address: {manifest['url']}")
    print("First boot installs Python packages and takes about three minutes before the page answers.")
    print("The scheduler stops it at 6:00 PM and starts it at 8:00 AM, America/Chicago.")


if __name__ == "__main__":
    main()
