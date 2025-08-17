# AI-StandardPatient

![AI-StandardPatient](assets/fig.png)

一个基于大语言模型的AI标准化病人（Standardized Patient, SP）系统，用于医学教育和临床技能训练。

## 项目简介

AI-StandardPatient 是一个智能的标准化病人模拟系统，能够：
- 根据预设的病历信息扮演特定疾病的病人
- 与医学生或医生进行自然的对话交流
- 模拟真实的病人行为和症状表达
- 支持多种疾病场景的配置

## 功能特性

### 🎭 角色扮演
- 基于病历数据进行真实的病人角色扮演
- 智能表达症状，避免直接透露诊断
- 支持个性化特质模拟

### 📋 标准化数据格式
- 定义标准的SP JSON格式
- 支持从自然语言病历转换为结构化数据
- 包含基本信息、症状、隐藏信息等完整病历要素

### 🤖 智能对话
- 基于OpenAI GPT模型的自然语言交互
- 记忆对话上下文
- 根据医生问题智能回应

### ⚙️ 灵活配置
- 支持多种大语言模型后端
- 可配置的环境变量设置
- 模块化的引擎架构

## 快速开始

### 🚀 一键启动（推荐）

```bash
# 一键启动前后端服务
python start_all.py

# 服务启动后自动打开浏览器
# 前端地址: http://localhost:3000
# 后端API: http://localhost:8080/api
```

### 📋 分别启动

#### 启动后端服务
```bash
# 方法1: 使用启动脚本
python start_server.py

# 方法2: 直接启动
cd backend
python app.py
```

#### 启动前端服务
```bash
# 方法1: 使用前端服务器
cd frontend
python server.py

# 方法2: 使用Python内置服务器
cd frontend
python -m http.server 3000
```

### 🌐 访问应用

- **前端界面**: http://localhost:3000 （直接访问根路径即可）
- **后端API**: http://localhost:8080/api
- **健康检查**: http://localhost:8080/api/health

### 环境要求
- Python 3.8+
- OpenAI API密钥或兼容的API服务

### 安装依赖
```bash
# 安装基础依赖
pip install -r requirements.txt

# 或使用启动脚本自动安装
python start_all.py
```

### 配置环境变量
1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，设置你的API密钥：
```bash
API_KEY=your-openai-api-key-here
MODEL_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo
```

## 项目结构

```
AI-StandardPatient/
├── README.md              # 项目说明文档
├── start_all.py           # 一键启动脚本
├── test_frontend.py       # 前端测试脚本
├── start_server.py        # 后端启动脚本
├── test_api.py           # API测试脚本
├── requirements.txt       # 依赖清单
├── .env.example          # 环境变量模板
├── sp.py                  # 命令行程序入口
├── sp_data.py             # SP数据结构定义
├── base_agent.py          # 基础Agent抽象类
├── backend/               # 后端API服务
│   ├── app.py            # Flask应用主文件
│   ├── config.py         # 配置管理
│   └── README.md         # 后端文档
├── frontend/              # Web前端界面
│   ├── index.html        # 主页面
│   ├── styles.css        # 样式文件
│   ├── app.js           # JavaScript应用
│   ├── server.py        # 前端服务器
│   └── README.md        # 前端文档
├── engine/                # 语言模型引擎
│   ├── __init__.py
│   ├── base_engine.py     # 引擎基类
│   └── gpt.py            # GPT引擎实现
├── presets/               # 预设病例数据
│   └── test.json         # 示例病例
├── tools/                 # 工具脚本
│   ├── generate_sp_json.py  # JSON生成工具
│   ├── SET_OPENAI.sh     # OpenAI配置脚本
│   └── SET_DEEPSEEK.sh   # DeepSeek配置脚本
└── assets/               # 资源文件
    ├── fig.pdf           # 项目图表
    └── fig.png
```

## 数据格式

### SP JSON 格式规范

SP数据包含以下主要字段：

```json
{
    "basics": {
        "name": "患者姓名",
        "性别": "男/女",
        "年龄": 40,
        "婚姻状况": "已婚",
        "职业": "职业描述",
        "联系方式": "电话号码",
        "地址": "住址"
    },
    "disease": "疾病名称",
    "symptoms": ["主要症状1", "主要症状2"],
    "symptom_details": {
        "症状详情": "具体描述"
    },
    "medical_history": {
        "既往病史": "病史描述",
        "手术史": "手术历史"
    },
    "hidden_info": {
        "问题": "对应回答"
    },
    "personalities": ["性格特征1", "性格特征2"]
}
```

## 使用方式

### 🌐 Web界面（推荐）

1. **启动服务**：
   ```bash
   python start_all.py
   ```

2. **访问界面**：
   - 浏览器会自动打开前端界面
   - 或手动访问 http://localhost:3000

3. **创建会话**：
   - 在左侧输入会话ID
   - 选择预设病例或输入自定义数据
   - 点击"创建会话"

4. **开始对话**：
   - 在聊天区域输入医生问题
   - AI病人会根据病例设定回答
   - 支持快速问题模板

### 💻 命令行界面

对于喜欢命令行的用户：

```bash
# 直接运行命令行版本
python sp.py
```

### 📡 API接口

对于开发者集成：

```bash
# 启动API服务
cd backend
python app.py

# API文档地址: http://localhost:8080/api/health
```

详细API文档请参考 `backend/README.md`。

## 配置说明

### 环境变量

- `API_KEY`: 大语言模型API密钥
- `MODEL_BASE`: API基础URL
- `MODEL_NAME`: 使用的模型名称

### 支持的模型

- OpenAI GPT系列模型
- 其他兼容OpenAI API的模型服务

## 开发指南

### 添加新的引擎

1. 在 `engine/` 目录下创建新的引擎文件
2. 继承 `Engine` 基类
3. 实现 `get_response` 方法

### 扩展数据格式

1. 修改 `sp_data.py` 中的 `Sp_data` 类
2. 添加新的属性和对应的setter/getter
3. 更新JSON格式规范

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 许可证

本项目基于MIT许可证开源。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目链接: [https://github.com/MuonChaser/AI-StandardPatient](https://github.com/MuonChaser/AI-StandardPatient)
- 问题反馈: [Issues](https://github.com/MuonChaser/AI-StandardPatient/issues)

## 致谢

感谢所有为医学教育数字化做出贡献的开发者和医学专家。