from strands import Agent, tool
from strands.models import BedrockModel


@tool
def get_my_pto() -> dict:
    """Return the signed-in employee's PTO balance in hours."""
    return {"available_hours": 96}


agent = Agent(
    model=BedrockModel(model_id="us.amazon.nova-2-lite-v1:0", region_name="us-east-1"),
    tools=[get_my_pto],
    system_prompt="You are an HR assistant. Use tools for employee records.",
)

agent("How much PTO do I have?")