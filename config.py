"""
config.py
---------
Loads environment variables and creates the shared LLM client.
All other files import 'llm' and 'IS_MOCK' from here.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load values from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL_NAME   = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

# Check if the key is missing or is still the default placeholder
IS_MOCK = not GROQ_API_KEY or GROQ_API_KEY.startswith("your_")

llm = None
if not IS_MOCK:
    try:
        # Create shared LLM instance
        llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=MODEL_NAME,
            temperature=0.2,
        )
    except Exception as e:
        print(f"Error initializing ChatGroq: {e}")
        IS_MOCK = True

if IS_MOCK:
    print("\n" + "=" * 80)
    print("  [!] WARNING: Running in Demo / Simulation Mode.")
    print("  To use real Groq LLM, please put a valid GROQ_API_KEY in your .env file.")
    print("=" * 80 + "\n")
else:
    print("\n" + "=" * 80)
    print(f"  [*] LLM Initialized Successfully! Model: {MODEL_NAME}")
    print("=" * 80 + "\n")


