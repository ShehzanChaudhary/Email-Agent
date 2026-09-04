from dataclasses import dataclass, field

@dataclass
class Message:
    """A single chat turn, in the shape OpenRouterService.chat() sends to the API."""
    role: str
    content: str

    def to_dict(self) -> dict:
        return {'role': self.role, 'content': self.content}

@dataclass
class EmailMessage:
    """A single mailbox message, parsed down to what the agent needs to act on."""
    uid: str
    sender: str
    subject: str
    body: str
    date: str
    attachments: list[str] = field(default_factory=list)