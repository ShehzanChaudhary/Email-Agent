import json

from src.adapters.logger import logger
from src.adapters.openrouter import openrouter
from config.config import Config
from src.model import EmailMessage, Message
from prompts import get_prompt_template
from src.tools import VALID_CLASSIFICATIONS, build_tools
from src.utils_helper import decode_json

_template = get_prompt_template("react_system.jinja2")


def build_prompt(email: EmailMessage, tools: dict, scratchpad: list[dict]) -> str:
    return _template.render(
        tools=tools,
        tool_names=", ".join(tools.keys()),
        sender=email.display_sender(),
        subject=email.subject,
        body=email.body,
        scratchpad=scratchpad,
    )


def run_tool(tools: dict, tool_name: str, tool_input: dict) -> str:
    if tool_name not in tools:
        return f"Error: unknown tool '{tool_name}'. Available tools: {', '.join(tools.keys())}"

    func = tools[tool_name]["func"]
    try:
        return func(**(tool_input or {}))
    except Exception as ex:
        logger.error(f"Tool '{tool_name}' raised: {ex}", exc_info=True)
        return f"Error: {ex}"


def _as_thought_process(scratchpad: list[dict]) -> list[dict]:
    """Reshapes the raw scratchpad into the {step, observation, thought, action} shape the dashboard expects."""
    return [
        {
            "step": i + 1,
            "observation": turn["observation"],
            "thought": turn["thought"],
            "action": f'{turn["tool_name"]}({json.dumps(turn["tool_input"])})' if turn["tool_name"] else "",
        }
        for i, turn in enumerate(scratchpad)
    ]


def run_agent(email: EmailMessage, max_turns: int = None, on_turn=None) -> dict:
    """
    Runs the ReAct loop for a single email: classify it, draft a reply if one
    is warranted, and return a structured result. If given, on_turn(turn_number,
    turn_dict) is called right after each turn is appended to the scratchpad.
    """
    max_turns = max_turns or Config.MAX_ITERATIONS
    tools = build_tools(email)
    scratchpad: list[dict] = []

    for turn in range(1, max_turns + 1):
        prompt = build_prompt(email, tools, scratchpad)
        raw, _ = openrouter.chat([Message(role="user", content=prompt)], json_mode=True)
        decoded_response = decode_json(raw)

        if decoded_response.get("is_response"):
            classification = decoded_response.get("classification", "")
            if classification not in VALID_CLASSIFICATIONS:
                classification = "Enquiry"

            suggested_reply = decoded_response.get("suggested_reply", "")
            if not suggested_reply and classification in {"Promotional", "Spam"}:
                suggested_reply = f"No reply needed -- classified as {classification}."

            logger.info(f"STATUS: Final response reached on turn {turn} for uid={email.uid}: classification={classification}")
            return {
                "classification": classification,
                "confidence": decoded_response.get("confidence", 0),
                "suggested_reply": suggested_reply,
                "summary": decoded_response.get("response", ""),
                "thought_process": _as_thought_process(scratchpad),
                "scratchpad": scratchpad,
                "turns": turn,
                "stopped_reason": "final_answer",
            }

        tool_name = decoded_response.get("tool_name")
        tool_input = decoded_response.get("tool_input") or {}
        tool_result = run_tool(tools, tool_name, tool_input)

        turn_data = {
            "observation": decoded_response.get("observation", ""),
            "thought": decoded_response.get("thought", ""),
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_result": tool_result,
        }
        scratchpad.append(turn_data)
        if on_turn:
            on_turn(turn, turn_data)
        logger.info(f"Turn {turn}: tool={tool_name} input={tool_input}")

    logger.warning(f"Hit max_turns={max_turns} without a final answer for uid={email.uid}")
    return {
        "classification": "",
        "confidence": 0,
        "suggested_reply": "",
        "summary": "Agent could not reach a final classification/reply within the allotted turns.",
        "thought_process": _as_thought_process(scratchpad),
        "scratchpad": scratchpad,
        "turns": max_turns,
        "stopped_reason": "max_turns",
    }
