#!/bin/bash
echo "🧪 Running KBI Labs Tests..."
echo "=========================="

# Run pytest
pytest tests/ -v

# Check code quality
echo -e "\n📝 Checking Code Quality..."
flake8 src/ --max-line-length=100 --exclude=__pycache__ --ignore=E402,W503

echo -e "\n✅ Tests Complete!"
