import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
DB_PATH = ROOT / "support.db"
FAQ_PATH = ROOT / "data" / "faqs.md"
CHROMA_PATH = ROOT / ".chroma"
