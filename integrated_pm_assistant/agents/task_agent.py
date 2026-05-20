from google.adk.agents import LlmAgent
from config_loader import load_config
from tools.save_tasks_tool import save_tasks_tool


def build_task_agent():

    config = load_config()
    model_name = config["models"]["default"]
    template = config["agents"]["task_decomposer"]["template"]

    instruction = f"""
{template}

You MUST:
1. Generate structured task JSON.
2. Call save_tasks_tool.
3. Return ONLY the JSON returned by save_tasks_tool.
Do not modify structure.
"""

    return LlmAgent(
        name="task_decomposer_agent",
        description="Generates development tasks from PRD JSON",
        model=model_name,
        instruction=instruction,
        tools=[save_tasks_tool]
    )