from dataclasses import dataclass, field


@dataclass
class Message:
    """A single chat turn, in the shape OpenRouterService.chat() sends to the API."""
    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class EmailMessage:
    """A single mailbox message, parsed down to what the agent needs to act on."""
    uid: str
    sender_name: str
    sender_email: str
    subject: str
    body: str
    received_at: str  # ISO 8601, derived from the IMAP INTERNALDATE
    attachments: list[str] = field(default_factory=list)

    def display_sender(self) -> str:
        if self.sender_name and self.sender_name != self.sender_email:
            return f"{self.sender_name} <{self.sender_email}>"
        return self.sender_email
