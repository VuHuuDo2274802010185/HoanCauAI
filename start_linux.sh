#!/usr/bin/env bash
# HoanCau AI - Enhanced Run Script for macOS/Linux
set -e

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# 0) Ensure we're in project root
if [ ! -f "src/main_engine/app.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Handle special commands first (before initialization)
MODE=$1
if [ "$MODE" = "check" ]; then
    print_status "🏥 Running health check..."
    echo ""
    if [ -f "scripts/quick_check.py" ]; then
        python3 scripts/quick_check.py
    elif [ -f "scripts/health_check_enhanced.py" ]; then
        python3 scripts/health_check_enhanced.py
    else
        python3 scripts/health_check.py
    fi
    exit $?
fi

if [ "$MODE" = "help" ]; then
    print_status "📖 Available commands:"
    echo ""
    echo "  ./start_linux.sh           - Start web interface (default)"
    echo "  ./start_linux.sh dev       - Development mode with auto-reload"
    echo "  ./start_linux.sh debug     - Debug mode with verbose logging"
    echo "  ./start_linux.sh cli       - Command line interface"
    echo "  ./start_linux.sh select    - Select top 5 CVs"
    echo "  ./start_linux.sh check     - Run health check"
    echo "  ./start_linux.sh help      - Show this help"
    echo ""
    exit 0
fi

# Function to show progress bar
show_progress() {
    local current=$1
    local total=$2
    local message=$3
    local percent=$((current * 100 / total))
    local filled=$((percent / 2))
    local empty=$((50 - filled))
    
    printf "\r${BLUE}[%3d%%]${NC} [" "$percent"
    printf "%*s" "$filled" | tr ' ' '='
    printf "%*s" "$empty" | tr ' ' ' '
    printf "] %s" "$message"
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking system dependencies..."
    show_progress 1 7 "Checking Python..."
    sleep 0.5
    
    # Check for python3
    if ! command -v python3 >/dev/null 2>&1; then
        print_error "python3 is required but not found."
        exit 1
    fi
    
    show_progress 2 7 "Python found: $(python3 --version)"
    sleep 0.5
}

# Function to setup virtual environment
setup_venv() {
    show_progress 3 7 "Setting up virtual environment..."
    sleep 0.5
    
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    show_progress 4 7 "Activating virtual environment..."
    sleep 0.5
    
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        print_success "Virtual environment activated."
    else
        print_warning ".venv not found, using system Python."
    fi
}

# Function to install/update dependencies
install_deps() {
    show_progress 5 7 "Checking dependencies..."
    sleep 0.5
    
    if [ -f "requirements.txt" ]; then
        print_status "Installing/updating Python packages..."
        pip install -q -r requirements.txt
        print_success "Dependencies installed."
    fi
}

# Function to validate installation
validate_installation() {
    show_progress 6 7 "Validating installation..."
    sleep 0.5
    
    # Check if streamlit is available
    if ! python3 -c "import streamlit" 2>/dev/null; then
        print_error "Streamlit not found. Installing..."
        pip install streamlit
    fi
    
    # Check if main modules are available
    if [ ! -f "src/main_engine/app.py" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Create streamlit config for better stability
    mkdir -p ~/.streamlit
    cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
enableCORS = false
enableXsrfProtection = false
maxUploadSize = 200
enableWebsocketCompression = false

[browser]
gatherUsageStats = false

[logger]
level = "error"
messageFormat = "%(asctime)s %(message)s"
EOF
}

print_status "🚀 HoanCau AI Startup Sequence"
echo ""

# Run all checks
check_dependencies
setup_venv
install_deps
validate_installation

# Health check option - moved before other processing
shift || true

case "$MODE" in
    cli)
        print_status "🔧 Running CLI processor..."
        echo ""
        python3 src/main_engine/main.py "$@"
        ;;
    select)
        print_status "🔍 Selecting TOP 5 resumes..."
        echo ""
        python3 src/main_engine/select_top5.py "$@"
        ;;
    dev)
        print_status "🛠️ Starting development server with auto-reload..."
        echo ""
        print_status "Development mode with enhanced error handling..."
        
        # Set environment variables for better debugging
        export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
        export STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false
        
        streamlit run src/main_engine/app.py \
            --server.runOnSave=true \
            --server.address=0.0.0.0 \
            --server.port=8501 \
            --server.headless=true \
            --server.enableCORS=false \
            --server.enableXsrfProtection=false \
            --logger.level=info
        ;;
    debug)
        print_status "🐛 Starting in debug mode..."
        echo ""
        print_status "Debug mode with verbose logging..."
        
        export STREAMLIT_LOGGER_LEVEL=debug
        export STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false
        
        streamlit run src/main_engine/app.py \
            --server.address=0.0.0.0 \
            --server.port=8501 \
            --server.headless=true \
            --logger.level=debug \
            --server.enableCORS=false
        ;;
    check)
        # This case should not be reached as it's handled above
        print_status "Health check already handled above"
        ;;
    help)
        # This case should not be reached as it's handled above  
        print_status "Help already handled above"
        ;;
    *)
        print_status "🌐 Launching Streamlit UI with auto-recovery..."
        echo ""
        print_status "Server will be available at:"
        print_status "  Local:   http://localhost:8501"
        print_status "  Network: http://0.0.0.0:8501"
        echo ""
        print_status "💡 Features: Auto-restart on errors, Enhanced stability"
        print_status "💡 Tip: Use './start_linux.sh help' to see all available options"
        echo ""
        
        # Use streamlit runner for better error handling
        if [ -f "scripts/streamlit_runner.py" ]; then
            python3 scripts/streamlit_runner.py src/main_engine/app.py 8501
        else
            # Fallback to direct streamlit
            export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
            export STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false
            
            streamlit run src/main_engine/app.py \
                --server.address=0.0.0.0 \
                --server.port=8501 \
                --server.runOnSave=true \
                --server.headless=true \
                --server.enableCORS=false \
                --server.enableXsrfProtection=false \
                --browser.gatherUsageStats=false \
                --logger.level=error \
                --server.maxUploadSize=200
        fi
        ;;
esac
