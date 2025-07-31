import re

with open('ai_insights_api.py', 'r') as f:
    content = f.read()

# Find the _call_gpt4 method and add logging
new_logging = '''
                logger.info(f"Calling OpenAI with model: {self.model}")
                response = openai.ChatCompletion.create('''

content = content.replace('response = openai.ChatCompletion.create(', new_logging)

# Add error logging
error_logging = '''
            except Exception as e:
                logger.error(f"GPT-4 API error (attempt {attempt + 1}): {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")'''

content = content.replace('except Exception as e:\n                logger.error(f"GPT-4 API error (attempt {attempt + 1}): {str(e)}")', error_logging)

with open('ai_insights_api.py', 'w') as f:
    f.write(content)

print("Logging added!")
