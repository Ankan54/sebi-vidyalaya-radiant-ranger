import requests
import json
import os
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from configs import config

# Global constant for Indian language mapping
INDIAN_LANGUAGE_CODES = {
    'hindi': 'hi',
    'bengali': 'bn', 
    'kannada': 'kn',
    'marathi': 'mr',
    'gujarati': 'gu',
    'tamil': 'ta',
    'telugu': 'te',
    'punjabi': 'pa',
    'malayalam': 'ml',
    'odia': 'or',
    'assamese': 'as',
    'urdu': 'ur'
}

def get_access_token_from_service_account(service_account_path):
    """
    Get access token using service account JSON file.
    
    Args:
        service_account_path (str): Path to the service account JSON file
        
    Returns:
        str: Access token
    """
    try:
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Refresh the credentials to get an access token
        credentials.refresh(Request())
        
        return credentials.token
        
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def translate_indian_language_to_english(text, source_language_code, project_id=config.GOOGLE_PROJECT_ID,
                                       service_account_path=config.GOOGLE_CREDS_JSON):
    """
    Translate text from any Indian language to English using service account credentials.
    
    Args:
        text (str): Text to translate
        source_language_code (str): Source language code (e.g., 'hi', 'bn', 'kn', 'mr', 'gu')
        project_id (str): Google Cloud Project ID
        service_account_path (str): Path to service account JSON file
        
    Returns:
        str: Translated text in English
    """
    
    # Convert language name to code if necessary
    if source_language_code.lower() in INDIAN_LANGUAGE_CODES:
        source_language_code = INDIAN_LANGUAGE_CODES[source_language_code.lower()]
    
    # Get access token from service account
    access_token = get_access_token_from_service_account(service_account_path)
    if not access_token:
        print("Failed to get access token")
        return None
    
    # API endpoint
    url = f"https://translation.googleapis.com/v3/projects/{project_id}:translateText"
    
    # Request headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'x-goog-user-project': project_id
    }
    
    # Request body
    data = {
        "sourceLanguageCode": source_language_code,
        "targetLanguageCode": "en",
        "contents": [text],
        "mimeType": "text/plain"
    }
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        translated_text = result['translations'][0]['translatedText']
        
        return translated_text
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None
    except KeyError as e:
        print(f"Error parsing response: {e}")
        print(f"Full response: {response.text}")
        return None


if __name__ == "__main__":
    # Test with different Indian languages
    test_cases = [
        ("आज मौसम बहुत अच्छा है।", "hi", "Hindi"),
        ("আজ আবহাওয়া খুব ভালো।", "bn", "Bengali"),
        ("ಇಂದು ಹವಾಮಾನ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ.", "kn", "Kannada"),
        ("आज हवामान खूप चांगले आहे.", "mr", "Marathi"),
        ("આજે હવામાન ખૂબ સારું છે.", "gu", "Gujarati")
    ]
    
    for text, lang_code, lang_name in test_cases:
        print(f"\nTranslating from {lang_name}:")
        english_text = translate_indian_language_to_english(text, lang_code)
        
        if english_text:
            print(f"Original ({lang_name}): {text}")
            print(f"Translated (English): {english_text}")
        else:
            print(f"Translation failed for {lang_name}")
    
    print("\n" + "="*50 + "\n")