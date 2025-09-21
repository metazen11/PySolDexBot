#!/bin/bash

echo "🔥 Starting Enhanced Token Scanner with Activity Tracking"
echo "======================================================="

# Enhance database schema first
echo "📊 Setting up activity tracking..."
python3 enhance_activity_tracking.py

# Start the main scanner
echo "🔍 Starting token scanner..."
python3 main.py &
SCANNER_PID=$!

# Wait for scanner to gather some data
echo "⏳ Waiting for initial token discovery..."
sleep 30

# Start activity monitoring
echo "📈 Starting activity monitoring..."
python3 -c "
import asyncio
from enhance_activity_tracking import scan_recent_tokens_for_activity

async def monitor_activity():
    while True:
        print('🔄 Checking token activity...')
        await scan_recent_tokens_for_activity()
        print('⏱️  Waiting 5 minutes before next activity check...')
        await asyncio.sleep(300)  # 5 minutes

asyncio.run(monitor_activity())
" &
ACTIVITY_PID=$!

# Start enhanced dashboard
echo "🖥️  Starting enhanced dashboard..."
python3 enhanced_dashboard.py &
DASHBOARD_PID=$!

echo ""
echo "✅ All services started!"
echo "==============================="
echo "📊 Enhanced Dashboard: http://localhost:8081"
echo "🔍 Scanner PID: $SCANNER_PID"
echo "📈 Activity Monitor PID: $ACTIVITY_PID"
echo "🖥️  Dashboard PID: $DASHBOARD_PID"
echo ""
echo "🛑 To stop all services:"
echo "   kill $SCANNER_PID $ACTIVITY_PID $DASHBOARD_PID"
echo ""
echo "🔥 The system will now continuously:"
echo "   - Scan for new tokens every 60 seconds"
echo "   - Check trading activity every 5 minutes"
echo "   - Show active tokens with momentum indicators"
echo ""

# Save PIDs
echo "$SCANNER_PID" > scanner.pid
echo "$ACTIVITY_PID" > activity.pid
echo "$DASHBOARD_PID" > enhanced_dashboard.pid

wait