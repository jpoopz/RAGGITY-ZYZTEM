"""
Test CLO 3D Bridge Connection

Quick test script to verify CLO Bridge Listener is working.
Run this after starting the listener in CLO 3D.
"""

import socket
import json
import time
import sys

# Force UTF-8 for Windows console
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "127.0.0.1"
PORT = 51235

def test_connection():
    """Test basic TCP connection"""
    print(f"Testing TCP connection to {HOST}:{PORT}...")
    try:
        with socket.create_connection((HOST, PORT), timeout=2.0) as sock:
            print(f"✅ TCP connection successful!")
            return True
    except ConnectionRefusedError:
        print(f"❌ Connection refused - CLO listener not running")
        return False
    except socket.timeout:
        print(f"❌ Connection timeout - CLO listener not responding")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_handshake():
    """Test ping/pong handshake"""
    print(f"\nTesting handshake protocol...")
    try:
        with socket.create_connection((HOST, PORT), timeout=2.0) as sock:
            # Send ping
            ping = json.dumps({"ping": "clo"}) + "\n"
            sock.sendall(ping.encode('utf-8'))
            print(f"  Sent: {ping.strip()}")
            
            # Receive pong
            sock.settimeout(2.0)
            response = sock.recv(4096).decode('utf-8')
            print(f"  Received: {response.strip()}")
            
            # Parse response
            data = json.loads(response)
            
            if data.get("pong") == "clo":
                print(f"✅ Handshake successful!")
                print(f"   Service: {data.get('service', 'Unknown')}")
                print(f"   Version: {data.get('version', 'Unknown')}")
                return True
            else:
                print(f"❌ Unexpected response: {data}")
                return False
    
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Handshake failed: {e}")
        return False

def test_command():
    """Test a simple command"""
    print(f"\nTesting command execution...")
    try:
        with socket.create_connection((HOST, PORT), timeout=2.0) as sock:
            # Send ping command
            cmd = json.dumps({"cmd": "ping"}) + "\n"
            sock.sendall(cmd.encode('utf-8'))
            print(f"  Sent: {cmd.strip()}")
            
            # Receive response
            sock.settimeout(2.0)
            response = sock.recv(4096).decode('utf-8')
            print(f"  Received: {response.strip()}")
            
            # Parse response
            data = json.loads(response)
            
            if data.get("success"):
                print(f"✅ Command executed successfully!")
                print(f"   Uptime requests: {data.get('uptime_requests', 0)}")
                return True
            else:
                print(f"❌ Command failed: {data.get('error')}")
                return False
    
    except Exception as e:
        print(f"❌ Command test failed: {e}")
        return False

def test_list_commands():
    """Get list of available commands"""
    print(f"\nGetting available commands...")
    try:
        with socket.create_connection((HOST, PORT), timeout=2.0) as sock:
            # Send list_commands
            cmd = json.dumps({"cmd": "list_commands"}) + "\n"
            sock.sendall(cmd.encode('utf-8'))
            
            # Receive response
            sock.settimeout(2.0)
            response = sock.recv(4096).decode('utf-8')
            
            # Parse response
            data = json.loads(response)
            
            if data.get("success"):
                commands = data.get("commands", [])
                print(f"✅ Available commands ({len(commands)}):")
                for cmd in commands:
                    print(f"   - {cmd}")
                return True
            else:
                print(f"❌ Failed to get commands")
                return False
    
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("CLO 3D Bridge Connection Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: TCP connection
    results.append(("TCP Connection", test_connection()))
    
    if not results[0][1]:
        print("\n" + "=" * 60)
        print("❌ FAILED: CLO listener not running")
        print("=" * 60)
        print("\nTo fix:")
        print("1. Open CLO 3D")
        print("2. File > Script > Run Script...")
        print("3. Select: modules\\clo_companion\\clo_bridge_listener.py")
        print("4. Click 'Run'")
        print("\nThen run this test again.")
        return
    
    # Test 2: Handshake
    time.sleep(0.5)
    results.append(("Handshake Protocol", test_handshake()))
    
    # Test 3: Command execution
    time.sleep(0.5)
    results.append(("Command Execution", test_command()))
    
    # Test 4: List commands
    time.sleep(0.5)
    results.append(("List Commands", test_list_commands()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! CLO Bridge is working perfectly!")
        print("\nNext step: Open RAG Control Panel and go to CLO 3D tab")
    else:
        print("\n⚠️ Some tests failed. Check CLO listener console for errors.")

if __name__ == "__main__":
    main()

