#!/usr/bin/env python3
"""Script to update Pydantic validators from V1 to V2 style."""

import re
import sys
from pathlib import Path

def update_validators(file_path):
    """Update validators in a file from V1 to V2 style.
    
    Args:
        file_path: Path to the file to update.
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace imports
    content = content.replace(
        'from pydantic import BaseModel, Field, validator',
        'from pydantic import BaseModel, Field, field_validator'
    )
    
    # Replace validator decorators
    content = re.sub(
        r'@validator\("([^"]+)", pre=True\)',
        r'@field_validator("\1", mode="before")',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Updated validators in {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_validators.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File {file_path} does not exist")
        sys.exit(1)
    
    update_validators(file_path)
