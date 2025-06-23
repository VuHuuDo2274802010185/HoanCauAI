#!/bin/bash
# run-all.sh - Script to run all HoanCau AI services

echo "🎯 Starting HoanCau AI Complete Suite..."

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "🔪 Killing process on port $port (PID: $pid)"
        kill -9 $pid
        sleep 2
    fi
}

# Check and setup Python environment
setup_python() {
    echo "🐍 Setting up Python environment..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found. Please install Python 3.10+"
        exit 1
    fi
    
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ Python environment ready"
}

# Setup Node.js environment
setup_node() {
    echo "📦 Setting up Node.js environment..."
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js not found. Please install Node.js"
        exit 1
    fi
    
    if [ ! -d "desktop/node_modules" ]; then
        echo "📥 Installing Node.js dependencies..."
        cd desktop
        npm install
        cd ..
    fi
    
    echo "✅ Node.js environment ready"
}

# Start API Server
start_api() {
    echo "🚀 Starting API Server..."
    source venv/bin/activate
    
    # Check if port 8000 is free
    if check_port 8000; then
        echo "⚠️  Port 8000 is in use"
        kill_port 8000
    fi
    
    cd api
    python api_server.py &
    API_PID=$!
    cd ..
    echo "📡 API Server started (PID: $API_PID) - http://localhost:8000"
}

# Start Streamlit App
start_streamlit() {
    echo "🌟 Starting Streamlit App..."
    source venv/bin/activate
    
    # Check if port 8501 is free
    if check_port 8501; then
        echo "⚠️  Port 8501 is in use"
        kill_port 8501
    fi
    
    cd main_engine
    streamlit run app.py --server.port 8501 --server.headless true &
    STREAMLIT_PID=$!
    cd ..
    echo "📊 Streamlit App started (PID: $STREAMLIT_PID) - http://localhost:8501"
}

# Start Electron App
start_electron() {
    echo "💻 Starting Desktop App..."
    cd desktop
    npm run electron-dev &
    ELECTRON_PID=$!
    cd ..
    echo "🖥️  Desktop App started (PID: $ELECTRON_PID)"
}

# Wait for services to be ready
wait_for_services() {
    echo "⏳ Waiting for services to start..."
    
    # Wait for API server
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API Server is ready"
            break
        fi
        echo "⏳ Waiting for API Server... ($i/30)"
        sleep 2
    done
    
    # Wait for Streamlit
    for i in {1..30}; do
        if curl -s http://localhost:8501 > /dev/null 2>&1; then
            echo "✅ Streamlit App is ready"
            break
        fi
        echo "⏳ Waiting for Streamlit App... ($i/30)"
        sleep 2
    done
}

# Show status
show_status() {
    echo ""
    echo "🎉 HoanCau AI Suite is running!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 API Server:      http://localhost:8000"
    echo "📖 API Docs:        http://localhost:8000/docs"
    echo "🎯 Widget Demo:     http://localhost:8000/widget"
    echo "📊 Streamlit App:   http://localhost:8501"
    echo "💻 Desktop App:     Running in Electron window"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📝 Usage:"
    echo "  • Open widget demo to test embeddable features"
    echo "  • Use Streamlit app for full web interface"
    echo "  • Desktop app provides native experience"
    echo ""
    echo "🛑 To stop all services: Ctrl+C or ./stop-all.sh"
    echo ""
}

# Save PIDs for cleanup
save_pids() {
    cat > .pids << EOF
API_PID=$API_PID
STREAMLIT_PID=$STREAMLIT_PID
ELECTRON_PID=$ELECTRON_PID
EOF
    echo "💾 Process IDs saved to .pids"
}

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down HoanCau AI Suite..."
    
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
    
    # Kill any remaining processes on our ports
    kill_port 8000
    kill_port 8501
    
    rm -f .pids
    echo "✅ All services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo "🚀 HoanCau AI Complete Suite Launcher"
    echo "======================================"
    
    # Setup environments
    setup_python
    setup_node
    
    # Start services
    start_api
    sleep 3
    
    start_streamlit
    sleep 3
    
    # Ask if user wants to start Electron
    read -p "🖥️  Start Desktop App? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_electron
        sleep 2
    fi
    
    # Wait for services
    wait_for_services
    
    # Save PIDs
    save_pids
    
    # Show status
    show_status
    
    # Keep script running
    echo "⏳ Services are running. Press Ctrl+C to stop all services."
    while true; do
        sleep 1
    done
}

# Run main function
main
