import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
    AZURE_API_KEY = os.getenv("AZURE_API_KEY")
    AZURE_ENDPOINT = os.getenv("AZURE_API_BASE")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
    GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
    EMBEDDINGS_URL = os.getenv("EMBEDDINGS_URL")
    CHROMA_DB_PATH = r"./data/sebi_study_materials_db"
    chroma_collection_name = ""
    exam_name = ""
    user_language = ""
    kb_results = {}

config = Config()