#!/usr/bin/env python3
"""Debug rate limiting issue"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from tools.security_framework import NetworkSecurityManager

# Test the rate limiting logic
network_security = NetworkSecurityManager()
test_agent_id = "test_agent"

print("Testing rate limiting logic:")
print(f"Rate limit: {network_security.rate_limits['requests_per_hour']}")

for i in range(102):  # Test a few more than the limit
    is_allowed, reason = network_security.check_rate_limit(test_agent_id, "requests")
    usage_count = len(network_security.agent_usage[test_agent_id]["requests"])
    print(f"Request {i}: allowed={is_allowed}, usage_count={usage_count}, reason={reason}")
    
    if i >= 99:  # Focus on the boundary
        print(f"  --> Request {i} (0-indexed): allowed={is_allowed}, expected_blocked={i >= 100}")
