import os
from langchain_openai import AzureChatOpenAI
from crewai import LLM
from configs import config


azure_llm = AzureChatOpenAI(
       api_version= config.AZURE_API_VERSION,
       api_key= config.AZURE_API_KEY,
       azure_endpoint= config.AZURE_ENDPOINT,
       azure_deployment= config.DEPLOYMENT_NAME, temperature= 0
   )

llm = LLM(
    model=f"azure/{config.DEPLOYMENT_NAME}",
    api_version=config.AZURE_API_VERSION, temperature=0
)

llm_stream = LLM(
    model=f"azure/{config.DEPLOYMENT_NAME}",
    api_version=config.AZURE_API_VERSION,temperature=0, stream= True
)