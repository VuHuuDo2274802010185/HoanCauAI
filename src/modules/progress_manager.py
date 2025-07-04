"""
Enhanced Progress Manager for HoanCau AI
Provides better progress tracking and status display
"""

import time
import logging
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
import streamlit as st
from tqdm import tqdm
import threading

logger = logging.getLogger(__name__)

class ProgressManager:
    """Enhanced progress manager with Streamlit integration"""
    
    def __init__(self):
        self.current_progress = 0
        self.total_steps = 100
        self.status_message = "Initializing..."
        self.start_time = None
        self.is_active = False
        self._lock = threading.Lock()
        
    def start(self, total_steps: int = 100, message: str = "Starting..."):
        """Start progress tracking"""
        with self._lock:
            self.total_steps = total_steps
            self.current_progress = 0
            self.status_message = message
            self.start_time = time.time()
            self.is_active = True
            logger.info(f"Progress started: {message}")
    
    def update(self, step: int, message: str = None):
        """Update progress"""
        with self._lock:
            if not self.is_active:
                return
                
            self.current_progress = min(step, self.total_steps)
            if message:
                self.status_message = message
                
            # Calculate percentage and elapsed time
            percentage = (self.current_progress / self.total_steps) * 100
            elapsed = time.time() - self.start_time if self.start_time else 0
            
            logger.info(f"Progress: {percentage:.1f}% - {self.status_message}")
    
    def increment(self, message: str = None):
        """Increment progress by 1"""
        self.update(self.current_progress + 1, message)
    
    def finish(self, message: str = "Completed"):
        """Finish progress tracking"""
        with self._lock:
            if not self.is_active:
                return
                
            self.current_progress = self.total_steps
            self.status_message = message
            self.is_active = False
            
            elapsed = time.time() - self.start_time if self.start_time else 0
            logger.info(f"Progress completed in {elapsed:.2f}s: {message}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        with self._lock:
            percentage = (self.current_progress / self.total_steps) * 100 if self.total_steps > 0 else 0
            elapsed = time.time() - self.start_time if self.start_time else 0
            
            return {
                'progress': self.current_progress,
                'total': self.total_steps,
                'percentage': percentage,
                'message': self.status_message,
                'elapsed': elapsed,
                'is_active': self.is_active
            }

class StreamlitProgressBar:
    """Streamlit-specific progress bar with enhanced features"""
    
    def __init__(self, container=None):
        self.container = container or st
        self.progress_bar = None
        self.status_text = None
        self.info_text = None
        self.manager = ProgressManager()
        
    def initialize(self, total_steps: int = 100, title: str = "Processing..."):
        """Initialize the progress bar display"""
        # Check if container is a streamlit container (has __enter__ and __exit__ methods)
        # If it's the st module itself, it doesn't support context manager
        if (self.container and 
            hasattr(self.container, '__enter__') and 
            hasattr(self.container, '__exit__')):
            with self.container:
                st.markdown(f"### {title}")
                self.progress_bar = st.progress(0)
                self.status_text = st.empty()
                self.info_text = st.empty()
        else:
            # Use st directly when container is None or st module
            st.markdown(f"### {title}")
            self.progress_bar = st.progress(0)
            self.status_text = st.empty()
            self.info_text = st.empty()
                
        self.manager.start(total_steps, title)
        self.update_display()
    
    def update(self, step: int, message: str = None):
        """Update progress and display"""
        self.manager.update(step, message)
        self.update_display()
    
    def increment(self, message: str = None):
        """Increment progress and update display"""
        self.manager.increment(message)
        self.update_display()
    
    def update_display(self):
        """Update the Streamlit display"""
        if not (self.progress_bar and self.status_text):
            return
            
        status = self.manager.get_status()
        
        # Update progress bar
        progress_value = status['percentage'] / 100
        self.progress_bar.progress(progress_value)
        
        # Update status text
        self.status_text.text(f"📊 {status['message']} ({status['percentage']:.1f}%)")
        
        # Update info text with timing
        if status['elapsed'] > 0:
            elapsed_str = f"{status['elapsed']:.1f}s"
            if status['is_active'] and status['percentage'] > 0:
                # Estimate remaining time
                remaining = (status['elapsed'] / status['percentage']) * (100 - status['percentage'])
                remaining_str = f"{remaining:.1f}s"
                self.info_text.text(f"⏱️ Elapsed: {elapsed_str} | Estimated remaining: {remaining_str}")
            else:
                self.info_text.text(f"⏱️ Completed in {elapsed_str}")
    
    def finish(self, message: str = "✅ Completed successfully!"):
        """Complete the progress bar"""
        self.manager.finish(message)
        self.update_display()
        
        # Show completion message
        if (self.container and 
            hasattr(self.container, '__enter__') and 
            hasattr(self.container, '__exit__')):
            time.sleep(0.5)  # Brief pause to show completion
            with self.container:
                st.success(message)
        elif self.container:
            time.sleep(0.5)  # Brief pause to show completion
            st.success(message)

@contextmanager
def progress_context(total_steps: int = 100, title: str = "Processing...", container=None):
    """Context manager for easy progress tracking"""
    progress_bar = StreamlitProgressBar(container)
    progress_bar.initialize(total_steps, title)
    
    try:
        yield progress_bar
    except Exception as e:
        if progress_bar.status_text:
            progress_bar.status_text.error(f"❌ Error: {str(e)}")
        raise
    finally:
        if progress_bar.manager.is_active:
            progress_bar.finish()

def with_progress(total_steps: int = 100, title: str = "Processing..."):
    """Decorator for functions that need progress tracking"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            with progress_context(total_steps, title) as progress:
                # Inject progress bar into function if it accepts it
                import inspect
                sig = inspect.signature(func)
                if 'progress' in sig.parameters:
                    kwargs['progress'] = progress
                return func(*args, **kwargs)
        return wrapper
    return decorator

class TerminalProgressBar:
    """Terminal-based progress bar using tqdm"""
    
    def __init__(self, total_steps: int = 100, description: str = "Processing"):
        self.pbar = tqdm(
            total=total_steps,
            desc=description,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
            ncols=80
        )
    
    def update(self, step: int = 1, message: str = None):
        """Update progress"""
        self.pbar.update(step)
        if message:
            self.pbar.set_description(message)
    
    def set_description(self, desc: str):
        """Set progress description"""
        self.pbar.set_description(desc)
    
    def close(self):
        """Close progress bar"""
        self.pbar.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Global progress manager instance
global_progress = ProgressManager()

def create_progress_bar(use_streamlit: bool = True, **kwargs) -> StreamlitProgressBar:
    """Factory function to create appropriate progress bar"""
    if use_streamlit:
        try:
            # Check if we're in a Streamlit context
            st.empty()
            return StreamlitProgressBar(**kwargs)
        except:
            # Fall back to terminal progress bar
            return TerminalProgressBar(**kwargs)
    else:
        return TerminalProgressBar(**kwargs)
