"""
Tools the email ReAct agent can call. Built fresh per email via build_tools()
rather than as a static registry -- the email content is already fully known
(read straight off IMAP), so it's captured in a closure instead of being
echoed back through the LLM's tool_input JSON, which would waste tokens and
risk mangling long or HTML-heavy bodies.

Each tool returns a plain string -- that string becomes the "Result" the LLM
reads back in its scratchpad, so formatting here is for the LLM's eyes.
"""
from src.adapters.logger import logger
from src.adapters.openrouter import openrouter
from src.model import EmailMessage, Message
from prompts import get_prompt_template
from src.utils_helper import decode_json

VALID_CLASSIFICATIONS = {
    "Enquiry",
    "Complaint",
    "Order Update",
    "Support Request",
    "Promotional",
    "Spam",
}


def build_tools(email: EmailMessage) -> dict:
    def classify_email() -> str:
        template = get_prompt_template("classify_email.jinja2")
        prompt = template.render(sender=email.display_sender(), subject=email.subject, body=email.body)
        raw, _ = openrouter.chat([Message(role="user", content=prompt)], json_mode=True)
        decoded = decode_json(raw)

        classification = decoded.get("classification", "")
        if classification not in VALID_CLASSIFICATIONS:
            logger.warning(f"classify_email returned unexpected classification {classification!r}, defaulting to 'Enquiry'")
            classification = "Enquiry"
        confidence = decoded.get("confidence", 0)
        reasoning = decoded.get("reasoning", "")

        return f"Classification: {classification} (confidence: {confidence}). Reasoning: {reasoning}"

    def generate_reply(classification: str, key_points: str = "") -> str:
        template = get_prompt_template("generate_reply.jinja2")
        prompt = template.render(
            sender=email.display_sender(),
            subject=email.subject,
            body=email.body,
            classification=classification,
            key_points=key_points,
        )
        raw, _ = openrouter.chat([Message(role="user", content=prompt)], json_mode=True)
        decoded = decode_json(raw)

        reply = decoded.get("reply", "")
        if not reply:
            return "Error: reply generation failed to produce any text."
        return f"Suggested reply:\n{reply}"

    return {
        "classify_email": {
            "func": classify_email,
            "description": (
                "Classifies the current email's intent into one of: Enquiry, Complaint, "
                "Order Update, Support Request, Promotional, Spam. Reads the email directly "
                "-- no input needed."
            ),
            "args": "{}",
        },
        "generate_reply": {
            "func": generate_reply,
            "description": (
                "Drafts a reply to the current email. Only call this for classifications "
                "that need a human-facing reply (Enquiry, Complaint, Order Update, Support "
                "Request) -- skip it for Promotional or Spam."
            ),
            "args": (
                '{"classification": "<the classification from classify_email>", '
                '"key_points": "<optional -- specific points the reply must address>"}'
            ),
        },
    }
