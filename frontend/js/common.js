/**
 * 公共工具类和配置
 */

// API基础配置
const API_BASE_URL = '/api';

// 应用状态基类
class BaseAppState {
    constructor() {
        this.isConnected = false;
        this.presets = [];
    }
}

// API客户端
class APIClient {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (config.body && typeof config.body !== 'string') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API请求失败 [${endpoint}]:`, error);
            throw error;
        }
    }

    static async healthCheck() {
        return this.request('/health');
    }

    static async getPresets() {
        return this.request('/sp/presets');
    }
}

// 通知系统
class NotificationManager {
    static show(message, type = 'info', title = null, duration = 5000) {
        let container = document.getElementById('notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications';
            container.className = 'notifications';
            document.body.appendChild(container);
        }

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${iconMap[type]} notification-icon"></i>
                <div class="notification-text">
                    ${title ? `<div class="notification-title">${title}</div>` : ''}
                    <div class="notification-message">${message}</div>
                </div>
            </div>
        `;

        container.appendChild(notification);

        // 自动移除
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }

        // 点击移除
        notification.addEventListener('click', () => {
            notification.remove();
        });
    }
}

// 加载管理器
class LoadingManager {
    static show() {
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'loading-overlay';
            overlay.style.display = 'none';
            overlay.innerHTML = `
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>处理中...</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    }

    static hide() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
}

// 连接状态管理
class ConnectionManager {
    static async checkConnection() {
        try {
            const result = await APIClient.healthCheck();
            this.updateConnectionStatus(result.success);
            return result.success;
        } catch (error) {
            this.updateConnectionStatus(false);
            return false;
        }
    }

    static updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connectionStatus');
        if (!statusEl) return;

        const dot = statusEl.querySelector('.status-dot');
        const text = statusEl.querySelector('.status-text');

        if (connected) {
            if (dot) dot.className = 'status-dot connected';
            if (text) text.textContent = '服务正常';
        } else {
            if (dot) dot.className = 'status-dot error';
            if (text) text.textContent = '连接失败';
        }
    }
}

// 工具函数
class Utils {
    static formatTime(date) {
        return new Date(date).toLocaleTimeString();
    }

    static formatDate(date) {
        return new Date(date).toLocaleDateString();
    }

    static scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}
