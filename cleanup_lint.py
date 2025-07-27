#!/usr/bin/env python3
"""Clean up common Python linting issues"""

import os
import re

def clean_python_files():
    """Clean up common Python linting issues"""
    issues_fixed = 0
    
    for root, dirs, files in os.walk('src'):
        # Skip cache directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Remove trailing whitespace
                    lines = content.split('\n')
                    lines = [line.rstrip() for line in lines]
                    content = '\n'.join(lines)
                    
                    # Ensure file ends with newline
                    if content and not content.endswith('\n'):
                        content += '\n'
                    
                    # Fix multiple blank lines (max 2)
                    content = re.sub(r'\n\n\n+', '\n\n\n', content)
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        issues_fixed += 1
                        print(f'Fixed: {file_path}')
                        
                except Exception as e:
                    print(f'Error processing {file_path}: {e}')
    
    return issues_fixed

if __name__ == '__main__':
    fixed = clean_python_files()
    print(f'Fixed linting issues in {fixed} files')