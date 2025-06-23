# Desktop Module

Thư mục này chứa ứng dụng desktop được xây dựng bằng Electron.

## Cấu trúc thư mục

```
desktop/
├── package.json          # Node.js dependencies & build configuration
├── src/
│   ├── electron-main.js   # Main Electron process
│   ├── electron-preload.js # Preload script (security bridge)
│   └── desktop.html       # Desktop UI
├── assets/
│   └── logo.png          # App icon
└── README.md
```

## Files chính

### `package.json`
- **Mục đích**: Cấu hình Node.js project và Electron build
- **Dependencies**: 
  - `electron` - Framework desktop app
  - `electron-builder` - Build tool cho multi-platform
  - `axios` - HTTP client
- **Scripts**:
  - `electron` - Chạy production mode
  - `electron-dev` - Chạy development mode
  - `build-*` - Build cho từng platform
  - `dist` - Build cho platform hiện tại

### `src/electron-main.js`
- **Mục đích**: Main process của Electron
- **Chức năng**:
  - Tạo và quản lý browser windows
  - Khởi động Python backend
  - Setup menu và IPC handlers
  - Quản lý lifecycle của app
- **Features**:
  - Auto-start Python API server
  - File dialog integration
  - System tray support
  - Cross-platform compatibility

### `src/electron-preload.js`
- **Mục đích**: Bridge giữa main và renderer process
- **Bảo mật**: Context isolation enabled
- **API exposed**:
  - `electronAPI.selectFile()` - File picker
  - `electronAPI.apiRequest()` - API calls
  - `electronAPI.checkBackend()` - Health check
- **Styling**: Thêm desktop-specific CSS

### `src/desktop.html`
- **Mục đích**: Giao diện chính của desktop app
- **Features**:
  - Welcome screen với quick actions
  - Feature cards giới thiệu tính năng
  - Statistics dashboard
  - Embedded widget iframe
  - Status bar với backend connection
- **Responsive**: Tối ưu cho desktop experience

## Cách sử dụng

### Development
```bash
cd desktop/
npm install
npm run electron-dev
```

### Production Build
```bash
cd desktop/
npm run build-win    # Windows
npm run build-mac    # macOS
npm run build-linux  # Linux
npm run build-all    # All platforms
```

### Chạy từ root directory
```bash
# Từ root project
npm run electron     # Chạy desktop app
```

## Platform Support

- ✅ **Windows**: NSIS installer (.exe)
- ✅ **macOS**: DMG package (.dmg)
- ✅ **Linux**: AppImage (.AppImage)

## Cập nhật sau này

### Tính năng mới
- Auto-updater cho production
- System tray với quick actions
- Drag & drop files từ desktop
- Offline mode với local AI
- Multi-window support
- Keyboard shortcuts
- Print support cho reports

### Tối ưu hóa
- Bundle size optimization
- Startup performance
- Memory usage optimization
- Native modules integration
- Code signing cho production
- Crash reporting

### Tích hợp
- Native notifications
- System file associations (.pdf, .docx)
- Context menu integration
- Dock/taskbar progress
- Native file picker
- OS-specific features (Windows JumpList, macOS TouchBar)

## Build Configuration

### Electron Builder Options
- **AppId**: com.hoancau.ai.resume.processor
- **Output**: dist/ directory
- **Icons**: assets/logo.png
- **Auto-updater**: Có thể thêm sau
- **Code signing**: Cần thiết cho production

### Security
- Context isolation enabled
- Node integration disabled
- Secure preload script
- CSP headers cho production
