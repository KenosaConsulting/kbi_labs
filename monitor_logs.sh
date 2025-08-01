#!/bin/bash
# Live monitoring of API logs with highlighting

echo "📊 Monitoring KBI Labs API Logs (Ctrl+C to stop)"
echo "Legend: 🟢 Success | 🔴 Error | 🟡 Warning | 🔵 Info"
echo "=================================================="

sudo journalctl -u kbi-api -f | while read line; do
    if echo "$line" | grep -q "ERROR\|Exception\|Failed"; then
        echo "🔴 $line"
    elif echo "$line" | grep -q "WARNING"; then
        echo "🟡 $line"
    elif echo "$line" | grep -q "200 OK"; then
        echo "🟢 $line"
    else
        echo "🔵 $line"
    fi
done
