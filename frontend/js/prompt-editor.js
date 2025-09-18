/**
 * Prompt编辑器相关的API和业务逻辑
 */

class PromptAPI {
    static async list() {
        return APIClient.request('/prompt/list');
    }

    static async load(filename) {
        return APIClient.request(`/prompt/load?filename=${encodeURIComponent(filename)}`);
    }

    static async save(filename, content) {
        return APIClient.request('/prompt/save', {
            method: 'POST',
            body: { filename, content }
        });
    }

    static async backup(filename, content) {
        return APIClient.request('/prompt/backup', {
            method: 'POST',
            body: { filename, content }
        });
    }

    static async create(filename, content = '') {
        return APIClient.request('/prompt/create', {
            method: 'POST',
            body: { filename, content }
        });
    }

    static async delete(filename) {
        return APIClient.request('/prompt/delete', {
            method: 'POST',
            body: { filename }
        });
    }

    static async getBackups() {
        return APIClient.request('/prompt/backups');
    }

    static async loadBackup(filename) {
        return APIClient.request(`/prompt/backup_load?filename=${encodeURIComponent(filename)}`);
    }

    static async restore(backupFilename, targetFilename) {
        return APIClient.request('/prompt/restore', {
            method: 'POST',
            body: { backup_filename: backupFilename, target_filename: targetFilename }
        });
    }

    static async getVars(filename) {
        return APIClient.request(`/prompt/vars?filename=${encodeURIComponent(filename)}`);
    }

    static async test(promptContent, context, doctorMessage) {
        return APIClient.request('/prompt/test', {
            method: 'POST',
            body: { prompt_content: promptContent, context, doctor_message: doctorMessage }
        });
    }
}

class PromptEditor {
    constructor() {
        this.currentFile = null;
        this.presets = [];
        this.isConnected = false;
        this.autoSaveDelay = 1000; // 1秒后自动保存草稿
        this.autoSaveTimer = null;
    }

    async init() {
        await this.checkConnection();
        setInterval(() => this.checkConnection(), 10000);
        await this.loadPresets();
        await this.loadPromptList();
        await this.loadBackupList();
        this.bindEvents();
    }

    async checkConnection() {
        this.isConnected = await ConnectionManager.checkConnection();
        if (this.isConnected) {
            NotificationManager.show('服务连接成功', 'success', null, 3000);
        } else {
            NotificationManager.show('无法连接到后端服务', 'error');
        }
    }

    async loadPresets() {
        try {
            const result = await APIClient.getPresets();
            if (result.success) {
                this.presets = result.data;
                this.updatePresetSelect();
            }
        } catch (error) {
            NotificationManager.show('加载预设病例失败: ' + error.message, 'error');
        }
    }

    updatePresetSelect() {
        const select = document.getElementById('testPresetSelect');
        if (!select) return;

        select.innerHTML = '<option value="">请选择预设病例</option>';
        this.presets.forEach(preset => {
            const option = document.createElement('option');
            option.value = preset.filename;
            option.textContent = preset.description;
            select.appendChild(option);
        });
    }

    async loadPromptList() {
        try {
            const select = document.getElementById('promptSelect');
            select.innerHTML = '<option value="">加载中...</option>';
            
            const result = await PromptAPI.list();
            if (result.success) {
                select.innerHTML = '<option value="">请选择Prompt文件</option>';
                result.data.forEach(filename => {
                    const opt = document.createElement('option');
                    opt.value = filename;
                    opt.textContent = filename;
                    select.appendChild(opt);
                });
                
                if (result.data.length > 0) {
                    select.value = result.data[0];
                    await this.loadPrompt(result.data[0]);
                }
            }
        } catch (error) {
            NotificationManager.show('加载Prompt文件列表失败: ' + error.message, 'error');
            document.getElementById('promptSelect').innerHTML = '<option value="">加载失败</option>';
        }
    }

    async loadPrompt(filename) {
        if (!filename) return;
        
        try {
            LoadingManager.show();
            const result = await PromptAPI.load(filename);
            if (result.success) {
                document.getElementById('promptEditor').value = result.data;
                this.currentFile = filename;
                await this.showVars(filename);
                this.loadDraft(); // 检查是否有草稿
                NotificationManager.show(`已加载 ${filename}`, 'success', null, 2000);
            }
        } catch (error) {
            NotificationManager.show('加载Prompt文件失败: ' + error.message, 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    async showVars(filename) {
        try {
            const result = await PromptAPI.getVars(filename);
            if (result.success) {
                const varList = document.getElementById('varList');
                if (result.data.length > 0) {
                    varList.innerHTML = '<strong>可用变量（点击插入）:</strong><br>' + 
                        result.data.map(v => `<span class="var-tag" onclick="promptEditor.insertVariable('${v}')">{${v}}</span>`).join(' ');
                } else {
                    varList.innerHTML = '<strong>可用变量:</strong> <em>无</em>';
                }
            }
        } catch (error) {
            console.error('获取变量失败:', error);
        }
    }

    insertVariable(varName) {
        const textarea = document.getElementById('promptEditor');
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const before = text.substring(0, start);
        const after = text.substring(end, text.length);
        
        textarea.value = before + `{${varName}}` + after;
        textarea.focus();
        
        const newPosition = start + varName.length + 2;
        textarea.setSelectionRange(newPosition, newPosition);
        
        this.debouncedSaveDraft();
        NotificationManager.show(`已插入变量 {${varName}}`, 'success', null, 1000);
    }

    async loadBackupList() {
        try {
            const result = await PromptAPI.getBackups();
            if (result.success) {
                const list = document.getElementById('backupList');
                if (result.data.length === 0) {
                    list.innerHTML = '<p style="color:#999;font-style:italic;">暂无副本</p>';
                    return;
                }
                
                list.innerHTML = result.data.map(f => `
                    <div class="backup-item">
                        <strong>${f}</strong>
                        <div style="margin-top:5px;">
                            <button class="btn btn-small btn-primary" onclick="promptEditor.loadBackup('${f}')">
                                <i class="fas fa-download"></i> 加载
                            </button>
                            <button class="btn btn-small btn-success" onclick="promptEditor.restoreBackup('${f}')" style="margin-left:5px;">
                                <i class="fas fa-undo"></i> 恢复为正式
                            </button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            NotificationManager.show('加载副本列表失败: ' + error.message, 'error');
        }
    }

    // 草稿管理
    saveDraft() {
        if (!this.currentFile) return;
        const content = document.getElementById('promptEditor').value;
        localStorage.setItem(`prompt_draft_${this.currentFile}`, content);
    }

    loadDraft() {
        if (!this.currentFile) return;
        const draft = localStorage.getItem(`prompt_draft_${this.currentFile}`);
        const currentContent = document.getElementById('promptEditor').value;
        
        if (draft && draft !== currentContent && draft.trim() !== '') {
            const loadDraftConfirm = confirm('检测到有未保存的草稿，是否加载？');
            if (loadDraftConfirm) {
                document.getElementById('promptEditor').value = draft;
                NotificationManager.show('已加载草稿', 'info', null, 2000);
            }
        }
    }

    removeDraft() {
        if (!this.currentFile) return;
        localStorage.removeItem(`prompt_draft_${this.currentFile}`);
    }

    bindEvents() {
        // 防抖的自动保存
        this.debouncedSaveDraft = Utils.debounce(() => this.saveDraft(), this.autoSaveDelay);

        // 编辑器事件
        const editor = document.getElementById('promptEditor');
        editor.addEventListener('input', () => this.debouncedSaveDraft());
        editor.addEventListener('blur', () => this.saveDraft());

        // 文件选择变化
        document.getElementById('promptSelect')?.addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadPrompt(e.target.value);
            }
        });

        // 数据源切换
        document.querySelectorAll('input[name="testDataSource"]')?.forEach(radio => {
            radio.addEventListener('change', this.handleTestDataSourceChange);
        });
    }

    handleTestDataSourceChange(e) {
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

    formatPrompt(text) {
        return text
            .replace(/\s+$/gm, '') // 去除行尾空格
            .replace(/\n{3,}/g, '\n\n') // 多个空行合并为两个
            .replace(/^\s+|\s+$/g, ''); // 去除首尾空格
    }
}

// 全局实例
let promptEditor;
