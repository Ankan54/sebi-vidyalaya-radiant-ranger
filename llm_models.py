import os
from langchain_openai import AzureChatOpenAI
from configs import config


llm = AzureChatOpenAI(
       api_version= config.AZURE_API_VERSION,
       api_key= config.AZURE_API_KEY,
       azure_endpoint= config.AZURE_ENDPOINT,
       azure_deployment= config.DEPLOYMENT_NAME, temperature= 0
   )