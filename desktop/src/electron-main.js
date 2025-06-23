// electron-main.js - Main Electron process

const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

class HoanCauElectronApp {
    constructor() {
        this.mainWindow = null;
        this.pythonProcess = null;
        this.apiPort = 8000;
        this.isDev = process.argv.includes('--dev');
        
        this.setupApp();
    }

    setupApp() {
        // Handle app ready
        app.whenReady().then(() => {
            this.createMainWindow();
            this.setupMenu();
            this.startPythonBackend();
            
            app.on('activate', () => {
                if (BrowserWindow.getAllWindows().length === 0) {
                    this.createMainWindow();
                }
            });
        });

        // Handle app window closed
        app.on('window-all-closed', () => {
            if (process.platform !== 'darwin') {
                this.cleanup();
                app.quit();
            }
        });

        // Handle app before quit
        app.on('before-quit', () => {
            this.cleanup();
        });

        // Setup IPC handlers
        this.setupIPC();
    }

    createMainWindow() {
        // Create the browser window
        this.mainWindow = new BrowserWindow({
            width: 1200,
            height: 800,
            minWidth: 800,
            minHeight: 600,
            icon: path.join(__dirname, '../assets/logo.png'),
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'electron-preload.js'),
                webSecurity: !this.isDev
            },
            titleBarStyle: 'default',
            show: false // Don't show until ready
        });

        // Load the app
        if (this.isDev) {
            // Development mode - load from localhost
            this.mainWindow.loadURL('http://localhost:8501'); // Streamlit default port
            this.mainWindow.webContents.openDevTools();
        } else {
            // Production mode - load local file
            this.mainWindow.loadFile('desktop.html');
        }

        // Show window when ready
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
            
            // Focus window
            if (this.isDev) {
                this.mainWindow.focus();
            }
        });

        // Handle window closed
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });

        // Handle external links
        this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
            shell.openExternal(url);
            return { action: 'deny' };
        });
    }

    setupMenu() {
        const template = [
            {
                label: 'File',
                submenu: [
                    {
                        label: 'Mở CV...',
                        accelerator: 'CmdOrCtrl+O',
                        click: () => this.openFileDialog()
                    },
                    { type: 'separator' },
                    {
                        label: 'Thoát',
                        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                        click: () => {
                            this.cleanup();
                            app.quit();
                        }
                    }
                ]
            },
            {
                label: 'View',
                submenu: [
                    { role: 'reload' },
                    { role: 'forceReload' },
                    { role: 'toggleDevTools' },
                    { type: 'separator' },
                    { role: 'resetZoom' },
                    { role: 'zoomIn' },
                    { role: 'zoomOut' },
                    { type: 'separator' },
                    { role: 'togglefullscreen' }
                ]
            },
            {
                label: 'Tools',
                submenu: [
                    {
                        label: 'Mở Streamlit App',
                        click: () => shell.openExternal('http://localhost:8501')
                    },
                    {
                        label: 'Mở API Docs',
                        click: () => shell.openExternal('http://localhost:8000/docs')
                    },
                    { type: 'separator' },
                    {
                        label: 'Restart Backend',
                        click: () => this.restartPythonBackend()
                    }
                ]
            },
            {
                label: 'Help',
                submenu: [
                    {
                        label: 'Về HoanCau AI',
                        click: () => this.showAbout()
                    },
                    {
                        label: 'Hướng dẫn sử dụng',
                        click: () => shell.openExternal('https://github.com/your-repo/wiki')
                    }
                ]
            }
        ];

        // macOS specific menu adjustments
        if (process.platform === 'darwin') {
            template.unshift({
                label: app.getName(),
                submenu: [
                    { role: 'about' },
                    { type: 'separator' },
                    { role: 'services' },
                    { type: 'separator' },
                    { role: 'hide' },
                    { role: 'hideothers' },
                    { role: 'unhide' },
                    { type: 'separator' },
                    { role: 'quit' }
                ]
            });
        }

        const menu = Menu.buildFromTemplate(template);
        Menu.setApplicationMenu(menu);
    }

    setupIPC() {
        // Handle file selection
        ipcMain.handle('select-file', async () => {
            const result = await dialog.showOpenDialog(this.mainWindow, {
                properties: ['openFile'],
                filters: [
                    { name: 'CV Files', extensions: ['pdf', 'docx'] },
                    { name: 'PDF Files', extensions: ['pdf'] },
                    { name: 'Word Documents', extensions: ['docx'] },
                    { name: 'All Files', extensions: ['*'] }
                ]
            });
            
            return result;
        });

        // Handle API requests
        ipcMain.handle('api-request', async (event, endpoint, options = {}) => {
            try {
                const url = `http://localhost:${this.apiPort}${endpoint}`;
                const response = await axios({
                    url,
                    method: options.method || 'GET',
                    data: options.data,
                    headers: options.headers,
                    timeout: 30000
                });
                
                return {
                    success: true,
                    data: response.data
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        });

        // Handle backend status check  
        ipcMain.handle('check-backend', async () => {
            try {
                const response = await axios.get(`http://localhost:${this.apiPort}/health`, {
                    timeout: 5000
                });
                return { status: 'online', data: response.data };
            } catch (error) {
                return { status: 'offline', error: error.message };
            }
        });
    }

    async startPythonBackend() {
        if (this.isDev) {
            console.log('Development mode - assuming Python backend is running separately');
            return;
        }

        try {
            console.log('Starting Python backend...');
            
            // Determine Python executable
            const pythonExe = process.platform === 'win32' ? 'python.exe' : 'python3';
            const pythonPath = this.isDev ? pythonExe : path.join(process.resourcesPath, 'python', pythonExe);
            
            // Start API server
            this.pythonProcess = spawn(pythonPath, ['api_server.py'], {
                cwd: __dirname,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            this.pythonProcess.stdout.on('data', (data) => {
                console.log(`Python stdout: ${data}`);
            });

            this.pythonProcess.stderr.on('data', (data) => {
                console.error(`Python stderr: ${data}`);
            });

            this.pythonProcess.on('close', (code) => {
                console.log(`Python process exited with code ${code}`);
                this.pythonProcess = null;
            });

            // Wait for backend to be ready
            await this.waitForBackend();
            
        } catch (error) {
            console.error('Failed to start Python backend:', error);
            this.showErrorDialog('Không thể khởi động backend Python', error.message);
        }
    }

    async waitForBackend(maxAttempts = 30) {
        for (let i = 0; i < maxAttempts; i++) {
            try {
                await axios.get(`http://localhost:${this.apiPort}/health`, { timeout: 2000 });
                console.log('Backend is ready!');
                return true;
            } catch (error) {
                console.log(`Waiting for backend... (${i + 1}/${maxAttempts})`);
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        throw new Error('Backend failed to start within timeout');
    }

    restartPythonBackend() {
        if (this.pythonProcess) {
            this.pythonProcess.kill();
            this.pythonProcess = null;
        }
        setTimeout(() => {
            this.startPythonBackend();
        }, 2000);
    }

    cleanup() {
        if (this.pythonProcess) {
            console.log('Terminating Python backend...');
            this.pythonProcess.kill();
            this.pythonProcess = null;
        }
    }

    async openFileDialog() {
        const result = await dialog.showOpenDialog(this.mainWindow, {
            properties: ['openFile'],
            filters: [
                { name: 'CV Files', extensions: ['pdf', 'docx'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });

        if (!result.canceled && result.filePaths.length > 0) {
            // Send file path to renderer
            this.mainWindow.webContents.send('file-selected', result.filePaths[0]);
        }
    }

    showAbout() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'Về HoanCau AI Resume Processor',
            message: 'HoanCau AI Resume Processor',
            detail: `Phiên bản: 1.0.0
Hệ thống AI xử lý và phân tích CV/Resume thông minh.

© 2024 HoanCau AI Team`
        });
    }

    showErrorDialog(title, message) {
        dialog.showErrorBox(title, message);
    }
}

// Initialize the app
new HoanCauElectronApp();
