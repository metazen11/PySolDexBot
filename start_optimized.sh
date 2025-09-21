#!/bin/bash

# Optimized Solana Token Security Scanner Startup Script

echo "🛡️  Starting Solana Token Security Scanner (Optimized Version)"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.7+"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "⚠️  requirements.txt not found. Make sure dependencies are installed manually."
fi

# Create logs directory
mkdir -p logs

# Set environment variables for optimal performance
export PYTHONUNBUFFERED=1
export CHECK_INTERVAL=30
export SECURITY_MODE=normal

echo ""
echo "🚀 Starting services..."
echo ""

# Start the optimized scanner
echo "Starting optimized token scanner..."
nohup python3 optimized_scanner.py > logs/scanner.log 2>&1 &
SCANNER_PID=$!
echo "✅ Scanner started (PID: $SCANNER_PID)"

# Wait a moment for scanner to initialize
sleep 3

# Start the enhanced dashboard
echo "Starting enhanced dashboard..."
nohup python3 enhanced_dashboard.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "✅ Dashboard started (PID: $DASHBOARD_PID)"

# Wait for services to fully start
sleep 5

echo ""
echo "🎉 Services started successfully!"
echo "=================================================="
echo "📊 Dashboard URL: http://localhost:8080"
echo "📈 Scanner PID: $SCANNER_PID"
echo "🖥️  Dashboard PID: $DASHBOARD_PID"
echo ""
echo "📋 Logs:"
echo "   Scanner: logs/scanner.log"
echo "   Dashboard: logs/dashboard.log"
echo ""
echo "🛑 To stop services:"
echo "   kill $SCANNER_PID $DASHBOARD_PID"
echo ""
echo "💡 Pro Tips:"
echo "   - Set SECURITY_MODE=conservative for stricter filtering"
echo "   - Set SECURITY_MODE=aggressive for broader discovery"
echo "   - Monitor logs/scanner.log for real-time activity"
echo ""

# Save PIDs for easy stopping
echo "$SCANNER_PID" > scanner.pid
echo "$DASHBOARD_PID" > dashboard.pid

echo "🔍 Scanner will begin finding tokens within 30 seconds..."
echo "🎯 Check the dashboard for real-time results!"