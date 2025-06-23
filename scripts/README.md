# Scripts Module

Thư mục này chứa các script tự động hóa cho việc build, deploy và chạy ứng dụng.

## Files

### Start/Stop Scripts

#### `start-api.sh` / `start-api.bat`
- **Mục đích**: Khởi động API server
- **Chức năng**:
  - Kiểm tra Python version (≥3.10)
  - Tạo và kích hoạt virtual environment
  - Cài đặt dependencies từ requirements.txt
  - Tạo .env template nếu chưa có
  - Khởi động API server trên port 8000
- **Usage**: 
  ```bash
  # Linux/macOS
  ./scripts/start-api.sh
  
  # Windows
  scripts\start-api.bat
  ```

#### `run-all.sh`
- **Mục đích**: Khởi động tất cả services (API + Streamlit + Electron)
- **Chức năng**:
  - Setup Python và Node.js environments
  - Khởi động API server (port 8000)
  - Khởi động Streamlit app (port 8501)
  - Tùy chọn khởi động Electron desktop app
  - Wait for services ready
  - Monitor và cleanup khi Ctrl+C
- **Features**:
  - Port conflict detection và resolution
  - Health check cho services
  - PID tracking cho cleanup
  - Interactive prompts
- **Usage**: `./scripts/run-all.sh`

#### `stop-all.sh`
- **Mục đích**: Dừng tất cả services
- **Chức năng**:
  - Đọc PIDs từ .pids file
  - Kill processes by PID
  - Kill processes by port (8000, 8501)
  - Cleanup temp files
- **Usage**: `./scripts/stop-all.sh`

### Build Scripts

#### `build-electron.sh` / `build-electron.bat`
- **Mục đích**: Build desktop app cho production
- **Chức năng**:
  - Kiểm tra Node.js và npm
  - Install Electron và electron-builder
  - Tạo Python distribution directory
  - Interactive platform selection
  - Build app cho target platforms
- **Platforms**:
  1. Windows (.exe với NSIS installer)
  2. macOS (.dmg)
  3. Linux (.AppImage)
  4. All platforms
  5. Current platform only
- **Output**: `desktop/dist/` directory
- **Usage**: 
  ```bash
  # Linux/macOS
  ./scripts/build-electron.sh
  
  # Windows
  scripts\build-electron.bat
  ```

## Cách sử dụng từ root directory

### Quick Start (tất cả services)
```bash
chmod +x scripts/*.sh
./scripts/run-all.sh
```

### Chỉ API server
```bash
./scripts/start-api.sh
```

### Build desktop app
```bash
./scripts/build-electron.sh
```

### Stop tất cả
```bash
./scripts/stop-all.sh
```

## Environment Setup

### Python Requirements
- Python 3.10+
- Virtual environment support
- Pip package manager

### Node.js Requirements
- Node.js 16+
- npm package manager
- Cross-platform build tools

## Troubleshooting

### Common Issues

1. **Port conflicts**
   - Scripts tự động detect và kill conflicting processes
   - Ports used: 8000 (API), 8501 (Streamlit)

2. **Permission errors**
   ```bash
   chmod +x scripts/*.sh
   ```

3. **Python version issues**
   - Scripts check for Python 3.10+
   - Use pyenv or conda for version management

4. **Node.js issues**
   - Use nvm for Node.js version management
   - Clear npm cache: `npm cache clean --force`

## Cập nhật sau này

### Script Enhancements
- Windows PowerShell versions
- Docker deployment scripts
- CI/CD pipeline scripts
- Database setup scripts
- SSL/TLS setup scripts
- Backup/restore scripts

### Monitoring & Logging
- Log rotation scripts
- Health monitoring scripts
- Performance monitoring
- Error reporting scripts
- Metrics collection

### Development Tools
- Test runner scripts
- Code quality scripts (linting, formatting)
- Documentation generation scripts
- Translation management scripts
- Asset optimization scripts

### Deployment Scripts
- Production deployment scripts
- Blue-green deployment
- Load balancer configuration
- Reverse proxy setup
- Environment migration scripts
- Database migration scripts
