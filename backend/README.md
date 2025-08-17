# Flask后端API文档

## 快速启动

### 1. 环境配置

复制环境变量模板文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的API密钥：
```bash
# 必需配置
API_KEY=your-openai-api-key-here
MODEL_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo

# 可选配置
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### 2. 启动服务

使用启动脚本（推荐）：
```bash
python start_server.py
```

或直接启动：
```bash
cd backend
python app.py
```

服务将在 `http://localhost:5000` 启动。

## API接口文档

### 基础信息

- **基础URL**: `http://localhost:5000/api`
- **响应格式**: JSON
- **编码**: UTF-8

### 统一响应格式

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {...}
}
```

### 接口列表

#### 1. 健康检查

**GET** `/api/health`

检查服务运行状态。

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "服务正常运行",
  "data": {
    "status": "running",
    "timestamp": "2025-08-17T10:30:00",
    "active_sessions": 2,
    "expired_sessions_cleaned": 0,
    "config": {
      "debug": true,
      "model_name": "gpt-3.5-turbo",
      "max_sessions": 100
    }
  }
}
```

#### 2. 获取预设病例列表

**GET** `/api/sp/presets`

获取所有可用的预设病例文件。

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "获取到 1 个预设病例",
  "data": [
    {
      "filename": "test.json",
      "name": "廖祖云",
      "disease": "发热",
      "symptoms": ["发热", "畏寒"],
      "description": "廖祖云 - 发热"
    }
  ]
}
```

#### 3. 创建SP会话

**POST** `/api/sp/session/create`

创建一个新的标准化病人会话。

**请求参数**:
```json
{
  "session_id": "session_001",
  "preset_file": "test.json"
}
```

或使用自定义数据：
```json
{
  "session_id": "session_002",
  "custom_data": {
    "basics": {
      "name": "张三",
      "性别": "男",
      "年龄": 30
    },
    "disease": "感冒",
    "symptoms": ["头痛", "发热"],
    "hiddens": [
      {"过敏史": "无明显过敏史"}
    ],
    "personalities": ["性格开朗", "配合治疗"]
  }
}
```

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "SP会话 session_001 创建成功",
  "data": {
    "session_id": "session_001",
    "patient_name": "廖祖云",
    "disease": "发热",
    "symptoms": ["发热", "畏寒"],
    "created_at": "2025-08-17T10:30:00"
  }
}
```

#### 4. 与SP对话

**POST** `/api/sp/session/<session_id>/chat`

与指定的标准化病人进行对话。

**请求参数**:
```json
{
  "message": "您好，请问您哪里不舒服？"
}
```

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "对话成功",
  "data": {
    "session_id": "session_001",
    "user_message": "您好，请问您哪里不舒服？",
    "sp_response": "医生您好，我这两天一直发热，还有点畏寒，主要是晚上比较严重。",
    "timestamp": "2025-08-17T10:30:00",
    "message_count": 1
  }
}
```

#### 5. 获取对话历史

**GET** `/api/sp/session/<session_id>/history`

获取指定会话的完整对话历史。

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "获取对话历史成功",
  "data": {
    "session_id": "session_001",
    "total_messages": 2,
    "history": [
      {
        "user_message": "您好，请问您哪里不舒服？",
        "sp_response": "医生您好，我这两天一直发热，还有点畏寒...",
        "timestamp": "第1轮对话"
      }
    ]
  }
}
```

#### 6. 获取会话信息

**GET** `/api/sp/session/<session_id>/info`

获取指定会话的详细信息。

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "获取会话信息成功",
  "data": {
    "session_id": "session_001",
    "basics": {
      "name": "廖祖云",
      "性别": "男",
      "年龄": 40
    },
    "disease": "发热",
    "symptoms": ["发热", "畏寒"],
    "personalities": ["文化水平较高..."],
    "examinations": [
      {"体温": "38.5°C"}
    ],
    "total_messages": 2
  }
}
```

#### 7. 获取所有会话列表

**GET** `/api/sp/sessions`

获取所有活跃的会话列表。

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "获取到 2 个活跃会话",
  "data": {
    "total_sessions": 2,
    "max_sessions": 100,
    "sessions": [
      {
        "session_id": "session_001",
        "patient_name": "廖祖云",
        "disease": "发热",
        "message_count": 2,
        "created_at": "2025-08-17T10:30:00",
        "last_activity": "2025-08-17T10:35:00",
        "status": "active"
      }
    ]
  }
}
```

#### 8. 删除会话

**DELETE** `/api/sp/session/<session_id>`

删除指定的会话。

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "会话 session_001 已删除",
  "data": {
    "session_id": "session_001",
    "patient_name": "廖祖云",
    "message_count": 2
  }
}
```

#### 9. 验证SP数据格式

**POST** `/api/sp/data/validate`

验证标准化病人数据的格式是否正确。

**请求参数**:
```json
{
  "basics": {
    "name": "张三",
    "性别": "男"
  },
  "disease": "感冒",
  "symptoms": ["头痛", "发热"]
}
```

**响应示例**:
```json
{
  "code": 200,
  "success": true,
  "message": "数据验证成功",
  "data": {
    "valid": true,
    "message": "SP数据格式验证通过",
    "data_summary": {
      "patient_name": "张三",
      "disease": "感冒",
      "symptoms_count": 2,
      "has_personalities": false,
      "has_hiddens": false,
      "has_examinations": false
    }
  }
}
```

## 错误处理

### 错误响应格式

```json
{
  "code": 400,
  "success": false,
  "message": "错误信息",
  "data": null
}
```

### 常见错误码

- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 使用示例

### Python客户端示例

```python
import requests
import json

BASE_URL = "http://localhost:5000/api"

# 1. 检查服务状态
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. 获取预设病例
response = requests.get(f"{BASE_URL}/sp/presets")
presets = response.json()["data"]
print(f"可用预设: {[p['name'] for p in presets]}")

# 3. 创建会话
session_data = {
    "session_id": "test_session",
    "preset_file": "test.json"
}
response = requests.post(f"{BASE_URL}/sp/session/create", json=session_data)
print(response.json())

# 4. 对话
chat_data = {
    "message": "您好，请问您哪里不舒服？"
}
response = requests.post(f"{BASE_URL}/sp/session/test_session/chat", json=chat_data)
result = response.json()
print(f"病人回复: {result['data']['sp_response']}")

# 5. 获取对话历史
response = requests.get(f"{BASE_URL}/sp/session/test_session/history")
print(response.json())

# 6. 删除会话
response = requests.delete(f"{BASE_URL}/sp/session/test_session")
print(response.json())
```

### JavaScript客户端示例

```javascript
const BASE_URL = "http://localhost:5000/api";

// 创建会话
async function createSession() {
    const response = await fetch(`${BASE_URL}/sp/session/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: 'web_session',
            preset_file: 'test.json'
        })
    });
    return response.json();
}

// 发送消息
async function sendMessage(sessionId, message) {
    const response = await fetch(`${BASE_URL}/sp/session/${sessionId}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
    });
    return response.json();
}

// 使用示例
createSession().then(result => {
    console.log('会话创建结果:', result);
    
    sendMessage('web_session', '您好，请问您哪里不舒服？').then(chatResult => {
        console.log('病人回复:', chatResult.data.sp_response);
    });
});
```

## 配置说明

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `API_KEY` | 是 | - | OpenAI API密钥 |
| `MODEL_BASE` | 否 | https://api.openai.com/v1 | API基础URL |
| `MODEL_NAME` | 否 | gpt-3.5-turbo | 模型名称 |
| `FLASK_HOST` | 否 | 0.0.0.0 | 服务监听地址 |
| `FLASK_PORT` | 否 | 5000 | 服务端口 |
| `FLASK_DEBUG` | 否 | True | 调试模式 |
| `MAX_SESSIONS` | 否 | 100 | 最大会话数 |
| `SESSION_TIMEOUT` | 否 | 3600 | 会话超时时间(秒) |

### 性能优化

1. **会话管理**: 系统会自动清理超时的会话，释放内存
2. **并发控制**: 限制最大会话数量，防止资源耗尽
3. **错误处理**: 完善的错误处理和日志记录

## 部署说明

### 开发环境
```bash
python start_server.py
```

### 生产环境
推荐使用gunicorn：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "backend/app.py"]
```

## 故障排除

### 常见问题

1. **API_KEY未设置**
   - 确保在`.env`文件中正确设置了`API_KEY`

2. **端口被占用**
   - 修改`.env`文件中的`FLASK_PORT`

3. **预设文件不存在**
   - 确保`presets/`目录下有`.json`格式的病例文件

4. **模块导入错误**
   - 确保在项目根目录运行服务
   - 检查Python路径设置

### 日志查看

开发模式下，错误信息会直接显示在控制台。生产环境建议配置日志文件。
