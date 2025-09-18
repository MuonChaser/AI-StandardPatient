// API基础配置 - 与 index.js 保持一致
const API_BASE_URL = 'https://api.bwzhang.cn/api';

// 应用状态
const AppState = {
    isConnected: false,
    presets: [],
    currentFile: null
};

// API客户端 - 与 index.js 保持一致
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

// 通知系统 - 与 index.js 保持一致
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

// 加载管理器 - 与 index.js 保持一致
class LoadingManager {
    static show() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    static hide() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
}

// Prompt API 请求函数
async function promptApiRequest(endpoint, options = {}) {
    return APIClient.request(`/prompt${endpoint}`, options);
}


// 连接状态检测 - 与 index.js 保持一致
async function checkConnection() {
    try {
        const result = await APIClient.healthCheck();
        AppState.isConnected = result.success;
        updateConnectionStatus(true);
    } catch (error) {
        AppState.isConnected = false;
        updateConnectionStatus(false);
    }
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('.status-text');

    if (connected) {
        dot.className = 'status-dot connected';
        text.textContent = '服务正常';
    } else {
        dot.className = 'status-dot error';
        text.textContent = '连接失败';
    }
}

// 初始化
window.addEventListener('DOMContentLoaded', async () => {
    await checkConnection();
    setInterval(checkConnection, 10000); // 每10秒检查一次连接状态
    await loadPresets();
    await loadPromptList();
    await loadBackupList();
    bindEvents();
    loadDraft();
});

async function loadPresets() {
    try {
        const result = await APIClient.getPresets();
        if (result.success) {
            AppState.presets = result.data;
            updatePresetSelect();
        }
    } catch (error) {
        NotificationManager.show('加载预设病例失败', 'error');
    }
}

function updatePresetSelect() {
    const select = document.getElementById('testPresetSelect');
    select.innerHTML = '<option value="">请选择预设病例</option>';
    
    AppState.presets.forEach(preset => {
        const option = document.createElement('option');
        option.value = preset.filename;
        option.textContent = preset.description;
        select.appendChild(option);
    });
}

async function loadPromptList() {
    try {
        const select = document.getElementById('promptSelect');
        select.innerHTML = '<option value="">加载中...</option>';
        const files = await promptApiRequest('/list');
        select.innerHTML = '<option value="">请选择Prompt文件</option>';
        files.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f;
            opt.textContent = f;
            select.appendChild(opt);
        });
        if (files.length) {
            select.value = files[0];
            await loadPrompt(files[0]);
        }
    } catch (error) {
        NotificationManager.show('加载Prompt文件列表失败', 'error');
    }
}

async function loadPrompt(filename) {
    try {
        LoadingManager.show();
        const content = await promptApiRequest(`/load?filename=${filename}`);
        document.getElementById('promptEditor').value = content;
        AppState.currentFile = filename;
        await showVars(filename);
        NotificationManager.show(`已加载 ${filename}`, 'success');
    } catch (error) {
        NotificationManager.show('加载Prompt文件失败', 'error');
    } finally {
        LoadingManager.hide();
    }
}

async function showVars(filename) {
    try {
        const vars = await promptApiRequest(`/vars?filename=${filename}`);
        const varList = document.getElementById('varList');
        if (vars.length > 0) {
            varList.innerHTML = '<strong>可用变量（点击插入）:</strong><br>' + 
                vars.map(v => `<span class="var-tag" onclick="insertVariable('${v}')">{${v}}</span>`).join(' ');
        } else {
            varList.innerHTML = '<strong>可用变量:</strong> <em>无</em>';
        }
    } catch (error) {
        console.error('获取变量失败:', error);
    }
}

// 插入变量到编辑器光标位置
function insertVariable(varName) {
    const textarea = document.getElementById('promptEditor');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const before = text.substring(0, start);
    const after = text.substring(end, text.length);
    
    textarea.value = before + `{${varName}}` + after;
    textarea.focus();
    // 设置光标位置到插入变量后
    const newPosition = start + varName.length + 2;
    textarea.setSelectionRange(newPosition, newPosition);
    
    // 触发保存草稿
    saveDraft();
}

function bindEvents() {
    // 数据源切换
    document.querySelectorAll('input[name="testDataSource"]').forEach(radio => {
        radio.addEventListener('change', handleTestDataSourceChange);
    });

    document.getElementById('loadPromptBtn').onclick = async () => {
        const filename = document.getElementById('promptSelect').value;
        if (!filename) {
            NotificationManager.show('请先选择Prompt文件', 'warning');
            return;
        }
        await loadPrompt(filename);
    };

    document.getElementById('backupBtn').onclick = async () => {
        const filename = document.getElementById('promptSelect').value;
        if (!filename) {
            NotificationManager.show('请先选择Prompt文件', 'warning');
            return;
        }
        const content = document.getElementById('promptEditor').value;
        try {
            LoadingManager.show();
            await promptApiRequest('/backup', { method: 'POST', body: { filename, content } });
            NotificationManager.show('副本已保存', 'success');
            await loadBackupList();
        } catch (error) {
            NotificationManager.show('保存副本失败', 'error');
        } finally {
            LoadingManager.hide();
        }
    };

    document.getElementById('saveBtn').onclick = async () => {
        const filename = document.getElementById('promptSelect').value;
        if (!filename) {
            NotificationManager.show('请先选择Prompt文件', 'warning');
            return;
        }
        if (!confirm('确定要覆盖原文件吗？此操作不可撤销！')) return;
        
        const content = document.getElementById('promptEditor').value;
        try {
            LoadingManager.show();
            await promptApiRequest('/save', { method: 'POST', body: { filename, content } });
            NotificationManager.show('已覆盖保存', 'success');
            await loadPromptList();
            removeDraft();
        } catch (error) {
            NotificationManager.show('保存失败', 'error');
        } finally {
            LoadingManager.hide();
        }
    };

    document.getElementById('testBtn').onclick = async () => {
        await performTest();
    };

    document.getElementById('newPromptBtn').onclick = async () => {
        const filename = prompt('请输入新Prompt文件名（建议以.txt结尾）:');
        if (!filename) return;
        if (!filename.endsWith('.txt')) {
            NotificationManager.show('文件名建议以.txt结尾', 'warning');
        }
        try {
            LoadingManager.show();
            await promptApiRequest('/create', { method: 'POST', body: { filename, content: '' } });
            NotificationManager.show('新建成功', 'success');
            await loadPromptList();
            // 自动选择新建的文件
            document.getElementById('promptSelect').value = filename;
            await loadPrompt(filename);
        } catch (error) {
            NotificationManager.show('新建失败: ' + error.message, 'error');
        } finally {
            LoadingManager.hide();
        }
    };

    document.getElementById('deletePromptBtn').onclick = async () => {
        const filename = document.getElementById('promptSelect').value;
        if (!filename) {
            NotificationManager.show('请先选择要删除的Prompt文件', 'warning');
            return;
        }
        if (!confirm(`确定要删除 ${filename} 吗？此操作不可撤销！`)) return;
        
        try {
            LoadingManager.show();
            await promptApiRequest('/delete', { method: 'POST', body: { filename } });
            NotificationManager.show('已删除', 'success');
            await loadPromptList();
            document.getElementById('promptEditor').value = '';
        } catch (error) {
            NotificationManager.show('删除失败: ' + error.message, 'error');
        } finally {
            LoadingManager.hide();
        }
    };

    document.getElementById('formatBtn').onclick = () => {
        const textarea = document.getElementById('promptEditor');
        textarea.value = formatPrompt(textarea.value);
        NotificationManager.show('内容已格式化', 'success');
        saveDraft();
    };

    // 自动保存草稿
    document.getElementById('promptEditor').addEventListener('input', saveDraft);
    document.getElementById('promptEditor').addEventListener('blur', saveDraft);

    // Prompt文件选择变化
    document.getElementById('promptSelect').addEventListener('change', (e) => {
        if (e.target.value) {
            loadDraft();
        }
    });
}

function handleTestDataSourceChange(e) {
    const presetSection = document.getElementById('presetTestSection');
    const customSection = document.getElementById('customTestSection');
    
    if (e.target.value === 'preset') {
        presetSection.style.display = 'block';
        customSection.style.display = 'none';
    } else {
        presetSection.style.display = 'none';
        customSection.style.display = 'block';
    }
}

async function performTest() {
    const prompt_content = document.getElementById('promptEditor').value;
    if (!prompt_content.trim()) {
        NotificationManager.show('请先输入Prompt内容', 'warning');
        return;
    }

    const dataSource = document.querySelector('input[name="testDataSource"]:checked').value;
    let context;

    try {
        if (dataSource === 'preset') {
            const presetFile = document.getElementById('testPresetSelect').value;
            if (!presetFile) {
                NotificationManager.show('请选择预设病例', 'warning');
                return;
            }
            // 从预设获取数据
            const preset = AppState.presets.find(p => p.filename === presetFile);
            if (preset && preset.data) {
                context = preset.data;
            } else {
                NotificationManager.show('预设数据无效', 'error');
                return;
            }
        } else {
            const customDataText = document.getElementById('customTestData').value.trim();
            if (!customDataText) {
                NotificationManager.show('请输入自定义测试数据', 'warning');
                return;
            }
            context = JSON.parse(customDataText);
        }
    } catch (error) {
        NotificationManager.show('测试数据格式错误，请检查JSON格式', 'error');
        return;
    }

    const doctor_message = document.getElementById('doctorMessage').value.trim();
    if (!doctor_message) {
        NotificationManager.show('请输入医生问题', 'warning');
        return;
    }

    try {
        LoadingManager.show();
        const result = await promptApiRequest('/test', {
            method: 'POST',
            body: { prompt_content, context, doctor_message }
        });
        
        const testResultDiv = document.getElementById('testResult');
        const testResultContent = document.getElementById('testResultContent');
        testResultContent.textContent = result;
        testResultDiv.style.display = 'block';
        
        NotificationManager.show('对话测试完成', 'success');
    } catch (error) {
        NotificationManager.show('测试失败: ' + error.message, 'error');
    } finally {
        LoadingManager.hide();
    }
}

async function loadBackupList() {
    try {
        const list = document.getElementById('backupList');
        const files = await promptApiRequest('/backups');
        if (files.length === 0) {
            list.innerHTML = '<p style="color:#999;font-style:italic;">暂无副本</p>';
            return;
        }
        list.innerHTML = files.map(f => `
            <div class="backup-item">
                <strong>${f}</strong>
                <div style="margin-top:5px;">
                    <button class="btn btn-small btn-primary" onclick="loadBackup('${f}')">
                        <i class="fas fa-download"></i> 加载
                    </button>
                    <button class="btn btn-small btn-success" onclick="restoreBackup('${f}')" style="margin-left:5px;">
                        <i class="fas fa-undo"></i> 恢复为正式
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        NotificationManager.show('加载副本列表失败', 'error');
    }
}

async function loadBackup(filename) {
    try {
        LoadingManager.show();
        const content = await promptApiRequest(`/backup_load?filename=${filename}`);
        document.getElementById('promptEditor').value = content;
        NotificationManager.show('已加载副本内容', 'success');
    } catch (error) {
        NotificationManager.show('加载副本失败', 'error');
    } finally {
        LoadingManager.hide();
    }
}

async function restoreBackup(backup_filename) {
    const target_filename = document.getElementById('promptSelect').value;
    if (!target_filename) {
        NotificationManager.show('请先选择要恢复到的目标文件', 'warning');
        return;
    }
    if (!confirm(`确定要用副本 "${backup_filename}" 覆盖 "${target_filename}" 吗？此操作不可撤销！`)) return;
    
    try {
        LoadingManager.show();
        await promptApiRequest('/restore', { method: 'POST', body: { backup_filename, target_filename } });
        NotificationManager.show('副本已恢复为正式文件', 'success');
        await loadPrompt(target_filename);
    } catch (error) {
        NotificationManager.show('恢复失败: ' + error.message, 'error');
    } finally {
        LoadingManager.hide();
    }
}

// 自动保存草稿到本地
function saveDraft() {
    const filename = document.getElementById('promptSelect').value;
    if (!filename) return;
    const content = document.getElementById('promptEditor').value;
    localStorage.setItem('prompt_draft_' + filename, content);
}

function loadDraft() {
    const filename = document.getElementById('promptSelect').value;
    if (!filename) return;
    const draft = localStorage.getItem('prompt_draft_' + filename);
    if (draft && draft !== document.getElementById('promptEditor').value) {
        const loadDraftConfirm = confirm('检测到有未保存的草稿，是否加载？');
        if (loadDraftConfirm) {
            document.getElementById('promptEditor').value = draft;
        }
    }
}

function removeDraft() {
    const filename = document.getElementById('promptSelect').value;
    if (!filename) return;
    localStorage.removeItem('prompt_draft_' + filename);
}

// 简单格式化：去除多余空格和空行
function formatPrompt(text) {
    return text
        .replace(/\s+$/gm, '') // 去除行尾空格
        .replace(/\n{3,}/g, '\n\n') // 多个空行合并为两个
        .replace(/^\s+|\s+$/g, ''); // 去除首尾空格
}
