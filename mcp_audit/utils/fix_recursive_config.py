#!/usr/bin/env python3
"""
Fix Recursive MCP Configuration

Detects and fixes recursive proxy configurations in .cursor/mcp.json
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_recursive_config(config: Dict) -> Dict:
    """Detect recursive proxy configurations and extract the original."""
    
    results = {
        "is_recursive": False,
        "recursion_depth": 0,
        "original_command": None,
        "original_args": None,
        "server_name": None
    }
    
    if "mcpServers" not in config:
        return results
    
    for server_name, server_config in config["mcpServers"].items():
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        
        # Check if this is a proxy configuration
        if command == "python" and len(args) >= 2 and args[0] == "-m" and args[1] == "mcp_audit.interceptors.mcp_proxy_runner":
            results["is_recursive"] = True
            results["server_name"] = server_name
            
            # Parse the proxy arguments to extract original
            original_command, original_args, depth = extract_original_from_proxy_args(args)
            results["original_command"] = original_command
            results["original_args"] = original_args
            results["recursion_depth"] = depth
            
            logger.info(f"🔍 Detected recursive proxy for '{server_name}' (depth: {depth})")
            break
    
    return results

def extract_original_from_proxy_args(args: List[str]) -> tuple:
    """Extract original command from potentially nested proxy args."""
    depth = 0
    current_args = args[:]
    
    while (len(current_args) >= 2 and 
           current_args[0] == "-m" and 
           current_args[1] == "mcp_audit.interceptors.mcp_proxy_runner"):
        
        depth += 1
        
        # Find the target command and args
        try:
            target_cmd_idx = current_args.index("--target-command")
            target_args_idx = current_args.index("--target-args")
            
            original_command = current_args[target_cmd_idx + 1]
            original_args = current_args[target_args_idx + 1:]
            
            # If the original command is also a proxy, continue unwrapping
            if original_command == "python" and len(original_args) >= 2:
                current_args = original_args[:]
            else:
                return original_command, original_args, depth
                
        except (ValueError, IndexError):
            logger.error("Malformed proxy configuration")
            return None, None, depth
    
    return current_args[0] if current_args else None, current_args[1:] if len(current_args) > 1 else [], depth

def create_clean_config(config: Dict, detection_result: Dict) -> Dict:
    """Create a clean configuration without recursive proxies."""
    clean_config = config.copy()
    
    if detection_result["is_recursive"] and detection_result["server_name"]:
        server_name = detection_result["server_name"]
        
        clean_config["mcpServers"][server_name] = {
            "command": detection_result["original_command"],
            "args": detection_result["original_args"]
        }
        
        logger.info(f"✅ Created clean config for '{server_name}': {detection_result['original_command']} {detection_result['original_args']}")
    
    return clean_config

def main():
    """Main cleanup routine."""
    print("🔧 MCP Recursive Configuration Fixer")
    print("=" * 50)
    
    # Find config file
    config_path = Path(".cursor/mcp.json")
    if not config_path.exists():
        config_path = Path.home() / ".cursor" / "mcp.json"
    
    if not config_path.exists():
        print("❌ No MCP configuration file found")
        return
    
    print(f"📁 Found config: {config_path}")
    
    # Load current config
    try:
        with open(config_path, 'r') as f:
            current_config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Detect recursion
    detection = detect_recursive_config(current_config)
    
    if not detection["is_recursive"]:
        print("✅ Configuration is already clean - no recursion detected")
        return
    
    print(f"⚠️ Recursion detected:")
    print(f"   Server: {detection['server_name']}")
    print(f"   Depth: {detection['recursion_depth']} layers")
    print(f"   Original: {detection['original_command']} {detection['original_args']}")
    
    # Create clean config
    clean_config = create_clean_config(current_config, detection)
    
    # Backup original
    backup_path = config_path.with_suffix('.json.backup')
    try:
        with open(backup_path, 'w') as f:
            json.dump(current_config, f, indent=2)
        print(f"💾 Backup saved: {backup_path}")
    except Exception as e:
        print(f"⚠️ Failed to create backup: {e}")
    
    # Write clean config
    try:
        with open(config_path, 'w') as f:
            json.dump(clean_config, f, indent=2)
        print(f"✅ Fixed configuration written to: {config_path}")
        
        print("\n🎯 Summary:")
        print(f"   Removed {detection['recursion_depth']} recursive proxy layers")
        print(f"   Restored original: {detection['original_command']} {detection['original_args']}")
        print("   Backup available if needed")
        
    except Exception as e:
        print(f"❌ Failed to write clean config: {e}")

if __name__ == "__main__":
    main() 