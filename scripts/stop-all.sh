#!/bin/bash
# stop-all.sh - Script to stop all HoanCau AI services

echo "🛑 Stopping HoanCau AI Suite..."

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "🔪 Killing process on port $port (PID: $pid)"
        kill -9 $pid
        sleep 1
    else
        echo "✅ Port $port is already free"
    fi
}

# Read saved PIDs if available
if [ -f ".pids" ]; then
    echo "📖 Reading saved process IDs..."
    source .pids
    
    if [ ! -z "$API_PID" ]; then
        echo "🔪 Stopping API Server (PID: $API_PID)"
        kill $API_PID 2>/dev/null
    fi
    
    if [ ! -z "$STREAMLIT_PID" ]; then
        echo "🔪 Stopping Streamlit App (PID: $STREAMLIT_PID)"
        kill $STREAMLIT_PID 2>/dev/null
    fi
    
    if [ ! -z "$ELECTRON_PID" ]; then
        echo "🔪 Stopping Desktop App (PID: $ELECTRON_PID)"
        kill $ELECTRON_PID 2>/dev/null
    fi
    
    rm -f .pids
    echo "🗑️  Removed .pids file"
fi

# Kill processes on known ports
echo "🔍 Checking and cleaning up ports..."
kill_port 8000  # API Server
kill_port 8501  # Streamlit

# Kill any Python processes running our scripts
echo "🐍 Stopping Python processes..."
pkill -f "api_server.py" 2>/dev/null
pkill -f "streamlit run" 2>/dev/null

# Kill any Electron processes
echo "⚡ Stopping Electron processes..."
pkill -f "electron" 2>/dev/null

# Clean up any remaining processes
echo "🧹 Final cleanup..."
sleep 2

echo "✅ All HoanCau AI services have been stopped"
echo "💡 You can restart with: ./run-all.sh"
