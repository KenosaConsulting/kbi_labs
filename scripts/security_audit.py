#!/usr/bin/env python3
"""
Security Audit Script for KBI Labs
Validates security configuration and identifies potential vulnerabilities
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import tempfile
import hashlib

class SecurityAuditor:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.issues = []
        self.warnings = []
        self.info = []
        
    def audit_secrets(self) -> Dict[str, List[str]]:
        """Audit for hardcoded secrets and credentials"""
        
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{4,}["\']', 'Hardcoded password'),
            (r'secret\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded secret'),
            (r'api.?key\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded API key'),
            (r'token\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded token'),
            (r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']', 'Base64 encoded secret'),
            (r'sk-[A-Za-z0-9]{48}', 'OpenAI API key'),
            (r'ghp_[A-Za-z0-9]{36}', 'GitHub personal access token'),
            (r'xoxb-[A-Za-z0-9\-]+', 'Slack bot token'),
        ]
        
        findings = {'critical': [], 'warning': [], 'info': []}
        
        # Scan Python files
        for py_file in self.repo_root.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, description in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Check if it's a placeholder/example
                        if self._is_placeholder(match.group()):
                            findings['warning'].append({
                                'file': str(py_file.relative_to(self.repo_root)),
                                'line': line_num,
                                'type': description,
                                'content': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                            })
                        else:
                            findings['critical'].append({
                                'file': str(py_file.relative_to(self.repo_root)),
                                'line': line_num,
                                'type': description,
                                'content': '***REDACTED***'
                            })
            except Exception as e:
                findings['info'].append({
                    'file': str(py_file.relative_to(self.repo_root)),
                    'error': f"Could not scan file: {e}"
                })
        
        return findings
    
    def audit_file_permissions(self) -> List[Dict]:
        """Check for files with overly permissive permissions"""
        issues = []
        
        sensitive_files = ['.env', '.env.local', '*.key', '*.pem', '*.p12']
        
        for pattern in sensitive_files:
            for file_path in self.repo_root.rglob(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]
                    
                    # Check if file is readable by others
                    if int(mode[2]) >= 4:  # Others can read
                        issues.append({
                            'file': str(file_path.relative_to(self.repo_root)),
                            'issue': 'File readable by others',
                            'permissions': mode,
                            'recommendation': 'chmod 600'
                        })
        
        return issues
    
    def audit_dependencies(self) -> Dict[str, List]:
        """Audit Python dependencies for known vulnerabilities"""
        
        try:
            # Try to run safety check if available
            result = subprocess.run(['safety', 'check', '--json'], 
                                  capture_output=True, text=True, 
                                  cwd=self.repo_root)
            
            if result.returncode == 0:
                import json
                vulnerabilities = json.loads(result.stdout)
                return {'vulnerabilities': vulnerabilities}
            else:
                return {'info': ['Safety check not available. Install with: pip install safety']}
                
        except FileNotFoundError:
            return {'info': ['Safety check not available. Install with: pip install safety']}
        except Exception as e:
            return {'error': [f'Error running safety check: {e}']}
    
    def audit_docker_security(self) -> List[Dict]:
        """Audit Docker configuration for security issues"""
        issues = []
        
        docker_files = list(self.repo_root.glob('**/Dockerfile*')) + list(self.repo_root.glob('**/docker-compose*.yml'))
        
        for docker_file in docker_files:
            try:
                with open(docker_file, 'r') as f:
                    content = f.read()
                    
                # Check for root user
                if re.search(r'USER\s+root', content, re.IGNORECASE):
                    issues.append({
                        'file': str(docker_file.relative_to(self.repo_root)),
                        'issue': 'Running as root user',
                        'severity': 'medium',
                        'recommendation': 'Create and use non-root user'
                    })
                
                # Check for hardcoded secrets in docker files
                if re.search(r'(password|secret|key)\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
                    issues.append({
                        'file': str(docker_file.relative_to(self.repo_root)),
                        'issue': 'Hardcoded secrets in Docker file',
                        'severity': 'high',
                        'recommendation': 'Use environment variables or secrets management'
                    })
                    
            except Exception as e:
                issues.append({
                    'file': str(docker_file.relative_to(self.repo_root)),
                    'error': f'Could not scan Docker file: {e}'
                })
        
        return issues
    
    def audit_environment_files(self) -> Dict[str, List]:
        """Audit environment files for security"""
        findings = {'critical': [], 'warning': [], 'info': []}
        
        env_files = list(self.repo_root.glob('.env*'))
        
        for env_file in env_files:
            if env_file.name == '.env.example':
                findings['info'].append({
                    'file': str(env_file.relative_to(self.repo_root)),
                    'status': 'Template file found - good practice'
                })
                continue
            
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    
                # Check for weak secrets
                weak_patterns = [
                    'your-.*-here',
                    'change-me',
                    'development-.*',
                    'test',
                    'demo'
                ]
                
                for pattern in weak_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        findings['warning'].append({
                            'file': str(env_file.relative_to(self.repo_root)),
                            'issue': 'Contains placeholder/weak values',
                            'recommendation': 'Replace with actual secure values'
                        })
                        break
                        
            except Exception as e:
                findings['info'].append({
                    'file': str(env_file.relative_to(self.repo_root)),
                    'error': f'Could not scan env file: {e}'
                })
        
        return findings
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during scanning"""
        skip_patterns = [
            '**/test*',
            '**/venv/**',
            '**/__pycache__/**',
            '**/node_modules/**',
            '**/.git/**',
            '**/backup/**'
        ]
        
        for pattern in skip_patterns:
            if file_path.match(pattern):
                return True
        return False
    
    def _is_placeholder(self, text: str) -> bool:
        """Check if text appears to be a placeholder"""
        placeholders = [
            'your-', 'change-me', 'example', 'demo', 'test', 
            'placeholder', 'replace-me', 'development-'
        ]
        
        text_lower = text.lower()
        return any(placeholder in text_lower for placeholder in placeholders)
    
    def generate_report(self) -> str:
        """Generate comprehensive security audit report"""
        
        print("🔒 Running KBI Labs Security Audit...")
        
        # Run all audits
        secrets_findings = self.audit_secrets()
        file_permissions = self.audit_file_permissions()
        dependencies = self.audit_dependencies()
        docker_issues = self.audit_docker_security()
        env_findings = self.audit_environment_files()
        
        # Generate report
        report = "# KBI Labs Security Audit Report\n\n"
        report += f"Generated: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}\n\n"
        
        # Executive Summary
        critical_count = len(secrets_findings['critical'])
        warning_count = len(secrets_findings['warning']) + len(file_permissions) + len(docker_issues)
        
        report += "## Executive Summary\n\n"
        if critical_count == 0:
            report += "✅ **No critical security issues found**\n\n"
        else:
            report += f"❌ **{critical_count} critical security issues found**\n\n"
        
        if warning_count > 0:
            report += f"⚠️  **{warning_count} warnings require attention**\n\n"
        
        # Critical Issues
        if secrets_findings['critical']:
            report += "## 🚨 Critical Issues\n\n"
            for issue in secrets_findings['critical']:
                report += f"- **{issue['type']}** in `{issue['file']}` (line {issue['line']})\n"
            report += "\n"
        
        # Warnings
        warnings_total = secrets_findings['warning'] + file_permissions + docker_issues
        if warnings_total:
            report += "## ⚠️ Warnings\n\n"
            
            # Secret warnings
            if secrets_findings['warning']:
                report += "### Potential Secrets\n"
                for issue in secrets_findings['warning']:
                    report += f"- {issue['type']} in `{issue['file']}`: `{issue['content']}`\n"
                report += "\n"
            
            # File permission issues
            if file_permissions:
                report += "### File Permissions\n"
                for issue in file_permissions:
                    report += f"- `{issue['file']}`: {issue['issue']} (permissions: {issue['permissions']})\n"
                report += "\n"
            
            # Docker issues
            if docker_issues:
                report += "### Docker Security\n"
                for issue in docker_issues:
                    if 'error' not in issue:
                        report += f"- `{issue['file']}`: {issue['issue']} ({issue['severity']} severity)\n"
                report += "\n"
        
        # Environment Files
        if env_findings['warning'] or env_findings['info']:
            report += "## 📋 Environment Configuration\n\n"
            for finding in env_findings['warning']:
                report += f"- ⚠️  `{finding['file']}`: {finding['issue']}\n"
            for finding in env_findings['info']:
                report += f"- ℹ️  `{finding['file']}`: {finding.get('status', finding.get('error', ''))}\n"
            report += "\n"
        
        # Dependencies
        if 'vulnerabilities' in dependencies:
            report += "## 📦 Dependency Vulnerabilities\n\n"
            if dependencies['vulnerabilities']:
                for vuln in dependencies['vulnerabilities']:
                    report += f"- **{vuln.get('package')}** {vuln.get('installed_version', '')}: {vuln.get('advisory', '')}\n"
            else:
                report += "✅ No known vulnerabilities in dependencies\n"
            report += "\n"
        elif 'info' in dependencies:
            report += "## 📦 Dependencies\n\n"
            for info in dependencies['info']:
                report += f"- ℹ️  {info}\n"
            report += "\n"
        
        # Recommendations
        report += "## 🔧 Recommendations\n\n"
        report += "1. **Generate secure secrets**: Run `python scripts/generate_secrets.py`\n"
        report += "2. **Set proper file permissions**: `chmod 600 .env*`\n"
        report += "3. **Use environment variables**: Never commit secrets to version control\n"
        report += "4. **Regular audits**: Run this script regularly, especially before deployments\n"
        report += "5. **Dependency scanning**: Install and use `safety` for vulnerability scanning\n"
        report += "6. **Secret management**: Consider using tools like HashiCorp Vault for production\n\n"
        
        return report

def main():
    repo_root = Path(__file__).parent.parent
    auditor = SecurityAuditor(repo_root)
    
    report = auditor.generate_report()
    
    # Write report
    report_path = repo_root / 'SECURITY_AUDIT.md'
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"📋 Security audit report written to: {report_path}")
    
    # Print summary to console
    lines = report.split('\n')
    summary_lines = []
    in_summary = False
    
    for line in lines:
        if '## Executive Summary' in line:
            in_summary = True
            continue
        elif in_summary and line.startswith('## '):
            break
        elif in_summary and line.strip():
            summary_lines.append(line)
    
    if summary_lines:
        print("\n" + "="*50)
        print("SECURITY AUDIT SUMMARY")
        print("="*50)
        for line in summary_lines:
            print(line)

if __name__ == "__main__":
    main()