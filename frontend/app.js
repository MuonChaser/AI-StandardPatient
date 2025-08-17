// API基础配置
const API_BASE_URL = 'http://api.bwzhang.cn/api';

// 应用状态
const AppState = {
    currentSession: null,
    sessions: [],
    presets: [],
    isConnected: false
};

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

    static async createSession(sessionData) {
        return this.request('/sp/session/create', {
            method: 'POST',
            body: JSON.stringify(sessionData)
        });
    }

    static async sendMessage(sessionId, message) {
        return this.request(`/sp/session/${sessionId}/chat`, {
            method: 'POST',
            body: JSON.stringify({ message })
        });
    }

    static async getSessionInfo(sessionId) {
        return this.request(`/sp/session/${sessionId}/info`);
    }

    static async getHistory(sessionId) {
        return this.request(`/sp/session/${sessionId}/history`);
    }

    static async getSessions() {
        return this.request('/sp/sessions');
    }

    static async deleteSession(sessionId) {
        return this.request(`/sp/session/${sessionId}`, {
            method: 'DELETE'
        });
    }

    static async validateData(data) {
        return this.request('/sp/data/validate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// 通知系统
class NotificationManager {
    static show(message, type = 'info', title = null, duration = 5000) {
        const container = document.getElementById('notifications');
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
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    static hide() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
}

// 应用主类
class SPApp {
    constructor() {
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.checkConnection();
        await this.loadPresets();
        await this.loadSessions();
        this.updateUI();
    }

    bindEvents() {
        // 数据源切换
        document.querySelectorAll('input[name="dataSource"]').forEach(radio => {
            radio.addEventListener('change', this.handleDataSourceChange.bind(this));
        });

        // 创建会话
        document.getElementById('createSessionBtn').addEventListener('click', this.createSession.bind(this));

        // 发送消息
        document.getElementById('sendBtn').addEventListener('click', this.sendMessage.bind(this));
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // 快速问题
        document.querySelectorAll('.quick-question').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.dataset.question;
                document.getElementById('messageInput').value = question;
                this.sendMessage();
            });
        });

        // 模态框控制
        document.getElementById('sessionInfoBtn').addEventListener('click', this.showSessionInfo.bind(this));
        document.getElementById('historyBtn').addEventListener('click', this.showHistory.bind(this));
        document.getElementById('deleteSessionBtn').addEventListener('click', this.deleteCurrentSession.bind(this));

        // 关闭模态框
        document.getElementById('closeSessionInfo').addEventListener('click', () => {
            document.getElementById('sessionInfoModal').classList.remove('show');
        });
        document.getElementById('closeHistory').addEventListener('click', () => {
            document.getElementById('historyModal').classList.remove('show');
        });

        // 点击模态框背景关闭
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                }
            });
        });
    }

    async checkConnection() {
        try {
            const result = await APIClient.healthCheck();
            AppState.isConnected = result.success;
            this.updateConnectionStatus(true, result.data);
            NotificationManager.show('服务连接成功', 'success');
        } catch (error) {
            AppState.isConnected = false;
            this.updateConnectionStatus(false);
            NotificationManager.show('无法连接到后端服务，请检查服务是否正常运行', 'error');
        }
    }

    updateConnectionStatus(connected, data = null) {
        const statusEl = document.getElementById('connectionStatus');
        const dot = statusEl.querySelector('.status-dot');
        const text = statusEl.querySelector('.status-text');

        if (connected) {
            dot.className = 'status-dot connected';
            text.textContent = '服务正常';
            if (data) {
                document.getElementById('sessionCount').innerHTML = `
                    <i class="fas fa-users"></i>
                    <span>${data.active_sessions} 个会话</span>
                `;
            }
        } else {
            dot.className = 'status-dot error';
            text.textContent = '连接失败';
        }
    }

    async loadPresets() {
        try {
            const result = await APIClient.getPresets();
            if (result.success) {
                AppState.presets = result.data;
                this.updatePresetSelect();
            }
        } catch (error) {
            NotificationManager.show('加载预设病例失败', 'error');
        }
    }

    updatePresetSelect() {
        const select = document.getElementById('presetSelect');
        select.innerHTML = '<option value="">请选择预设病例</option>';
        
        AppState.presets.forEach(preset => {
            const option = document.createElement('option');
            option.value = preset.filename;
            option.textContent = preset.description;
            select.appendChild(option);
        });
    }

    async loadSessions() {
        try {
            const result = await APIClient.getSessions();
            if (result.success) {
                AppState.sessions = result.data.sessions;
                this.updateSessionList();
                this.updateConnectionStatus(true, result.data);
            }
        } catch (error) {
            NotificationManager.show('加载会话列表失败', 'error');
        }
    }

    updateSessionList() {
        const container = document.getElementById('sessionList');
        
        if (AppState.sessions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>暂无活跃会话</p>
                </div>
            `;
            return;
        }

        container.innerHTML = AppState.sessions.map(session => `
            <div class="session-item ${session.session_id === AppState.currentSession?.session_id ? 'active' : ''}" 
                 onclick="app.selectSession('${session.session_id}')">
                <div class="session-item-header">
                    <div class="session-item-name">${session.patient_name}</div>
                    <div class="session-item-id">${session.session_id}</div>
                </div>
                <div class="session-item-disease">${session.disease}</div>
                <div class="session-item-meta">
                    <span>${session.message_count} 条消息</span>
                    <span>${new Date(session.last_activity).toLocaleTimeString()}</span>
                </div>
            </div>
        `).join('');
    }

    handleDataSourceChange(e) {
        const presetSection = document.getElementById('presetSection');
        const customSection = document.getElementById('customSection');
        
        if (e.target.value === 'preset') {
            presetSection.style.display = 'block';
            customSection.style.display = 'none';
        } else {
            presetSection.style.display = 'none';
            customSection.style.display = 'block';
        }
    }

    async createSession() {
        const sessionId = document.getElementById('sessionId').value.trim();
        const dataSource = document.querySelector('input[name="dataSource"]:checked').value;
        
        if (!sessionId) {
            NotificationManager.show('请输入会话ID', 'warning');
            return;
        }

        const sessionData = { session_id: sessionId };

        if (dataSource === 'preset') {
            const presetFile = document.getElementById('presetSelect').value;
            if (!presetFile) {
                NotificationManager.show('请选择预设病例', 'warning');
                return;
            }
            sessionData.preset_file = presetFile;
        } else {
            const customDataText = document.getElementById('customData').value.trim();
            if (!customDataText) {
                NotificationManager.show('请输入自定义数据', 'warning');
                return;
            }
            
            try {
                sessionData.custom_data = JSON.parse(customDataText);
            } catch (error) {
                NotificationManager.show('自定义数据格式错误，请检查JSON格式', 'error');
                return;
            }
        }

        LoadingManager.show();
        try {
            const result = await APIClient.createSession(sessionData);
            if (result.success) {
                NotificationManager.show(`会话 "${result.data.patient_name}" 创建成功`, 'success');
                document.getElementById('sessionId').value = '';
                document.getElementById('customData').value = '';
                await this.loadSessions();
                this.selectSession(sessionId);
            }
        } catch (error) {
            NotificationManager.show(`创建会话失败: ${error.message}`, 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    selectSession(sessionId) {
        const session = AppState.sessions.find(s => s.session_id === sessionId);
        if (!session) return;

        AppState.currentSession = session;
        this.updateSessionList();
        this.showChatInterface(session);
        this.loadChatHistory();
    }

    showChatInterface(session) {
        const welcomeMessage = document.getElementById('welcomeMessage');
        const patientInfo = document.querySelector('.patient-info');
        const chatInputContainer = document.getElementById('chatInputContainer');

        welcomeMessage.style.display = 'none';
        patientInfo.style.display = 'flex';
        chatInputContainer.style.display = 'block';

        document.getElementById('patientName').textContent = session.patient_name;
        document.getElementById('patientDisease').textContent = session.disease;
        
        // 清空聊天记录显示
        document.getElementById('chatMessages').innerHTML = '';
    }

    async loadChatHistory() {
        if (!AppState.currentSession) return;

        try {
            const result = await APIClient.getHistory(AppState.currentSession.session_id);
            if (result.success) {
                this.displayChatHistory(result.data.history);
            }
        } catch (error) {
            NotificationManager.show('加载对话历史失败', 'error');
        }
    }

    displayChatHistory(history) {
        const container = document.getElementById('chatMessages');
        container.innerHTML = '';

        history.forEach(item => {
            this.addMessage('user', item.user_message);
            this.addMessage('patient', item.sp_response);
        });

        this.scrollToBottom();
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || !AppState.currentSession) return;

        // 添加用户消息到界面
        this.addMessage('user', message);
        input.value = '';
        
        // 显示加载状态
        const loadingMessage = this.addMessage('patient', '思考中...', true);

        try {
            const result = await APIClient.sendMessage(AppState.currentSession.session_id, message);
            
            // 移除加载消息
            if (loadingMessage) {
                loadingMessage.remove();
            }
            
            if (result.success) {
                this.addMessage('patient', result.data.sp_response);
                
                // 更新会话消息计数
                const session = AppState.sessions.find(s => s.session_id === AppState.currentSession.session_id);
                if (session) {
                    session.message_count = result.data.message_count;
                    this.updateSessionList();
                }
            }
        } catch (error) {
            if (loadingMessage) {
                loadingMessage.remove();
            }
            NotificationManager.show(`发送消息失败: ${error.message}`, 'error');
        }
    }

    addMessage(type, content, isLoading = false) {
        const container = document.getElementById('chatMessages');
        const messageEl = document.createElement('div');
        messageEl.className = `message ${type}`;
        
        const avatar = type === 'user' ? 'fa-user-md' : 'fa-user';
        const time = new Date().toLocaleTimeString();
        
        messageEl.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${avatar}"></i>
            </div>
            <div class="message-content">
                ${content}
                ${!isLoading ? `<div class="message-time">${time}</div>` : ''}
            </div>
        `;

        container.appendChild(messageEl);
        this.scrollToBottom();
        
        return messageEl;
    }

    scrollToBottom() {
        const container = document.getElementById('chatMessages');
        container.scrollTop = container.scrollHeight;
    }

    async showSessionInfo() {
        if (!AppState.currentSession) return;

        LoadingManager.show();
        try {
            const result = await APIClient.getSessionInfo(AppState.currentSession.session_id);
            if (result.success) {
                this.displaySessionInfo(result.data);
                document.getElementById('sessionInfoModal').classList.add('show');
            }
        } catch (error) {
            NotificationManager.show('获取会话信息失败', 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    displaySessionInfo(info) {
        const container = document.getElementById('sessionInfoContent');
        
        const formatValue = (value) => {
            if (Array.isArray(value)) {
                return `<ul class="session-info-list">${value.map(item => `<li>${item}</li>`).join('')}</ul>`;
            } else if (typeof value === 'object' && value !== null) {
                return Object.entries(value).map(([k, v]) => `<strong>${k}:</strong> ${v}`).join('<br>');
            }
            return value;
        };

        container.innerHTML = `
            <div class="session-info-item">
                <div class="session-info-label">会话ID</div>
                <div class="session-info-value">${info.session_id}</div>
            </div>
            <div class="session-info-item">
                <div class="session-info-label">基本信息</div>
                <div class="session-info-value">${formatValue(info.basics)}</div>
            </div>
            <div class="session-info-item">
                <div class="session-info-label">疾病</div>
                <div class="session-info-value">${info.disease}</div>
            </div>
            <div class="session-info-item">
                <div class="session-info-label">症状</div>
                <div class="session-info-value">${formatValue(info.symptoms)}</div>
            </div>
            <div class="session-info-item">
                <div class="session-info-label">性格特征</div>
                <div class="session-info-value">${formatValue(info.personalities)}</div>
            </div>
            <div class="session-info-item">
                <div class="session-info-label">检查结果</div>
                <div class="session-info-value">${formatValue(info.examinations)}</div>
            </div>
            <div class="session-info-item">
                <div class="session-info-label">消息数量</div>
                <div class="session-info-value">${info.total_messages} 条</div>
            </div>
        `;
    }

    async showHistory() {
        if (!AppState.currentSession) return;

        LoadingManager.show();
        try {
            const result = await APIClient.getHistory(AppState.currentSession.session_id);
            if (result.success) {
                this.displayHistoryModal(result.data);
                document.getElementById('historyModal').classList.add('show');
            }
        } catch (error) {
            NotificationManager.show('获取对话历史失败', 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    displayHistoryModal(data) {
        const container = document.getElementById('historyContent');
        
        if (data.history.length === 0) {
            container.innerHTML = '<p>暂无对话记录</p>';
            return;
        }

        container.innerHTML = data.history.map((item, index) => `
            <div class="session-info-item">
                <div class="session-info-label">第 ${index + 1} 轮对话</div>
                <div class="session-info-value">
                    <strong>医生:</strong> ${item.user_message}<br>
                    <strong>病人:</strong> ${item.sp_response}
                </div>
            </div>
        `).join('');
    }

    async deleteCurrentSession() {
        if (!AppState.currentSession) return;

        const confirmed = confirm(`确定要删除会话 "${AppState.currentSession.patient_name}" 吗？`);
        if (!confirmed) return;

        LoadingManager.show();
        try {
            const result = await APIClient.deleteSession(AppState.currentSession.session_id);
            if (result.success) {
                NotificationManager.show('会话已删除', 'success');
                AppState.currentSession = null;
                await this.loadSessions();
                this.updateUI();
            }
        } catch (error) {
            NotificationManager.show(`删除会话失败: ${error.message}`, 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    updateUI() {
        const welcomeMessage = document.getElementById('welcomeMessage');
        const patientInfo = document.querySelector('.patient-info');
        const chatInputContainer = document.getElementById('chatInputContainer');

        if (!AppState.currentSession) {
            welcomeMessage.style.display = 'block';
            patientInfo.style.display = 'none';
            chatInputContainer.style.display = 'none';
            document.getElementById('chatMessages').innerHTML = '';
        }
    }
}

// 初始化应用
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SPApp();
});

// 定期刷新会话列表
setInterval(async () => {
    if (app && AppState.isConnected) {
        await app.loadSessions();
    }
}, 30000); // 每30秒刷新一次
