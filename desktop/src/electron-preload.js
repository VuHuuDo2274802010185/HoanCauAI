// electron-preload.js - Preload script for Electron

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // File operations
    selectFile: () => ipcRenderer.invoke('select-file'),
    
    // API operations  
    apiRequest: (endpoint, options) => ipcRenderer.invoke('api-request', endpoint, options),
    
    // Backend status
    checkBackend: () => ipcRenderer.invoke('check-backend'),
    
    // Event listeners
    onFileSelected: (callback) => ipcRenderer.on('file-selected', callback),
    removeFileSelectedListener: (callback) => ipcRenderer.removeListener('file-selected', callback),
    
    // App info
    getAppVersion: () => process.env.npm_package_version || '1.0.0',
    getPlatform: () => process.platform,
    
    // Utilities
    openExternal: (url) => ipcRenderer.invoke('open-external', url)
});

// DOM content loaded handler
window.addEventListener('DOMContentLoaded', () => {
    console.log('HoanCau AI Desktop App - Preload script loaded');
    
    // Add desktop-specific styles
    const style = document.createElement('style');
    style.textContent = `
        body {
            overflow-x: hidden;
        }
        
        .desktop-app {
            margin: 0;
            padding: 0;
        }
        
        .desktop-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            -webkit-app-region: drag;
        }
        
        .desktop-header h1 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
        }
        
        .desktop-header .version {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .desktop-content {
            height: calc(100vh - 60px);
            overflow-y: auto;
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-indicator.online {
            background: #4CAF50;
        }
        
        .status-indicator.offline {
            background: #f44336;
        }
        
        .desktop-controls {
            -webkit-app-region: no-drag;
        }
    `;
    document.head.appendChild(style);
});
