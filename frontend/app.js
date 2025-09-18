// API基础配置
const API_BASE_URL = 'https://api.bwzhang.cn/api';


// 应用状态
const AppState = {
    currentSession: null,
    sessions: [],
    presets: [],
    prompts: [],
    currentPrompt: null,
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

    static async getExamReport(sessionId) {
        return this.request(`/sp/session/${sessionId}/exam_report`);
    }

    static async getPrompts() {
        return this.request('/prompt/list');
    }

    static async getCurrentPrompt() {
        return this.request('/prompt/current');
    }

    static async setCurrentPrompt(filename) {
        return this.request('/prompt/set_current', {
            method: 'POST',
            body: JSON.stringify({ filename })
        });
    }

    static async getScoreReport(sessionId) {
        return this.request(`/scoring/report/${sessionId}`);
    }

    static async getScoreSummary(sessionId) {
        return this.request(`/scoring/summary/${sessionId}`);
    }

    static async getSuggestions(sessionId) {
        return this.request(`/scoring/suggestions/${sessionId}`);
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
        this.examReports = [];
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.checkConnection();
        await this.loadPresets();
        await this.loadPrompts();
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

        // Prompt选择
        const promptSelect = document.getElementById('promptSelect');
        if (promptSelect) {
            promptSelect.addEventListener('change', this.handlePromptChange.bind(this));
        }

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

        // 请求检查报告按钮
        document.getElementById('requestExamBtn').addEventListener('click', this.requestExamReport.bind(this));
        // 打开报告列表
        document.getElementById('examListBtn').addEventListener('click', this.showExamList.bind(this));
        // 查看评分报告
        document.getElementById('scoreReportBtn').addEventListener('click', this.showScoreReport.bind(this));

        // 关闭模态框
        document.getElementById('closeSessionInfo').addEventListener('click', () => {
            document.getElementById('sessionInfoModal').classList.remove('show');
        });
        document.getElementById('closeHistory').addEventListener('click', () => {
            document.getElementById('historyModal').classList.remove('show');
        });
        document.getElementById('closeExamModal').addEventListener('click', () => {
            document.getElementById('examModal').classList.remove('show');
        });
        document.getElementById('closeExamList').addEventListener('click', () => {
            document.getElementById('examListModal').classList.remove('show');
        });
        document.getElementById('closeScoreModal').addEventListener('click', () => {
            document.getElementById('scoreModal').classList.remove('show');
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

    async loadPrompts() {
        try {
            const result = await APIClient.getPrompts();
            if (result.success) {
                AppState.prompts = result.data;
                this.updatePromptSelect();
                
                // 获取当前使用的prompt
                const currentResult = await APIClient.getCurrentPrompt();
                if (currentResult.success) {
                    AppState.currentPrompt = currentResult.data;
                    this.updatePromptDisplay();
                }
            }
        } catch (error) {
            NotificationManager.show('加载Prompt列表失败', 'error');
        }
    }

    updatePresetSelect() {
        const select = document.getElementById('presetSelect');
        select.innerHTML = '<option value="">请选择预设病例</option>';
        
        AppState.presets.forEach(preset => {
            const option = document.createElement('option');
            option.value = preset.filename;
            // 显示病名而不是人名
            option.textContent =preset.description;
            select.appendChild(option);
        });
    }

    updatePromptSelect() {
        const select = document.getElementById('promptSelect');
        if (!select) return;
        
        select.innerHTML = '<option value="">请选择Prompt模板</option>';
        
        AppState.prompts.forEach(prompt => {
            const option = document.createElement('option');
            option.value = prompt;
            option.textContent = prompt;
            select.appendChild(option);
        });
    }

    updatePromptDisplay() {
        const select = document.getElementById('promptSelect');
        const display = document.getElementById('currentPromptDisplay');
        
        if (select && AppState.currentPrompt) {
            select.value = AppState.currentPrompt;
        }
        
        if (display) {
            display.textContent = AppState.currentPrompt || '未设置';
        }
    }

    async loadSessions() {
        try {
            const result = await APIClient.getSessions();
            if (result.success) {
                const currentSessionId = AppState.currentSession?.session_id;
                AppState.sessions = result.data.sessions;
                
                // 重新设置当前会话引用，确保引用的是最新的对象
                if (currentSessionId) {
                    const updatedCurrentSession = AppState.sessions.find(s => s.session_id === currentSessionId);
                    if (updatedCurrentSession) {
                        AppState.currentSession = updatedCurrentSession;
                    } else {
                        // 如果当前会话不存在了，清空引用
                        AppState.currentSession = null;
                    }
                }
                
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

    async handlePromptChange(e) {
        const selectedPrompt = e.target.value;
        if (!selectedPrompt) return;
        
        try {
            LoadingManager.show();
            const result = await APIClient.setCurrentPrompt(selectedPrompt);
            if (result.success) {
                AppState.currentPrompt = selectedPrompt;
                this.updatePromptDisplay();
                NotificationManager.show(`已切换到 ${selectedPrompt}`, 'success');
            }
        } catch (error) {
            NotificationManager.show('切换Prompt失败', 'error');
        } finally {
            LoadingManager.hide();
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

    async requestExamReport() {
        if (!AppState.currentSession) return;
        LoadingManager.show();
        try {
            const result = await APIClient.getExamReport(AppState.currentSession.session_id);
            if (result.success) {
                // 保存报告
                this.examReports.push({
                    session_id: AppState.currentSession.session_id,
                    timestamp: new Date().toLocaleString(),
                    report: result.data
                });
                NotificationManager.show('检查报告已获取', 'success');
                this.showExamModal(result.data);
            }
        } catch (error) {
            NotificationManager.show('获取检查报告失败', 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    showExamModal(report) {
        const container = document.getElementById('examModalContent');
        container.innerHTML = this.formatExamReport(report);
        document.getElementById('examModal').classList.add('show');
    }

    showExamList() {
        const container = document.getElementById('examListContent');
        if (this.examReports.length === 0) {
            container.innerHTML = '<p>暂无检查报告</p>';
        } else {
            container.innerHTML = this.examReports.map((item, idx) => `
                <div class="exam-list-item">
                    <span>第${idx + 1}份报告</span>
                    <span>${item.timestamp}</span>
                    <button class="btn btn-small" onclick="app.showExamModal(app.examReports[${idx}].report)">查看</button>
                </div>
            `).join('');
        }
        document.getElementById('examListModal').classList.add('show');
    }

    formatExamReport(report) {
        let html = '';
        if (report.physical_exam) {
            html += '<h4>体格检查</h4>';
            html += '<ul>' + Object.entries(report.physical_exam).map(([k, v]) => `<li><strong>${k}:</strong> ${v}</li>`).join('') + '</ul>';
        }
        if (report.auxiliary_exam) {
            html += '<h4>辅助检查</h4>';
            if (report.auxiliary_exam.blood) {
                html += '<strong>血常规:</strong><ul>' + Object.entries(report.auxiliary_exam.blood).map(([k, v]) => `<li>${k}: ${v}</li>`).join('') + '</ul>';
            }
            if (report.auxiliary_exam.urine) {
                html += '<strong>尿常规:</strong><ul>' + Object.entries(report.auxiliary_exam.urine).map(([k, v]) => `<li>${k}: ${v}</li>`).join('') + '</ul>';
            }
            if (report.auxiliary_exam.ultrasound) {
                html += `<strong>B超:</strong> ${report.auxiliary_exam.ultrasound}<br>`;
            }
        }
        return html || '<p>无检查数据</p>';
    }

    async showScoreReport() {
        if (!AppState.currentSession) {
            NotificationManager.show('请先选择一个会话', 'warning');
            return;
        }

        LoadingManager.show();
        try {
            const result = await APIClient.getScoreReport(AppState.currentSession.session_id);
            if (result.success) {
                this.displayScoreReport(result.data);
                document.getElementById('scoreModal').classList.add('show');
            }
        } catch (error) {
            NotificationManager.show('获取评分报告失败', 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    displayScoreReport(report) {
        const container = document.getElementById('scoreModalContent');
        const score = report.score_summary;
        
        // 获取评价等级的颜色
        const getScoreColor = (percentage) => {
            if (percentage >= 90) return '#4caf50';
            if (percentage >= 80) return '#8bc34a';
            if (percentage >= 70) return '#ff9800';
            if (percentage >= 60) return '#ff5722';
            return '#f44336';
        };
        
        // 判断是否为智能评分
        const isIntelligentScoring = score.scoring_method === 'intelligent_partial_matching';
        const displayScore = isIntelligentScoring ? score.recommended_score : score.percentage;
        
        let html = `
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 48px; font-weight: bold; color: ${getScoreColor(displayScore)};">
                    ${displayScore}%
                </div>
                <div style="font-size: 18px; margin: 10px 0;">
                    评价等级: <span style="color: ${getScoreColor(displayScore)}; font-weight: bold;">${score.evaluation.level}</span>
                </div>
                <div style="color: #666; margin-bottom: 20px;">
                    ${score.evaluation.comment}
                </div>
                ${isIntelligentScoring ? '<div style="color: #2196f3; font-size: 14px; margin-bottom: 10px;">🧠 AI智能评分系统</div>' : ''}
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div style="text-align: center; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: #2196f3;">${score.asked_questions}</div>
                    <div style="color: #666;">完全匹配</div>
                </div>
                <div style="text-align: center; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: #666;">${score.total_questions}</div>
                    <div style="color: #666;">总问题数</div>
                </div>
            </div>
        `;
        
        // 智能评分特有信息
        if (isIntelligentScoring) {
            html += `
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #1976d2;">📊 智能评分详情</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 14px;">
                        <div>完美匹配: <strong>${score.perfect_score}%</strong></div>
                        <div>部分匹配: <strong>${score.partial_score}%</strong></div>
                        <div>推荐得分: <strong>${score.recommended_score}%</strong></div>
                    </div>
                </div>
            `;
        }
        
        // 分类统计
        if (score.category_stats && Object.keys(score.category_stats).length > 0) {
            html += '<h4>分类完成情况</h4>';
            html += '<div style="margin-bottom: 20px;">';
            
            for (const [category, stats] of Object.entries(score.category_stats)) {
                const completionRate = stats.completion_rate || 0;
                html += `
                    <div style="margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span>${category}</span>
                            <span>${completionRate.toFixed(1)}% (${stats.asked_questions}/${stats.total_questions})</span>
                        </div>
                        <div style="background: #e0e0e0; border-radius: 10px; height: 8px; overflow: hidden;">
                            <div style="background: ${getScoreColor(completionRate)}; height: 100%; width: ${completionRate}%; transition: width 0.3s;"></div>
                        </div>
                    </div>
                `;
            }
            html += '</div>';
        }
        
        // 问题分类显示
        const showQuestionCategory = (questions, title, color, icon) => {
            if (questions && questions.length > 0) {
                html += `<h4 style="color: ${color};">${icon} ${title} (${questions.length})</h4>`;
                html += '<div style="max-height: 200px; overflow-y: auto;">';
                html += '<ul style="margin: 0; padding-left: 20px;">';
                questions.forEach(item => {
                    html += `<li style="color: ${color}; margin-bottom: 8px;">
                        <strong>${item.question}</strong>`;
                    
                    // 智能评分显示匹配度
                    if (item.best_match_score !== undefined) {
                        html += ` <span style="color: #666; font-size: 12px;">(匹配度: ${item.best_match_score.toFixed(1)}%)</span>`;
                    }
                    
                    if (item.description) {
                        html += `<br><span style="color: #666; font-size: 14px;">${item.description}</span>`;
                    }
                    
                    // 显示部分得分
                    if (item.partial_score !== undefined && item.partial_score > 0 && item.partial_score < item.weight) {
                        html += `<br><span style="color: #ff9800; font-size: 12px;">部分得分: ${item.partial_score.toFixed(2)}/${item.weight}</span>`;
                    }
                    
                    html += `</li>`;
                });
                html += '</ul></div>';
            }
        };
        
        // 智能评分的问题分类
        if (isIntelligentScoring) {
            showQuestionCategory(report.fully_matched_questions, '完全匹配的问题', '#4caf50', '✅');
            showQuestionCategory(report.partially_matched_questions, '部分匹配的问题', '#ff9800', '🔶');
            showQuestionCategory(report.missed_questions, '未匹配的问题', '#f44336', '❌');
        } else {
            // 传统评分的问题分类
            showQuestionCategory(report.asked_questions, '已询问的问题', '#4caf50', '✅');
            showQuestionCategory(report.missed_questions, '遗漏的问题', '#f44336', '❌');
        }
        
        // 改进建议
        if (report.system_info && report.system_info.scoring_method === "AI智能评分") {
            // 为智能评分获取建议
            this.displayIntelligentSuggestions(report);
        }
        
        container.innerHTML = html;
    }
    
    async displayIntelligentSuggestions(report) {
        try {
            if (!AppState.currentSession || !AppState.currentSession.session_id) {
                console.warn('No current session available for suggestions');
                return;
            }
            
            const sessionId = AppState.currentSession.session_id;
            const result = await APIClient.getSuggestions(sessionId);
            
            if (result.success && result.data.length > 0) {
                const suggestionsHtml = `
                    <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #ff9800;">
                        <h4 style="margin: 0 0 10px 0; color: #f57c00;">💡 AI智能建议</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            ${result.data.map(suggestion => `<li style="margin-bottom: 5px;">${suggestion}</li>`).join('')}
                        </ul>
                    </div>
                `;
                
                const container = document.getElementById('scoreModalContent');
                container.innerHTML += suggestionsHtml;
            }
        } catch (error) {
            console.warn('获取智能建议失败:', error);
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
