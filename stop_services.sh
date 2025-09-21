#!/bin/bash

# Stop all scanner and dashboard services

echo "🛑 Stopping Solana Token Security Scanner services..."

# Kill by PID files if they exist
if [ -f "scanner.pid" ]; then
    SCANNER_PID=$(cat scanner.pid)
    echo "Stopping scanner (PID: $SCANNER_PID)..."
    kill $SCANNER_PID 2>/dev/null
    rm scanner.pid
fi

if [ -f "dashboard.pid" ]; then
    DASHBOARD_PID=$(cat dashboard.pid)
    echo "Stopping dashboard (PID: $DASHBOARD_PID)..."
    kill $DASHBOARD_PID 2>/dev/null
    rm dashboard.pid
fi

# Kill any remaining Python processes for our scripts
echo "Cleaning up any remaining processes..."
pkill -f "python3.*main.py" 2>/dev/null
pkill -f "python3.*dashboard.py" 2>/dev/null
pkill -f "python3.*optimized_scanner.py" 2>/dev/null
pkill -f "python3.*enhanced_dashboard.py" 2>/dev/null

sleep 2

echo "✅ All services stopped"
echo "📊 Dashboard is no longer accessible"
echo "🔍 Token scanning has stopped"