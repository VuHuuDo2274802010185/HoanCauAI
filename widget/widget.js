// widget.js - JavaScript for HoanCau AI Resume Analyzer Widget

class HoanCauWidget {
    constructor(apiBaseUrl = 'http://localhost:8000') {
        this.apiBaseUrl = apiBaseUrl;
        this.selectedFile = null;
        this.availableModels = {};
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadAvailableModels();
    }

    initializeElements() {
        // Get DOM elements
        this.elements = {
            fileInput: document.getElementById('cvFile'),
            fileInfo: document.getElementById('fileInfo'),
            provider: document.getElementById('provider'),
            model: document.getElementById('model'),
            temperature: document.getElementById('temperature'),
            analyzeButton: document.getElementById('analyzeButton'),
            loading: document.getElementById('loading'),
            error: document.getElementById('error'),
            results: document.getElementById('results'),
            resultsContent: document.getElementById('resultsContent'),
            chatInput: document.getElementById('chatInput'),
            chatSendButton: document.getElementById('chatSendButton'),
            chatMessages: document.getElementById('chatMessages')
        };
    }

    attachEventListeners() {
        // File input change
        this.elements.fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // Provider change
        this.elements.provider.addEventListener('change', () => {
            this.updateModelOptions();
        });

        // Analyze button click
        this.elements.analyzeButton.addEventListener('click', () => {
            this.analyzeCV();
        });

        // Chat functionality
        this.elements.chatSendButton.addEventListener('click', () => {
            this.sendChatMessage();
        });

        this.elements.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });
    }

    async loadAvailableModels() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/models`);
            const data = await response.json();
            
            if (data.success) {
                this.availableModels = data.models;
                this.updateModelOptions();
            }
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }

    updateModelOptions() {
        const provider = this.elements.provider.value;
        const modelSelect = this.elements.model;
        
        // Clear existing options
        modelSelect.innerHTML = '';
        
        // Add new options
        if (this.availableModels[provider]) {
            this.availableModels[provider].forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        }
    }

    handleFileSelect(file) {
        if (!file) {
            this.selectedFile = null;
            this.elements.fileInfo.style.display = 'none';
            this.elements.analyzeButton.disabled = true;
            return;
        }

        // Validate file type
        const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Chỉ hỗ trợ file PDF và DOCX');
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('File không được vượt quá 10MB');
            return;
        }

        this.selectedFile = file;
        
        // Show file info
        this.elements.fileInfo.innerHTML = `
            ✅ <strong>${file.name}</strong><br>
            📏 Kích thước: ${this.formatFileSize(file.size)}<br>
            📅 Ngày sửa đổi: ${new Date(file.lastModified).toLocaleDateString('vi-VN')}
        `;
        this.elements.fileInfo.style.display = 'block';
        
        // Enable analyze button
        this.elements.analyzeButton.disabled = false;
        
        // Hide previous results
        this.hideError();
        this.hideResults();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async analyzeCV() {
        if (!this.selectedFile) {
            this.showError('Vui lòng chọn file CV trước');
            return;
        }

        try {
            // Show loading
            this.showLoading();
            this.hideError();
            this.hideResults();
            
            // Prepare form data
            const formData = new FormData();
            formData.append('file', this.selectedFile);
            formData.append('provider', this.elements.provider.value);
            formData.append('model_name', this.elements.model.value);
            formData.append('temperature', this.elements.temperature.value);

            // Make API request
            const response = await fetch(`${this.apiBaseUrl}/api/analyze-cv`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showResults(data.analysis, data.processing_time);
            } else {
                this.showError(data.error || 'Có lỗi xảy ra khi phân tích CV');
            }

        } catch (error) {
            console.error('Analysis error:', error);
            this.showError('Không thể kết nối đến server. Vui lòng thử lại sau.');
        } finally {
            this.hideLoading();
        }
    }

    async sendChatMessage() {
        const message = this.elements.chatInput.value.trim();
        if (!message) return;

        try {
            // Add user message to chat
            this.addChatMessage(message, 'user');
            this.elements.chatInput.value = '';

            // Show chat messages container
            this.elements.chatMessages.style.display = 'block';

            // Send to API
            const response = await fetch(`${this.apiBaseUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    provider: this.elements.provider.value,
                    model_name: this.elements.model.value,
                    temperature: parseFloat(this.elements.temperature.value)
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addChatMessage(data.message, 'ai');
            } else {
                this.addChatMessage('Xin lỗi, tôi không thể trả lời câu hỏi này lúc này.', 'ai');
            }

        } catch (error) {
            console.error('Chat error:', error);
            this.addChatMessage('Có lỗi xảy ra khi gửi tin nhắn.', 'ai');
        }
    }

    addChatMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'chat-message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.elements.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    showResults(analysis, processingTime) {
        if (!analysis) {
            this.showError('Không có dữ liệu phân tích');
            return;
        }

        let html = '';
        
        // Processing time
        if (processingTime) {
            html += `
                <div class="result-item">
                    <div class="result-label">⏱️ Thời gian xử lý:</div>
                    <div class="result-value">${processingTime.toFixed(2)} giây</div>
                </div>
            `;
        }

        // Display analysis results
        for (const [key, value] of Object.entries(analysis)) {
            if (value && value !== 'N/A') {
                const displayKey = this.getDisplayName(key);
                html += `
                    <div class="result-item">
                        <div class="result-label">${displayKey}:</div>
                        <div class="result-value">${this.formatValue(value)}</div>
                    </div>
                `;
            }
        }

        this.elements.resultsContent.innerHTML = html;
        this.elements.results.classList.add('show');
    }

    getDisplayName(key) {
        const displayNames = {
            'name': '👤 Họ và tên',
            'email': '📧 Email',
            'phone': '📞 Số điện thoại',
            'address': '🏠 Địa chỉ',
            'education': '🎓 Học vấn',
            'experience': '💼 Kinh nghiệm',
            'skills': '⚡ Kỹ năng',
            'summary': '📋 Tóm tắt',
            'languages': '🌐 Ngôn ngữ',
            'certifications': '🏆 Chứng chỉ',
            'projects': '🚀 Dự án',
            'score': '⭐ Điểm đánh giá',
            'recommendations': '💡 Đề xuất cải thiện'
        };
        return displayNames[key] || key;
    }

    formatValue(value) {
        if (Array.isArray(value)) {
            return value.join(', ');
        }
        if (typeof value === 'object') {
            return JSON.stringify(value, null, 2);
        }
        return String(value);
    }

    showLoading() {
        this.elements.loading.classList.add('show');
        this.elements.analyzeButton.disabled = true;
    }

    hideLoading() {
        this.elements.loading.classList.remove('show');
        this.elements.analyzeButton.disabled = false;
    }

    showError(message) {
        this.elements.error.textContent = message;
        this.elements.error.classList.add('show');
    }

    hideError() {
        this.elements.error.classList.remove('show');
    }

    hideResults() {
        this.elements.results.classList.remove('show');
    }
}

// Initialize widget when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get API base URL from data attribute or use default
    const widget = document.getElementById('hoancauWidget');
    const apiBaseUrl = widget.dataset.apiUrl || 'http://localhost:8000';
    
    // Initialize the widget
    window.hoancauWidget = new HoanCauWidget(apiBaseUrl);
});

// Export for use in other contexts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HoanCauWidget;
}
