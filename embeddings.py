import requests
import json, os
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import time
from configs import config

# def get_creds():
#     credentials, project = default()
#     credentials.refresh(Request())
#     return credentials.token

def get_creds(service_account_path=config.GOOGLE_CREDS_JSON):
    """
    Get access token using service account JSON file.
    
    Args:
        service_account_path (str): Path to the service account JSON file
        
    Returns:
        str: Access token
    """
    try:
        # Load service account credentials from JSON file
        credentials = Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Refresh the credentials to get an access token
        credentials.refresh(Request())
        
        return credentials.token
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def get_embeddings(input_text):
    url = config.EMBEDDINGS_URL

    headers = {
        'Authorization': f'Bearer {get_creds()}',
        'Content-Type': 'application/json'
    }

    # Define the data payload
    data = {
        "instances": [
            {
            # "task_type": "QUESTION_ANSWERING",
            "content": input_text
            }
        ],
        # "parameters": {
        #     "outputDimensionality": 256
        # }
    }

    # Send the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Print the response
    if response.status_code != 200:
        if response.status_code == 429:
            print('quota limit reached, waiting a minute')
            time.sleep(60)
            print("trying again")
            return get_embeddings(input_text)
        else:
            print(response.status_code)
            print(response.json())
    else:
        response_json = response.json()
        return response_json['predictions'][0]['embeddings']['values']

# print(get_embeddings("hello world"))