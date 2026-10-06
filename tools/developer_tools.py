"""Developer tools: the signed-in employee's projects and Jira-style tasks.

The app builds these with make_developer_tools(employee_id). The employee ID is
fixed inside the tools, and a project the employee isn't a member of is denied.
"""
from boto3.dynamodb.conditions import Key
from strands import tool

from tools.hr_tools import TABLE, _plain


def _partition(pk: str) -> list:
    """Read every item in one partition, following pagination."""
    items = []
    kwargs = {"KeyConditionExpression": Key("pk").eq(pk)}
    while True:
        page = TABLE.query(**kwargs)
        items.extend(page["Items"])
        if "LastEvaluatedKey" not in page:
            return items
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def make_developer_tools(employee_id: str) -> list:
    """Build the developer tools for one signed-in employee."""

    def my_projects() -> list:
        return [p for p in _partition("PROJECTS") if employee_id in p.get("member_employee_ids", [])]

    @tool
    def get_my_projects() -> dict:
        """List the projects the signed-in employee is a member of."""
        fields = ("project_key", "name", "owner_employee_id")
        return {"projects": [_plain({k: p[k] for k in fields if k in p}) for p in my_projects()]}

    @tool
    def get_my_tasks(project_key: str | None = None) -> dict:
        """List the tasks assigned to the signed-in employee.

        Each task's required_service_id names the access it needs, for example
        VPN-DEV. The IT specialist can check or request that access.

        Args:
            project_key: Optional project key, for example NST. Leave empty for all of the employee's projects.
        """
        keys = [p["project_key"] for p in my_projects()]
        if project_key:
            key = project_key.strip().upper()
            if key not in keys:
                return {"error": f"Access denied: you are not a member of project {key}."}
            keys = [key]

        tasks = []
        for key in keys:
            tasks += [i for i in _partition(f"ISSUES#{key}") if i.get("assignee_employee_id") == employee_id]

        fields = ("issue_key", "project_key", "summary", "status", "priority",
                  "due_date", "sprint_id", "required_service_id")
        return {"task_count": len(tasks),
                "tasks": [_plain({k: t[k] for k in fields if k in t}) for t in tasks]}

    return [get_my_projects, get_my_tasks]