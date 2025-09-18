/**
 * Prompt编辑器 - 重构版本
 * 与 index.html 风格保持一致，简化错误处理
 */

// API配置
const API_BASE_URL = 'https://api.bwzhang.cn/api';

// 应用状态
const PromptEditorState = {
    isConnected: false,
    presets: [],
    currentFile: null,
    backups: []
};

// 通用API请求函数 - 简化版本
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };

    // 如果有body数据，转换为JSON字符串
    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    try {
        console.log(`发送API请求: ${config.method} ${url}`);
        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`API响应:`, data);
        
        if (!data.success) {
            throw new Error(data.message || 'API调用失败');
        }
        
        return data.data;
    } catch (error) {
        console.error(`API请求失败 [${endpoint}]:`, error);
        showNotification(`API请求失败: ${error.message}`, 'error');
        throw error;
    }
}

// 通知显示函数
function showNotification(message, type = 'info') {
    const container = document.getElementById('notifications');
    if (!container) {
        alert(message);
        return;
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;

    container.appendChild(notification);

    // 3秒后自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);

    // 点击移除
    notification.addEventListener('click', () => {
        notification.remove();
    });
}

// 加载动画控制
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// 连接状态检查
async function checkConnection() {
    try {
        await apiRequest('/health');
        PromptEditorState.isConnected = true;
        updateConnectionStatus(true);
    } catch (error) {
        PromptEditorState.isConnected = false;
        updateConnectionStatus(false);
    }
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (!statusEl) return;

    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('.status-text');
    
    if (dot && text) {
        if (connected) {
            dot.className = 'status-dot connected';
            text.textContent = '服务正常';
        } else {
            dot.className = 'status-dot error';
            text.textContent = '连接失败';
        }
    }
}

// 加载预设列表
async function loadPresets() {
    try {
        console.log('开始加载预设列表...');
        const presets = await apiRequest('/sp/presets');
        PromptEditorState.presets = presets;
        updatePresetSelect();
        console.log('预设列表加载成功:', presets);
    } catch (error) {
        console.error('加载预设失败:', error);
        showNotification('加载预设失败', 'error');
    }
}

function updatePresetSelect() {
    const select = document.getElementById('testPresetSelect');
    if (!select) return;

    select.innerHTML = '<option value="">请选择预设病例</option>';
    
    PromptEditorState.presets.forEach(preset => {
        const option = document.createElement('option');
        option.value = preset.filename;
        option.textContent = preset.description || preset.filename;
        select.appendChild(option);
    });
}

// 加载Prompt文件列表
async function loadPromptList() {
    try {
        console.log('开始加载Prompt文件列表...');
        const select = document.getElementById('promptSelect');
        if (!select) {
            console.error('找不到promptSelect元素');
            return;
        }

        select.innerHTML = '<option value="">加载中...</option>';
        
        const files = await apiRequest('/prompt/list');
        console.log('获取到的Prompt文件列表:', files);
        
        select.innerHTML = '<option value="">请选择Prompt文件</option>';
        
        if (Array.isArray(files) && files.length > 0) {
            files.forEach(filename => {
                const option = document.createElement('option');
                option.value = filename;
                option.textContent = filename;
                select.appendChild(option);
            });
            
            // 自动选择第一个文件
            select.value = files[0];
            PromptEditorState.currentFile = files[0];
            await loadPrompt(files[0]);
        } else {
            select.innerHTML = '<option value="">暂无Prompt文件</option>';
            showNotification('暂无Prompt文件', 'warning');
        }
    } catch (error) {
        console.error('加载Prompt文件列表失败:', error);
        const select = document.getElementById('promptSelect');
        if (select) {
            select.innerHTML = '<option value="">加载失败</option>';
        }
    }
}

// 加载单个Prompt文件
async function loadPrompt(filename) {
    if (!filename) {
        showNotification('请选择要加载的文件', 'warning');
        return;
    }

    try {
        showLoading();
        console.log('加载Prompt文件:', filename);
        
        const content = await apiRequest(`/prompt/load?filename=${encodeURIComponent(filename)}`);
        
        const editor = document.getElementById('promptEditor');
        if (editor) {
            editor.value = content;
            PromptEditorState.currentFile = filename;
            
            // 加载变量列表
            await loadVariables(filename);
            
            showNotification(`已加载 ${filename}`, 'success');
        } else {
            console.error('找不到promptEditor元素');
        }
    } catch (error) {
        console.error('加载Prompt文件失败:', error);
    } finally {
        hideLoading();
    }
}

// 加载变量列表
async function loadVariables(filename) {
    try {
        const vars = await apiRequest(`/prompt/vars?filename=${encodeURIComponent(filename)}`);
        const varList = document.getElementById('varList');
        
        if (varList) {
            if (Array.isArray(vars) && vars.length > 0) {
                varList.innerHTML = '<strong>可用变量（点击插入）:</strong><br>' + 
                    vars.map(v => `<span class="var-tag" onclick="insertVariable('${v}')">{${v}}</span>`).join(' ');
            } else {
                varList.innerHTML = '<strong>可用变量:</strong> <em>无</em>';
            }
        }
    } catch (error) {
        console.error('加载变量失败:', error);
    }
}

// 插入变量到编辑器
function insertVariable(varName) {
    const textarea = document.getElementById('promptEditor');
    if (!textarea) return;

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
    
    showNotification(`已插入变量 {${varName}}`, 'success');
}

// 加载副本列表
async function loadBackupList() {
    try {
        console.log('开始加载副本列表...');
        const backups = await apiRequest('/prompt/backups');
        PromptEditorState.backups = backups;
        
        const list = document.getElementById('backupList');
        if (!list) return;
        
        if (Array.isArray(backups) && backups.length > 0) {
            list.innerHTML = backups.map(filename => `
                <div class="backup-item">
                    <strong>${filename}</strong>
                    <div style="margin-top:5px;">
                        <button class="btn btn-small btn-primary" onclick="loadBackup('${filename}')">
                            <i class="fas fa-download"></i> 加载
                        </button>
                        <button class="btn btn-small btn-success" onclick="restoreBackup('${filename}')" style="margin-left:5px;">
                            <i class="fas fa-undo"></i> 恢复
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            list.innerHTML = '<p style="color:#999;font-style:italic;">暂无副本</p>';
        }
    } catch (error) {
        console.error('加载副本列表失败:', error);
    }
}

// 加载副本内容
async function loadBackup(filename) {
    try {
        showLoading();
        const content = await apiRequest(`/prompt/backup_load?filename=${encodeURIComponent(filename)}`);
        
        const editor = document.getElementById('promptEditor');
        if (editor) {
            editor.value = content;
            showNotification(`已加载副本 ${filename}`, 'success');
        }
    } catch (error) {
        console.error('加载副本失败:', error);
    } finally {
        hideLoading();
    }
}

// 恢复副本为正式文件
async function restoreBackup(backupFilename) {
    const targetFilename = PromptEditorState.currentFile;
    if (!targetFilename) {
        showNotification('请先选择要恢复到的目标文件', 'warning');
        return;
    }
    
    if (!confirm(`确定要用副本 "${backupFilename}" 覆盖 "${targetFilename}" 吗？`)) {
        return;
    }
    
    try {
        showLoading();
        await apiRequest('/prompt/restore', {
            method: 'POST',
            body: { 
                backup_filename: backupFilename, 
                target_filename: targetFilename 
            }
        });
        
        showNotification('副本已恢复为正式文件', 'success');
        await loadPrompt(targetFilename);
    } catch (error) {
        console.error('恢复副本失败:', error);
    } finally {
        hideLoading();
    }
}

// 保存副本
async function saveBackup() {
    const filename = PromptEditorState.currentFile;
    const content = document.getElementById('promptEditor')?.value;
    
    if (!filename) {
        showNotification('请先选择文件', 'warning');
        return;
    }
    
    if (!content) {
        showNotification('编辑器内容为空', 'warning');
        return;
    }
    
    try {
        showLoading();
        await apiRequest('/prompt/backup', {
            method: 'POST',
            body: { filename, content }
        });
        
        showNotification('副本已保存', 'success');
        await loadBackupList();
    } catch (error) {
        console.error('保存副本失败:', error);
    } finally {
        hideLoading();
    }
}

// 覆盖保存
async function savePrompt() {
    const filename = PromptEditorState.currentFile;
    const content = document.getElementById('promptEditor')?.value;
    
    if (!filename) {
        showNotification('请先选择文件', 'warning');
        return;
    }
    
    if (!confirm('确定要覆盖原文件吗？此操作不可撤销！')) {
        return;
    }
    
    try {
        showLoading();
        await apiRequest('/prompt/save', {
            method: 'POST',
            body: { filename, content }
        });
        
        showNotification('文件已保存', 'success');
    } catch (error) {
        console.error('保存文件失败:', error);
    } finally {
        hideLoading();
    }
}

// 另存为新文件
async function saveAsPrompt() {
    const content = document.getElementById('promptEditor')?.value;
    
    if (!content) {
        showNotification('编辑器内容为空', 'warning');
        return;
    }
    
    const filename = prompt('请输入新文件名（建议以.txt结尾）:');
    if (!filename) return;
    
    try {
        showLoading();
        await apiRequest('/prompt/create', {
            method: 'POST',
            body: { filename, content }
        });
        
        showNotification(`文件已保存为 ${filename}`, 'success');
        await loadPromptList();
        
        // 自动选择新保存的文件
        const select = document.getElementById('promptSelect');
        if (select) {
            select.value = filename;
            PromptEditorState.currentFile = filename;
        }
    } catch (error) {
        console.error('另存为失败:', error);
    } finally {
        hideLoading();
    }
}

// 新建文件
async function createNewPrompt() {
    const filename = prompt('请输入新文件名（建议以.txt结尾）:');
    if (!filename) return;
    
    try {
        showLoading();
        await apiRequest('/prompt/create', {
            method: 'POST',
            body: { filename, content: '' }
        });
        
        showNotification('文件创建成功', 'success');
        await loadPromptList();
        
        // 自动选择新创建的文件
        const select = document.getElementById('promptSelect');
        if (select) {
            select.value = filename;
            PromptEditorState.currentFile = filename;
            await loadPrompt(filename);
        }
    } catch (error) {
        console.error('创建文件失败:', error);
    } finally {
        hideLoading();
    }
}

// 删除文件
async function deletePrompt() {
    const filename = PromptEditorState.currentFile;
    if (!filename) {
        showNotification('请先选择要删除的文件', 'warning');
        return;
    }
    
    if (!confirm(`确定要删除文件 "${filename}" 吗？此操作不可撤销！`)) {
        return;
    }
    
    try {
        showLoading();
        await apiRequest('/prompt/delete', {
            method: 'POST',
            body: { filename }
        });
        
        showNotification('文件已删除', 'success');
        
        // 清空编辑器并重新加载列表
        const editor = document.getElementById('promptEditor');
        if (editor) {
            editor.value = '';
        }
        
        PromptEditorState.currentFile = null;
        await loadPromptList();
    } catch (error) {
        console.error('删除文件失败:', error);
    } finally {
        hideLoading();
    }
}

// 格式化内容
function formatPrompt() {
    const editor = document.getElementById('promptEditor');
    if (!editor) return;
    
    const content = editor.value;
    const formatted = content
        .replace(/\s+$/gm, '') // 去除行尾空格
        .replace(/\n{3,}/g, '\n\n') // 多个空行合并为两个
        .replace(/^\s+|\s+$/g, ''); // 去除首尾空格
    
    editor.value = formatted;
    showNotification('内容已格式化', 'success');
}

// 测试功能
async function testPrompt() {
    const content = document.getElementById('promptEditor')?.value;
    const doctorMessage = document.getElementById('doctorMessage')?.value;
    
    if (!content) {
        showNotification('请先输入Prompt内容', 'warning');
        return;
    }
    
    if (!doctorMessage) {
        showNotification('请输入医生问题', 'warning');
        return;
    }
    
    // 获取测试数据
    const dataSource = document.querySelector('input[name="testDataSource"]:checked')?.value;
    let context = {};
    
    if (dataSource === 'preset') {
        const presetFile = document.getElementById('testPresetSelect')?.value;
        if (!presetFile) {
            showNotification('请选择预设病例', 'warning');
            return;
        }
        
        const preset = PromptEditorState.presets.find(p => p.filename === presetFile);
        if (preset && preset.data) {
            context = preset.data;
        } else {
            showNotification('预设数据无效', 'error');
            return;
        }
    } else {
        const customData = document.getElementById('customTestData')?.value;
        if (!customData) {
            showNotification('请输入自定义测试数据', 'warning');
            return;
        }
        
        try {
            context = JSON.parse(customData);
        } catch (error) {
            showNotification('自定义数据格式错误', 'error');
            return;
        }
    }
    
    try {
        showLoading();
        const result = await apiRequest('/prompt/test', {
            method: 'POST',
            body: {
                prompt_content: content,
                context: context,
                doctor_message: doctorMessage
            }
        });
        
        // 显示测试结果
        const resultDiv = document.getElementById('testResult');
        const resultContent = document.getElementById('testResultContent');
        
        if (resultDiv && resultContent) {
            resultContent.textContent = result;
            resultDiv.style.display = 'block';
        }
        
        showNotification('测试完成', 'success');
    } catch (error) {
        console.error('测试失败:', error);
    } finally {
        hideLoading();
    }
}

// 事件绑定
function bindEvents() {
    // 文件选择变化
    const promptSelect = document.getElementById('promptSelect');
    if (promptSelect) {
        promptSelect.addEventListener('change', (e) => {
            const filename = e.target.value;
            if (filename) {
                PromptEditorState.currentFile = filename;
                loadPrompt(filename);
            }
        });
    }
    
    // 按钮事件
    const loadBtn = document.getElementById('loadPromptBtn');
    if (loadBtn) {
        loadBtn.addEventListener('click', () => {
            const filename = document.getElementById('promptSelect')?.value;
            if (filename) {
                loadPrompt(filename);
            }
        });
    }
    
    const backupBtn = document.getElementById('backupBtn');
    if (backupBtn) {
        backupBtn.addEventListener('click', saveBackup);
    }
    
    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', savePrompt);
    }
    
    const saveAsBtn = document.getElementById('saveAsBtn');
    if (saveAsBtn) {
        saveAsBtn.addEventListener('click', saveAsPrompt);
    }
    
    const newBtn = document.getElementById('newPromptBtn');
    if (newBtn) {
        newBtn.addEventListener('click', createNewPrompt);
    }
    
    const deleteBtn = document.getElementById('deletePromptBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', deletePrompt);
    }
    
    const formatBtn = document.getElementById('formatBtn');
    if (formatBtn) {
        formatBtn.addEventListener('click', formatPrompt);
    }
    
    const testBtn = document.getElementById('testBtn');
    if (testBtn) {
        testBtn.addEventListener('click', testPrompt);
    }
    
    // 测试数据源切换
    document.querySelectorAll('input[name="testDataSource"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const presetSection = document.getElementById('presetTestSection');
            const customSection = document.getElementById('customTestSection');
            
            if (e.target.value === 'preset') {
                if (presetSection) presetSection.style.display = 'block';
                if (customSection) customSection.style.display = 'none';
            } else {
                if (presetSection) presetSection.style.display = 'none';
                if (customSection) customSection.style.display = 'block';
            }
        });
    });
}

// 初始化应用
async function initPromptEditor() {
    console.log('初始化Prompt编辑器...');
    
    try {
        // 检查连接状态
        await checkConnection();
        
        // 加载数据
        await loadPresets();
        await loadPromptList();
        await loadBackupList();
        
        // 绑定事件
        bindEvents();
        
        // 定时检查连接状态
        setInterval(checkConnection, 10000);
        
        console.log('Prompt编辑器初始化完成');
    } catch (error) {
        console.error('初始化失败:', error);
        showNotification('初始化失败', 'error');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initPromptEditor);

// 导出全局函数供HTML调用
window.insertVariable = insertVariable;
window.loadBackup = loadBackup;
window.restoreBackup = restoreBackup;
window.saveAsPrompt = saveAsPrompt;
