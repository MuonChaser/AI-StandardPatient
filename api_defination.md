# AI标准化病人系统后端 API 文档

## 通用说明
- 所有接口均为 RESTful 风格，返回 JSON 格式数据
- 后端服务默认端口：`http://localhost:3000`

---

## 1. 健康检查

- `GET /api/health`
  - 检查后端服务状态
  - 返回：`{"status": "ok"}`

---

## 2. 预设病例管理

- `GET /api/presets/list`
  - 获取所有预设病例列表
  - 返回：`[{ "id": 1, "description": "张三-社区获得性肺炎", ... }]`

- `GET /api/presets/<preset_id>`
  - 获取指定预设病例详情
  - 返回：完整病例 JSON

---

## 3. 会话管理

- `POST /api/sp/session`
  - 创建新会话
  - 参数：`{ "preset_id": 1 }`
  - 返回：`{ "session_id": 3, ... }`

- `GET /api/sp/session/<session_id>`
  - 获取会话详情

- `POST /api/sp/session/<session_id>/chat`
  - 向标准化病人发送消息
  - 参数：`{ "message": "..." }`
  - 返回：AI回复

---

## 4. 检查报告

- `POST /api/sp/session/<session_id>/exam_report`
  - 请求检查报告（如化验、影像等）
  - 参数：`{ "exam_type": "血常规" }`
  - 返回：报告内容

---

## 5. 评分系统

- `GET /api/sp/session/<session_id>/scoring_report`
  - 获取当前会话的评分报告
  - 返回：得分详情、未问到的隐藏问题等

---

## 6. Prompt 管理

- `GET /api/prompt/list`
  - 获取所有 prompt 列表

- `POST /api/prompt/save`
  - 保存/更新 prompt
  - 参数：`{ "name": "...", "content": "..." }`

- `POST /api/prompt/test`
  - 测试 prompt 效果
  - 参数：`{ "prompt_id": 1, "input": "..." }`
  - 返回：AI回复

---

## 7. 其他接口

- `GET /api/logs`
  - 获取系统运行日志（如有实现）

---

> 说明：部分接口参数和返回值可能根据实际代码有所不同，具体请参考后端实现文件（如 `backend/api/` 目录下的各模块）。