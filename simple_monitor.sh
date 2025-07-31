#!/bin/bash

echo "=== KBI Labs API Simple Monitor ==="
echo "Time: $(date)"
echo ""

# Check if API is running
echo "1. API Status:"
if curl -s http://localhost:8001/health > /dev/null; then
    echo "   ✅ API is running"
    echo "   Health: $(curl -s http://localhost:8001/health)"
else
    echo "   ❌ API is not responding"
fi
echo ""

# Check system resources
echo "2. System Resources:"
echo "   CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
echo "   Memory: $(free -m | awk 'NR==2{printf "%.1f%% (Used: %sMB / Total: %sMB)\n", $3*100/$2, $3, $2}')"
echo "   Disk: $(df -h / | awk 'NR==2{printf "%s (Used: %s / Total: %s)\n", $5, $3, $2}')"
echo ""

# Check recent API logs
echo "3. Recent API Activity (last 10 requests):"
sudo journalctl -u kbi-api -n 10 --no-pager | grep -E "GET|POST" | tail -5
echo ""

# Count total requests today
echo "4. Request Summary:"
TOTAL_REQUESTS=$(sudo journalctl -u kbi-api --since today --no-pager | grep -c "HTTP/1.1")
echo "   Total requests today: $TOTAL_REQUESTS"
echo ""

# Check for errors
echo "5. Recent Errors (if any):"
sudo journalctl -u kbi-api -n 100 --no-pager | grep -i "error\|exception\|failed" | tail -3 || echo "   No errors found ✅"
echo ""

echo "=== End of Report ==="
