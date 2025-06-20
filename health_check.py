import os
import sys
import importlib

errors = []

# Check Python version
if sys.version_info < (3, 7):
    errors.append("Python 3.7+ is required")

# Check required module
try:
    importlib.import_module('streamlit')
except ImportError:
    errors.append("Missing required package: streamlit")

# Check essential directories
for d in ["attachments", "csv", "log", "static"]:
    if not os.path.isdir(d):
        errors.append(f"Missing directory: {d}")

# Check for environment file
if not os.path.isfile('.env'):
    errors.append(".env file not found")

if errors:
    print("Health check failed:")
    for e in errors:
        print(f" - {e}")
    sys.exit(1)

print("All checks passed")
