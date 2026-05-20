import json
from .deterministic_agent import DeterministicAgent
from tools.assign_employee_tool import assign_resources


class ResourceAllocationLogic:
    """
    Deterministic logic for the ResourceAgent step.
    Parses input, delegates to assign_resources tool, detects shortages.
    """

    def __call__(self, input_text: str) -> str:
        try:
            data = json.loads(input_text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", input_text, re.DOTALL)
            if not match:
                raise ValueError("Could not extract JSON from input_text.")
            data = json.loads(match.group(0))

        project_name = data["project_name"]
        tasks = data["tasks"]

        result = assign_resources(project_name=project_name, tasks=tasks)
        result["resource_blocked"] = self._has_shortage(result.get("tasks", []))

        if result["resource_blocked"]:
            count = sum(1 for t in result["tasks"] if t.get("Assigned_Employee") == "No Resource Available")
            print(f"\n🚨 RESOURCE SHORTAGE: {count} tasks unassigned in '{project_name}'\n")

        return json.dumps(result)

    def _has_shortage(self, tasks: list) -> bool:
        return any(t.get("Assigned_Employee") == "No Resource Available" for t in tasks)


def build_resource_agent():
    return DeterministicAgent(
        name="resource_agent",
        description="Deterministic resource allocation agent",
        logic=ResourceAllocationLogic(),
    )
