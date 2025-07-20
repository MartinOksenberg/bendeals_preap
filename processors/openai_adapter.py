import os
import requests
import json

def call_openai_api(system_prompt, user_prompt, model="gpt-4o"):
    """
    Manually call the OpenAI API using the requests library.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not found.")
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    
    print("Using OpenAI API Key.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 16000
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            proxies=None  # Explicitly disable proxies
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenAI API: {e}")
        return None 
