#!/usr/bin/env python3
"""
MCP Server Verification Script

This script verifies that Blender and Fetch MCP servers are properly installed
and accessible through the UV package manager.
"""

import subprocess
import sys
import json
from pathlib import Path

def run_command(command, capture_output=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_uv_installation():
    """Check if UV package manager is installed and accessible."""
    print("🔍 Checking UV installation...")
    success, stdout, stderr = run_command("uvx --version")
    
    if success:
        print(f"✅ UV is installed: {stdout.strip()}")
        return True
    else:
        print(f"❌ UV not found: {stderr}")
        return False

def check_mcp_server(server_name, command):
    """Check if an MCP server is accessible."""
    print(f"🔍 Checking {server_name} MCP server...")
    
    # Try to get help/version info
    success, stdout, stderr = run_command(f"{command} --help")
    
    if success:
        print(f"✅ {server_name} MCP server is accessible")
        return True
    else:
        print(f"❌ {server_name} MCP server not accessible: {stderr}")
        return False

def check_config_file():
    """Check if MCP configuration file exists."""
    print("🔍 Checking MCP configuration file...")
    
    config_path = Path(".claude/mcp_config.json")
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            servers = config.get('mcpServers', {})
            print(f"✅ Configuration file found with {len(servers)} servers:")
            
            for server_name in servers.keys():
                print(f"   - {server_name}")
            
            return True
        except json.JSONDecodeError:
            print("❌ Configuration file exists but contains invalid JSON")
            return False
    else:
        print("❌ Configuration file not found")
        return False

def check_python_packages():
    """Check if required Python packages are installed."""
    print("🔍 Checking Python packages...")
    
    packages = [
        "mcp",
        "blender-mcp", 
        "mcp-server-fetch"
    ]
    
    all_installed = True
    
    for package in packages:
        success, stdout, stderr = run_command(f"pip show {package}")
        if success:
            # Extract version from pip show output
            for line in stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    print(f"✅ {package}: {version}")
                    break
        else:
            print(f"❌ {package}: Not installed")
            all_installed = False
    
    return all_installed

def main():
    """Main verification function."""
    print("🚀 MCP Server Setup Verification\n")
    print("=" * 50)
    
    checks = [
        ("UV Package Manager", check_uv_installation),
        ("Python Packages", check_python_packages),
        ("Configuration File", check_config_file),
        ("Blender MCP Server", lambda: check_mcp_server("Blender", "uvx blender-mcp")),
        ("Fetch MCP Server", lambda: check_mcp_server("Fetch", "uvx mcp-server-fetch")),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! MCP servers are ready to use.")
        print("\n📝 Next steps:")
        print("   1. Install Blender addon (see docs/MCP_SETUP_GUIDE.md)")
        print("   2. Configure Claude Desktop or Cursor IDE")
        print("   3. Start using MCP servers!")
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please review the setup.")
        print("\n📖 See docs/MCP_SETUP_GUIDE.md for troubleshooting.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)