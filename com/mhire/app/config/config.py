import os
from dotenv import load_dotenv
            
load_dotenv()

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.groq_api_key = os.getenv("GROQ_API_KEY")
            cls._instance.groq_api_model = os.getenv("GROQ_MODEL_NAME")
            cls._instance.tavily_api_key = os.getenv("TAVILY_API_KEY")

        return cls._instance