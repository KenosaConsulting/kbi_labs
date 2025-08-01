import re

with open('ai_insights_api.py', 'r') as f:
    content = f.read()

# Make sure CORS is properly configured
if 'CORS(app)' not in content:
    # Add CORS after app initialization
    content = content.replace(
        'app = Flask(__name__)',
        'app = Flask(__name__)\nCORS(app, resources={r"/api/*": {"origins": "*"}})'
    )
else:
    # Update existing CORS to allow all origins
    content = re.sub(
        r'CORS\(app\)',
        'CORS(app, resources={r"/api/*": {"origins": "*"}})',
        content
    )

with open('ai_insights_api.py', 'w') as f:
    f.write(content)

print("CORS configuration updated!")
