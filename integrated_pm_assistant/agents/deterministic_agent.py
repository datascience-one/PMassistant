import json
import re
from typing import AsyncGenerator, Callable, Any

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.events.event import Event
from pydantic import Field


class DeterministicAgent(BaseAgent):
    """
    ADK BaseAgent that runs a plain Python function instead of an LLM.
    Used for deterministic pipeline steps (resource allocation, scheduling, etc.).

    The logic callable receives the previous agent's text output as a string
    and must return a JSON-serialisable string.
    """

    logic: Callable[[str], Any] = Field(exclude=True)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        input_text = self._extract_input(ctx)
        input_text = self._unwrap_adk_envelope(input_text)
        result = self.logic(input_text)
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(parts=[types.Part(text=str(result))]),
            branch=ctx.branch,
        )

    # ── Private helpers ─────────────────────────────────────────────

    def _extract_input(self, ctx: InvocationContext) -> str:
        """Walk backwards through events and return the first non-empty text."""
        for event in reversed(ctx._get_events(current_invocation=True)):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        return part.text
        return "{}"

    def _unwrap_adk_envelope(self, text: str) -> str:
        """
        ADK sometimes wraps tool results in:
            {"tool_name": {"result": "<json>"}}
        This method peels that envelope and returns the inner payload as a
        JSON string, or returns the original text if no wrapping is detected.
        """
        try:
            parsed = self._extract_json(text)
            unwrapped = self._peel(parsed)
            return json.dumps(unwrapped) if isinstance(unwrapped, (dict, list)) else str(unwrapped)
        except Exception:
            return text

    def _extract_json(self, text: str):
        """Return parsed JSON from text, searching for the first {...} block."""
        if isinstance(text, (dict, list)):
            return text
        match = re.search(r'\{.*\}', str(text), re.DOTALL)
        if match:
            # Replace literal NaN (from Pandas) with null for valid JSON
            cleaned = re.sub(r'\bNaN\b', 'null', match.group(0))
            return json.loads(cleaned)
        raise ValueError("No JSON object found")

    def _peel(self, value):
        """Recursively unwrap single-key ADK envelope dicts."""
        if not isinstance(value, dict):
            return value
        # Already a payload
        if "project_name" in value or "tasks" in value:
            return value
        # ADK envelope: {"some_tool": {"result": "..."}}
        if len(value) == 1:
            inner = list(value.values())[0]
            if isinstance(inner, dict) and "result" in inner:
                return self._peel(self._extract_json(inner["result"]))
        return value
