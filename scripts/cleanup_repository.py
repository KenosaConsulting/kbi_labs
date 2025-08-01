#!/usr/bin/env python3
"""
Repository Cleanup Script for KBI Labs
Identifies and optionally removes backup, old, and broken files
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict

class RepositoryCleanup:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.backup_patterns = [
            '*backup*', '*old*', '*broken*', '*.bak', '*.backup',
            '*_backup.py', '*_old.py', '*_broken.py', '*~'
        ]
        self.test_file_patterns = [
            'test_*.py', '*_test.py', 'debug_*.py'
        ]
        
    def find_cleanup_candidates(self) -> Dict[str, List[Path]]:
        """Find files that are candidates for cleanup"""
        candidates = {
            'backup_files': [],
            'broken_files': [],
            'old_files': [],
            'duplicate_apis': [],
            'test_files': []
        }
        
        for pattern in self.backup_patterns:
            for file_path in self.repo_root.rglob(pattern):
                if file_path.is_file():
                    if 'backup' in file_path.name.lower():
                        candidates['backup_files'].append(file_path)
                    elif 'broken' in file_path.name.lower():
                        candidates['broken_files'].append(file_path)
                    elif 'old' in file_path.name.lower():
                        candidates['old_files'].append(file_path)
        
        # Find duplicate API files
        api_files = list(self.repo_root.rglob('*api*.py'))
        api_names = {}
        
        for api_file in api_files:
            base_name = api_file.name.replace('_backup', '').replace('_old', '').replace('_broken', '')
            if base_name not in api_names:
                api_names[base_name] = []
            api_names[base_name].append(api_file)
        
        for base_name, files in api_names.items():
            if len(files) > 1:
                # Keep the most recent, mark others as duplicates
                files_sorted = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
                candidates['duplicate_apis'].extend(files_sorted[1:])
        
        # Find test files outside test directories
        for pattern in self.test_file_patterns:
            for file_path in self.repo_root.rglob(pattern):
                if file_path.is_file() and 'test' not in str(file_path.parent).lower():
                    candidates['test_files'].append(file_path)
        
        return candidates
    
    def analyze_files(self, candidates: Dict[str, List[Path]]) -> Dict[str, int]:
        """Analyze the cleanup candidates"""
        analysis = {}
        total_size = 0
        
        for category, files in candidates.items():
            size = sum(f.stat().st_size for f in files if f.exists())
            analysis[category] = {
                'count': len(files),
                'size_mb': round(size / (1024 * 1024), 2)
            }
            total_size += size
        
        analysis['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        return analysis
    
    def create_cleanup_script(self, candidates: Dict[str, List[Path]]) -> str:
        """Create a bash script for cleanup"""
        script_content = """#!/bin/bash
# KBI Labs Repository Cleanup Script
# Generated automatically - review before running

set -e

echo "🧹 Starting KBI Labs repository cleanup..."

# Create backup directory
mkdir -p .cleanup_backup/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".cleanup_backup/$(date +%Y%m%d_%H%M%S)"

echo "📦 Backup directory: $BACKUP_DIR"

"""

        for category, files in candidates.items():
            if files:
                script_content += f"\n# {category.replace('_', ' ').title()}\n"
                script_content += f"echo \"Cleaning up {len(files)} {category}...\"\n"
                
                for file_path in files:
                    rel_path = file_path.relative_to(self.repo_root)
                    script_content += f"# {rel_path}\n"
                    script_content += f"mkdir -p \"$BACKUP_DIR/$(dirname '{rel_path}')\"\n"
                    script_content += f"cp '{rel_path}' \"$BACKUP_DIR/{rel_path}\" 2>/dev/null || true\n"
                    script_content += f"rm '{rel_path}'\n\n"

        script_content += """
echo "✅ Cleanup completed!"
echo "📦 Backup created in: $BACKUP_DIR"
echo "🗑️  To permanently delete backups: rm -rf .cleanup_backup"
"""

        return script_content
    
    def generate_report(self) -> str:
        """Generate a cleanup report"""
        candidates = self.find_cleanup_candidates()
        analysis = self.analyze_files(candidates)
        
        report = "# KBI Labs Repository Cleanup Report\n\n"
        report += f"Generated: {os.popen('date').read().strip()}\n\n"
        
        report += "## Summary\n\n"
        total_files = sum(len(files) for files in candidates.values())
        report += f"- **Total files identified for cleanup**: {total_files}\n"
        report += f"- **Total size**: {analysis['total_size_mb']} MB\n\n"
        
        report += "## Cleanup Candidates\n\n"
        
        for category, files in candidates.items():
            if files:
                report += f"### {category.replace('_', ' ').title()}\n"
                report += f"- Count: {analysis[category]['count']}\n"
                report += f"- Size: {analysis[category]['size_mb']} MB\n\n"
                
                report += "Files:\n"
                for file_path in sorted(files):
                    rel_path = file_path.relative_to(self.repo_root)
                    size_kb = round(file_path.stat().st_size / 1024, 1)
                    report += f"- `{rel_path}` ({size_kb} KB)\n"
                report += "\n"
        
        # Create cleanup script
        cleanup_script = self.create_cleanup_script(candidates)
        
        return report, cleanup_script

def main():
    repo_root = Path(__file__).parent.parent
    cleanup = RepositoryCleanup(repo_root)
    
    print("🔍 Analyzing repository for cleanup candidates...")
    report, script = cleanup.generate_report()
    
    # Write report
    report_path = repo_root / 'CLEANUP_REPORT.md'
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Write cleanup script
    script_path = repo_root / 'cleanup_repository.sh'
    with open(script_path, 'w') as f:
        f.write(script)
    
    os.chmod(script_path, 0o755)  # Make executable
    
    print(f"📋 Cleanup report written to: {report_path}")
    print(f"🔧 Cleanup script written to: {script_path}")
    print()
    print("Next steps:")
    print("1. Review the cleanup report")
    print("2. Run the cleanup script: ./cleanup_repository.sh")
    print("3. Test the application after cleanup")

if __name__ == "__main__":
    main()