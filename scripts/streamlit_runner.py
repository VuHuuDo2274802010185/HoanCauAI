#!/usr/bin/env python3
"""
Streamlit Wrapper with Error Recovery
Automatically restarts Streamlit when websocket errors occur
"""

import os
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class StreamlitRunner:
    def __init__(self, app_path: str, port: int = 8501):
        self.app_path = app_path
        self.port = port
        self.process = None
        self.restart_count = 0
        self.max_restarts = 5
        self.running = True
        
    def start_streamlit(self):
        """Start Streamlit process"""
        cmd = [
            sys.executable, "-m", "streamlit", "run", self.app_path,
            "--server.address=0.0.0.0",
            f"--server.port={self.port}",
            "--server.runOnSave=true",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
            "--browser.gatherUsageStats=false",
            "--logger.level=error",
            "--server.maxUploadSize=200"
        ]
        
        logger.info(f"Starting Streamlit: {' '.join(cmd)}")
        
        # Set environment variables
        env = os.environ.copy()
        env.update({
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
            "STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION": "false"
        })
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env=env
        )
        
        return self.process
    
    def monitor_process(self):
        """Monitor Streamlit process and handle errors"""
        if not self.process:
            return False
            
        # Check if process is still running
        if self.process.poll() is not None:
            logger.warning("Streamlit process has terminated")
            return False
            
        return True
    
    def restart_streamlit(self):
        """Restart Streamlit process"""
        if self.restart_count >= self.max_restarts:
            logger.error(f"Maximum restart attempts ({self.max_restarts}) reached")
            return False
            
        logger.info(f"Restarting Streamlit (attempt {self.restart_count + 1}/{self.max_restarts})")
        
        # Kill existing process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
        
        # Wait a bit before restart
        time.sleep(2)
        
        # Start new process
        self.start_streamlit()
        self.restart_count += 1
        
        return True
    
    def run(self):
        """Main run loop with error recovery"""
        logger.info("🚀 Starting Streamlit with error recovery...")
        
        # Handle graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            self.running = False
            if self.process:
                self.process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start initial process
        self.start_streamlit()
        
        logger.info(f"🌐 Server available at:")
        logger.info(f"  Local:   http://localhost:{self.port}")
        logger.info(f"  Network: http://0.0.0.0:{self.port}")
        logger.info("Press Ctrl+C to stop")
        
        # Monitor loop
        while self.running:
            try:
                if not self.monitor_process():
                    if self.running and not self.restart_streamlit():
                        break
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitor loop: {e}")
                if self.running:
                    time.sleep(5)  # Wait before retry
        
        # Cleanup
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        
        logger.info("Streamlit runner stopped")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python streamlit_runner.py <app_path> [port]")
        sys.exit(1)
    
    app_path = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8501
    
    if not Path(app_path).exists():
        print(f"Error: App file not found: {app_path}")
        sys.exit(1)
    
    runner = StreamlitRunner(app_path, port)
    runner.run()

if __name__ == "__main__":
    main()
