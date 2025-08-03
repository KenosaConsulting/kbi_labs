import fileinput
import sys

# Read the file and fix the jwt.decode line
with open('src/api/v2/intelligence.py', 'r') as f:
    content = f.read()

# Replace the jwt.decode to not verify audience
content = content.replace(
    """        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )""",
    """        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False}
        )"""
)

# Write back
with open('src/api/v2/intelligence.py', 'w') as f:
    f.write(content)

print("✅ Fixed JWT audience verification")
