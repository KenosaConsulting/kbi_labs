import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'API is working!' if you receive this."}],
        max_tokens=10
    )
    print("Success! OpenAI says:", response.choices[0].message.content)
except Exception as e:
    print("Error:", str(e))
    print("API Key starts with:", os.getenv('OPENAI_API_KEY')[:20] + "...")
