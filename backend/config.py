import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Read configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))

# Validate API Key
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Please add it to the .env file.")

# Shared LLM instance
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)

 App settings
APP_NAME = "AI Agent Coordination & Decision Engine"
APP_VERSION = "1.0.0"