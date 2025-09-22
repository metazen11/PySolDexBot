#!/bin/bash
# Start Price Momentum Tracker

echo "🔥 Starting Price Momentum Tracker..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the price tracker with logging
python3 price_momentum_tracker.py 2>&1 | tee logs/price_tracker.log