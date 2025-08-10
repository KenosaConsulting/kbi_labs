#!/bin/bash
# Security scanning and analysis script

set -e

echo "🔒 Running KBI Labs Security Analysis Suite"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        echo "Install with: pip install $2"
        exit 1
    fi
}

echo "📋 Checking security tools..."
check_tool "bandit" "bandit[toml]"
check_tool "safety" "safety"
check_tool "pip-audit" "pip-audit"

echo ""

# 1. Bandit - Security linter for Python
echo -e "${YELLOW}🔍 Running Bandit security scan...${NC}"
if bandit -c .bandit -f json -o security-report.json .; then
    echo -e "${GREEN}✅ Bandit scan completed${NC}"
    
    # Check for high severity issues
    high_issues=$(jq '.results[] | select(.issue_severity == "HIGH")' security-report.json | jq -s length)
    medium_issues=$(jq '.results[] | select(.issue_severity == "MEDIUM")' security-report.json | jq -s length)
    
    if [ "$high_issues" -gt 0 ]; then
        echo -e "${RED}❌ Found $high_issues HIGH severity security issues${NC}"
        jq '.results[] | select(.issue_severity == "HIGH")' security-report.json
        exit 1
    elif [ "$medium_issues" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Found $medium_issues MEDIUM severity security issues${NC}"
        jq '.results[] | select(.issue_severity == "MEDIUM")' security-report.json
    fi
else
    echo -e "${RED}❌ Bandit scan failed${NC}"
    exit 1
fi

echo ""

# 2. Safety - Check for known vulnerabilities in dependencies
echo -e "${YELLOW}🛡️  Running Safety vulnerability scan...${NC}"
if safety check --json --output safety-report.json; then
    echo -e "${GREEN}✅ Safety scan completed - no known vulnerabilities${NC}"
else
    echo -e "${RED}❌ Safety found known vulnerabilities in dependencies${NC}"
    cat safety-report.json
    exit 1
fi

echo ""

# 3. pip-audit - Audit Python packages for known vulnerabilities
echo -e "${YELLOW}📦 Running pip-audit vulnerability scan...${NC}"
if pip-audit --format=json --output=pip-audit-report.json; then
    echo -e "${GREEN}✅ pip-audit scan completed - no vulnerabilities found${NC}"
else
    echo -e "${RED}❌ pip-audit found vulnerabilities in packages${NC}"
    cat pip-audit-report.json
    exit 1
fi

echo ""

# 4. Check for secrets in code (simple grep-based check)
echo -e "${YELLOW}🔐 Scanning for potential secrets...${NC}"
secrets_found=0

# Common secret patterns
patterns=(
    "password\s*=\s*['\"][^'\"]{8,}"
    "api[_-]?key\s*=\s*['\"][^'\"]{10,}"
    "secret[_-]?key\s*=\s*['\"][^'\"]{10,}"
    "token\s*=\s*['\"][^'\"]{10,}"
    "-----BEGIN RSA PRIVATE KEY-----"
    "-----BEGIN PRIVATE KEY-----"
    "sk-[a-zA-Z0-9]{48}"  # OpenAI API key pattern
)

for pattern in "${patterns[@]}"; do
    if grep -r -i -E "$pattern" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=node_modules --exclude=security_scan.sh --exclude="*.json" --exclude="*.md" --exclude=".env*"; then
        echo -e "${RED}❌ Potential secret found matching pattern: $pattern${NC}"
        secrets_found=$((secrets_found + 1))
    fi
done

if [ $secrets_found -eq 0 ]; then
    echo -e "${GREEN}✅ No hardcoded secrets detected${NC}"
fi

echo ""

# 5. File permissions check
echo -e "${YELLOW}🔒 Checking file permissions...${NC}"
sensitive_files=(".env" ".env.production" "*.key" "*.pem")
permission_issues=0

for pattern in "${sensitive_files[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            perms=$(stat -c "%a" "$file" 2>/dev/null || stat -f "%Lp" "$file" 2>/dev/null)
            if [ "$perms" != "600" ] && [ "$perms" != "400" ]; then
                echo -e "${RED}❌ File $file has insecure permissions: $perms${NC}"
                permission_issues=$((permission_issues + 1))
            fi
        fi
    done
done

if [ $permission_issues -eq 0 ]; then
    echo -e "${GREEN}✅ File permissions are secure${NC}"
fi

echo ""

# 6. Docker security check (if Dockerfile exists)
if [ -f "Dockerfile" ]; then
    echo -e "${YELLOW}🐳 Checking Docker security...${NC}"
    
    # Check for running as root
    if grep -q "USER root" Dockerfile || ! grep -q "USER " Dockerfile; then
        echo -e "${YELLOW}⚠️  Docker container may be running as root${NC}"
    else
        echo -e "${GREEN}✅ Docker container runs as non-root user${NC}"
    fi
    
    # Check for specific security issues
    if grep -q "ADD.*http" Dockerfile; then
        echo -e "${RED}❌ Dockerfile uses ADD with HTTP - potential security risk${NC}"
    fi
    
    if grep -q "chmod 777\|chmod a+rwx" Dockerfile; then
        echo -e "${RED}❌ Dockerfile sets overly permissive file permissions${NC}"
    fi
fi

echo ""

# 7. Generate security report summary
echo -e "${YELLOW}📊 Generating security report summary...${NC}"

cat > security-summary.json << EOF
{
    "scan_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "bandit": {
        "high_issues": $high_issues,
        "medium_issues": $medium_issues,
        "report_file": "security-report.json"
    },
    "safety": {
        "vulnerabilities_found": false,
        "report_file": "safety-report.json"
    },
    "pip_audit": {
        "vulnerabilities_found": false,
        "report_file": "pip-audit-report.json"
    },
    "secrets_scan": {
        "potential_secrets": $secrets_found
    },
    "file_permissions": {
        "issues_found": $permission_issues
    },
    "overall_status": "$([ $high_issues -eq 0 ] && [ $secrets_found -eq 0 ] && [ $permission_issues -eq 0 ] && echo "PASS" || echo "FAIL")"
}
EOF

echo -e "${GREEN}✅ Security summary generated: security-summary.json${NC}"

echo ""
echo "🎯 Security Scan Complete!"
echo "=========================="

# Final status
overall_status=$(jq -r .overall_status security-summary.json)
if [ "$overall_status" = "PASS" ]; then
    echo -e "${GREEN}✅ All security checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some security issues found. Please review reports.${NC}"
    exit 1
fi