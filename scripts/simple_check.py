#!/usr/bin/env python3

import sys
import os
from pathlib import Path

print("🏥 HoanCau AI Health Check")
print("=" * 30)

# Check Python
version = sys.version_info
if version.major == 3 and version.minor >= 8:
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
else:
    print(f"❌ Python {version.major}.{version.minor}.{version.micro}")

# Check files
if Path("src/main_engine/app.py").exists():
    print("✅ App file found")
else:
    print("❌ App file missing")

if Path("requirements.txt").exists():
    print("✅ Requirements file found")
else:
    print("❌ Requirements file missing")

print("\n🎉 Basic checks completed!")
