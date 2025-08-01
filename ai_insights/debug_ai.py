# Quick debug script to check what's happening
import sys
import os
sys.path.append('/home/ubuntu/KBILabs/ai_insights')

from dotenv import load_dotenv
load_dotenv()

print("API Key present:", bool(os.getenv('OPENAI_API_KEY')))
print("API Key length:", len(os.getenv('OPENAI_API_KEY', '')))
print("API Key prefix:", os.getenv('OPENAI_API_KEY', '')[:7])

# Try to import and check the module
try:
    import openai
    print("OpenAI version:", openai.__version__)
except Exception as e:
    print("Error importing openai:", e)
