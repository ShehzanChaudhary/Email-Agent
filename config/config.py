import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')
    MODEL = os.environ.get('MODEL', 'openai/gpt-4o-mini')
    MAX_ITERATIONS = int(os.environ.get('EMAIL_AGENT_MAX_ITERATIONS', '6'))

    # Mailbox (IMAP) -- for Gmail, EMAIL_PASSWORD must be an App Password,
    # not the regular account password (needs 2-Step Verification enabled).
    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
    IMAP_HOST = os.environ.get('IMAP_HOST', 'imap.gmail.com')
    IMAP_PORT = int(os.environ.get('IMAP_PORT', '993'))
    IMAP_FOLDER = os.environ.get('IMAP_FOLDER', 'INBOX')
    POLL_INTERVAL_SECONDS = int(os.environ.get('POLL_INTERVAL_SECONDS', '30'))