import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

print("XXXBot Optimization Test")
print("========================")

# Test 1: Config Manager
print("\n1. Testing Config Manager")
try:
    from utils.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    print("OK - Config manager loaded")
    print(f"Protocol: {config.protocol.version}")
    print(f"API Port: {config.wechat_api.port}")
    print(f"Admin Port: {config.admin.port}")
    
except Exception as e:
    print(f"FAIL - Config manager: {e}")

# Test 2: Exception System
print("\n2. Testing Exception System")
try:
    from utils.exceptions import WechatAPIException, create_exception
    
    test_exception = WechatAPIException("Test error", status_code=500)
    print("OK - Exception system loaded")
    print(f"Exception type: {test_exception.__class__.__name__}")
    
except Exception as e:
    print(f"FAIL - Exception system: {e}")

# Test 3: Environment Override
print("\n3. Testing Environment Override")
try:
    import os
    os.environ['WECHAT_API_PORT'] = '8888'
    
    config_manager_env = ConfigManager()
    config_env = config_manager_env.config
    
    if config_env.wechat_api.port == 8888:
        print("OK - Environment override works")
    else:
        print(f"INFO - Port is {config_env.wechat_api.port}")
    
    del os.environ['WECHAT_API_PORT']
    
except Exception as e:
    print(f"FAIL - Environment override: {e}")

print("\nTest completed!") 