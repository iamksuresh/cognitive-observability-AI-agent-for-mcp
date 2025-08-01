#!/usr/bin/env python3
"""
Quick User Prompt Logger for MCP Audit

Ultra-simple logging: python quick_log.py "your question here"
Then ask your question in Cursor immediately after.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

def quick_log(prompt):
    """Log user prompt with minimal friction."""
    log_file = Path.home() / ".cursor" / "user_prompts.jsonl"
    log_file.parent.mkdir(exist_ok=True)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_prompt": prompt,
        "logged_at": datetime.now().strftime("%H:%M:%S")
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    print(f"✅ Logged: '{prompt[:50]}...' at {entry['logged_at']}")
    print("💬 Now ask your question in Cursor!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_log.py 'your question'")
        print("Example: python quick_log.py 'what is agent in mastrae?'")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    quick_log(prompt) 