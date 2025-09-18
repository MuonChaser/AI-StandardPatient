# 后端项目结构说明

## 重构后的目录结构

```
backend/
├── app.py                  # 主应用入口（Flask应用工厂）
├── app_backup.py           # 原始单文件备份
├── config.py               # 配置管理
├── README.md               # 项目说明
├── models/                 # 数据模型层
│   ├── __init__.py
│   └── session.py          # 会话管理模型
├── services/               # 业务逻辑层
│   ├── __init__.py
│   ├── preset_service.py   # 预设病例服务
│   └── sp_service.py       # SP会话服务
├── api/                    # API路由层
│   ├── __init__.py
│   ├── health.py           # 健康检查API
│   ├── preset.py           # 预设病例API
│   └── sp.py               # SP会话API
└── utils/                  # 工具函数
  ├── __init__.py
  └── response.py         # API响应工具
```

## 模块说明

### 1. models/ - 数据模型层
- `session.py`: 会话管理器，负责SP会话的创建、删除、清理等操作

### 2. services/ - 业务逻辑层
- `preset_service.py`: 预设病例相关的业务逻辑
- `sp_service.py`: SP会话相关的业务逻辑，包括对话、历史记录等

### 3. api/ - API路由层
- `health.py`: 健康检查相关API
- `preset.py`: 预设病例相关API
- `sp.py`: SP会话相关API

### 4. utils/ - 工具函数
- `response.py`: 统一的API响应格式处理

## API 路由说明

### 健康检查接口
```
GET /api/health
```
- **功能**: 服务健康检查，返回服务状态和统计信息
- **响应**: 服务状态、活跃会话数、配置信息等

### 预设病例接口
```
GET /api/sp/presets
```
- **功能**: 获取所有可用的预设病例列表
- **响应**: 预设病例文件列表，包含病人姓名、疾病、症状等信息

### SP会话管理接口

#### 创建会话
```
POST /api/sp/session/create
```
- **功能**: 创建新的SP会话
- **请求参数**:
  ```json
  {
    "session_id": "string",
    "preset_file": "string (可选)",
    "custom_data": "object (可选)"
  }
  ```
- **响应**: 会话信息，包含会话ID、病人姓名、疾病等

#### 对话交互
```
POST /api/sp/session/<session_id>/chat
```
- **功能**: 与指定SP会话进行对话
- **请求参数**:
  ```json
  {
    "message": "string"
  }
  ```
- **响应**: 对话结果，包含用户消息、SP回复、时间戳等

#### 获取对话历史
```
GET /api/sp/session/<session_id>/history
```
- **功能**: 获取指定会话的完整对话历史
- **响应**: 对话历史列表，按时间顺序排列

#### 获取会话信息
```
GET /api/sp/session/<session_id>/info
```
- **功能**: 获取指定会话的详细信息
- **响应**: 会话基本信息、病例数据、统计信息等

#### 获取所有会话
```
GET /api/sp/sessions
```
- **功能**: 获取所有活跃会话的列表
- **响应**: 会话列表，包含会话ID、病人姓名、状态等

#### 删除会话
```
DELETE /api/sp/session/<session_id>
```
- **功能**: 删除指定的会话
- **响应**: 删除确认信息

#### 数据验证
```
POST /api/sp/data/validate
```
- **功能**: 验证SP数据格式是否正确
- **请求参数**: SP数据对象
- **响应**: 验证结果和数据摘要

## 请求到返回的调用路径

### 典型API请求的调用流程

#### 1. 创建会话 (`POST /api/sp/session/create`)
```
HTTP请求 → Flask路由 → api/sp.py:create_sp_session()
    ↓
services/sp_service.py:SPService.create_sp_session()
    ↓
models/session.py:SessionManager.create_session()
    ↓
utils/response.py:APIResponse.success() → JSON响应
```

#### 2. 对话交互 (`POST /api/sp/session/<id>/chat`)
```
HTTP请求 → Flask路由 → api/sp.py:chat_with_sp()
    ↓
services/sp_service.py:SPService.chat_with_sp()
    ↓
sp.py:SP.speak() (调用核心AI引擎)
    ↓
models/session.py:SessionManager.update_activity()
    ↓
utils/response.py:APIResponse.success() → JSON响应
```

#### 3. 获取预设病例 (`GET /api/sp/presets`)
```
HTTP请求 → Flask路由 → api/preset.py:get_presets()
    ↓
services/preset_service.py:PresetService.get_all_presets()
    ↓
文件系统访问 (读取presets/目录)
    ↓
utils/response.py:APIResponse.success() → JSON响应
```

### 错误处理流程
```
任何异常 → try/catch捕获
    ↓
ValueError → 400错误响应
    ↓
Exception → 500错误响应
    ↓
utils/response.py:APIResponse.error() → JSON错误响应
```
