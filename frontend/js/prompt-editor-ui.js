/**
 * Prompt编辑器的事件处理和UI交互
 */

class PromptEditorUI {
    constructor(editor) {
        this.editor = editor;
        this.bindAllEvents();
    }

    bindAllEvents() {
        this.bindFileOperations();
        this.bindEditorOperations();
        this.bindTestOperations();
        this.bindBackupOperations();
    }

    bindFileOperations() {
        // 加载文件
        document.getElementById('loadPromptBtn')?.addEventListener('click', async () => {
            const filename = document.getElementById('promptSelect').value;
            if (!filename) {
                NotificationManager.show('请先选择Prompt文件', 'warning');
                return;
            }
            await this.editor.loadPrompt(filename);
        });

        // 新建文件
        document.getElementById('newPromptBtn')?.addEventListener('click', async () => {
            await this.createNewPrompt();
        });

        // 删除文件
        document.getElementById('deletePromptBtn')?.addEventListener('click', async () => {
            await this.deletePrompt();
        });

        // 保存文件
        document.getElementById('saveBtn')?.addEventListener('click', async () => {
            await this.savePrompt();
        });
    }

    bindEditorOperations() {
        // 格式化
        document.getElementById('formatBtn')?.addEventListener('click', () => {
            const textarea = document.getElementById('promptEditor');
            textarea.value = this.editor.formatPrompt(textarea.value);
            NotificationManager.show('内容已格式化', 'success', null, 1000);
            this.editor.debouncedSaveDraft();
        });
    }

    bindTestOperations() {
        // 测试对话
        document.getElementById('testBtn')?.addEventListener('click', async () => {
            await this.performTest();
        });
    }

    bindBackupOperations() {
        // 保存副本
        document.getElementById('backupBtn')?.addEventListener('click', async () => {
            await this.createBackup();
        });
    }

    async createNewPrompt() {
        const filename = prompt('请输入新Prompt文件名（建议以.txt结尾）:');
        if (!filename) return;
        
        if (!filename.endsWith('.txt')) {
            NotificationManager.show('文件名建议以.txt结尾', 'warning');
        }
        
        try {
            LoadingManager.show();
            const result = await PromptAPI.create(filename, '');
            if (result.success) {
                NotificationManager.show('新建成功', 'success');
                await this.editor.loadPromptList();
                document.getElementById('promptSelect').value = filename;
                await this.editor.loadPrompt(filename);
            }
        } catch (error) {
            NotificationManager.show('新建失败: ' + error.message, 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    async deletePrompt() {
        const filename = document.getElementById('promptSelect').value;
        if (!filename) {
            NotificationManager.show('请先选择要删除的Prompt文件', 'warning');
            return;
        }
        
        if (!confirm(`确定要删除 ${filename} 吗？此操作不可撤销！`)) return;
        
        try {
            LoadingManager.show();
            const result = await PromptAPI.delete(filename);
            if (result.success) {
                NotificationManager.show('已删除', 'success');
                await this.editor.loadPromptList();
                document.getElementById('promptEditor').value = '';
                this.editor.currentFile = null;
            }
        } catch (error) {
            NotificationManager.show('删除失败: ' + error.message, 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    async savePrompt() {
        const filename = document.getElementById('promptSelect').value;
        if (!filename) {
            NotificationManager.show('请先选择Prompt文件', 'warning');
            return;
        }
        
        if (!confirm('确定要覆盖原文件吗？此操作不可撤销！')) return;
        
        const content = document.getElementById('promptEditor').value;
        try {
            LoadingManager.show();
            const result = await PromptAPI.save(filename, content);
            if (result.success) {
                NotificationManager.show('已覆盖保存', 'success');
                this.editor.removeDraft();
                await this.editor.loadPromptList();
            }
        } catch (error) {
            NotificationManager.show('保存失败: ' + error.message, 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    async createBackup() {
        const filename = document.getElementById('promptSelect').value;
        if (!filename) {
            NotificationManager.show('请先选择Prompt文件', 'warning');
            return;
        }
        
        const content = document.getElementById('promptEditor').value;
        try {
            LoadingManager.show();
            const result = await PromptAPI.backup(filename, content);
            if (result.success) {
                NotificationManager.show('副本已保存', 'success');
                await this.editor.loadBackupList();
            }
        } catch (error) {
            NotificationManager.show('保存副本失败: ' + error.message, 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    async performTest() {
        const promptContent = document.getElementById('promptEditor').value;
        if (!promptContent.trim()) {
            NotificationManager.show('请先输入Prompt内容', 'warning');
            return;
        }

        const dataSource = document.querySelector('input[name="testDataSource"]:checked')?.value;
        if (!dataSource) {
            NotificationManager.show('请选择测试数据源', 'warning');
            return;
        }

        let context;
        try {
            if (dataSource === 'preset') {
                context = await this.getPresetContext();
            } else {
                context = await this.getCustomContext();
            }
        } catch (error) {
            NotificationManager.show('测试数据格式错误: ' + error.message, 'error');
            return;
        }

        const doctorMessage = document.getElementById('doctorMessage')?.value.trim();
        if (!doctorMessage) {
            NotificationManager.show('请输入医生问题', 'warning');
            return;
        }

        try {
            LoadingManager.show();
            const result = await PromptAPI.test(promptContent, context, doctorMessage);
            if (result.success) {
                this.showTestResult(result.data);
                NotificationManager.show('对话测试完成', 'success');
            }
        } catch (error) {
            NotificationManager.show('测试失败: ' + error.message, 'error');
        } finally {
            LoadingManager.hide();
        }
    }

    async getPresetContext() {
        const presetFile = document.getElementById('testPresetSelect')?.value;
        if (!presetFile) {
            throw new Error('请选择预设病例');
        }
        
        const preset = this.editor.presets.find(p => p.filename === presetFile);
        if (!preset || !preset.data) {
            throw new Error('预设数据无效');
        }
        
        return preset.data;
    }

    async getCustomContext() {
        const customDataText = document.getElementById('customTestData')?.value.trim();
        if (!customDataText) {
            throw new Error('请输入自定义测试数据');
        }
        
        return JSON.parse(customDataText);
    }

    showTestResult(result) {
        const testResultDiv = document.getElementById('testResult');
        const testResultContent = document.getElementById('testResultContent');
        
        if (testResultContent) {
            testResultContent.textContent = result;
        } else {
            testResultDiv.innerHTML = `<pre>${result}</pre>`;
        }
        
        if (testResultDiv) {
            testResultDiv.style.display = 'block';
        }
    }
}

// 备份操作的全局函数（供HTML onclick调用）
window.loadBackup = async function(filename) {
    try {
        LoadingManager.show();
        const result = await PromptAPI.loadBackup(filename);
        if (result.success) {
            document.getElementById('promptEditor').value = result.data;
            NotificationManager.show('已加载副本内容', 'success');
        }
    } catch (error) {
        NotificationManager.show('加载副本失败: ' + error.message, 'error');
    } finally {
        LoadingManager.hide();
    }
};

window.restoreBackup = async function(backupFilename) {
    const targetFilename = document.getElementById('promptSelect').value;
    if (!targetFilename) {
        NotificationManager.show('请先选择要恢复到的目标文件', 'warning');
        return;
    }
    
    if (!confirm(`确定要用副本 "${backupFilename}" 覆盖 "${targetFilename}" 吗？此操作不可撤销！`)) return;
    
    try {
        LoadingManager.show();
        const result = await PromptAPI.restore(backupFilename, targetFilename);
        if (result.success) {
            NotificationManager.show('副本已恢复为正式文件', 'success');
            await promptEditor.loadPrompt(targetFilename);
        }
    } catch (error) {
        NotificationManager.show('恢复失败: ' + error.message, 'error');
    } finally {
        LoadingManager.hide();
    }
};
