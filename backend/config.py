import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HMAC_SECRET_KEY = os.getenv("HMAC_SECRET_KEY")
    if not HMAC_SECRET_KEY:
        raise ValueError("HMAC_SECRET_KEY must be set in the environment or .env file.")

config = Config()
