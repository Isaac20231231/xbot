# xbot API 文档

## 1. 概述

xbot 提供了一套完整的 API 接口，允许开发者通过 HTTP 请求与系统进行交互。这些 API 接口主要通过管理后台的 Web 服务提供，使用 JSON 格式进行数据交换。本文档详细说明了可用的 API 端点、请求参数和响应格式。

## 2. 认证

所有 API 请求都需要进行认证。认证方式如下：

### 2.1 获取访问令牌

```
POST /api/auth/token
```

**请求参数：**

```json
{
  "username": "admin",
  "password": "your_password"
}
```

**响应：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2.2 使用访问令牌

在后续请求中，将访问令牌添加到请求头中：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 3. 消息相关 API

### 3.1 发送文本消息

```
POST /api/message/send_text
```

**请求参数：**

```json
{
  "target_id": "wxid_example",
  "content": "这是一条测试消息",
  "room_id": "12345678@chatroom" // 可选，如果是群消息则提供
}
```

**响应：**

```json
{
  "success": true,
  "message_id": "12345678901234567890",
  "timestamp": 1625123456
}
```

### 3.2 发送图片消息

```
POST /api/message/send_image
```

**请求参数：**

```json
{
  "target_id": "wxid_example",
  "image_path": "/path/to/image.jpg", // 服务器上的路径
  "room_id": "12345678@chatroom" // 可选
}
```

或者使用 multipart/form-data 上传图片：

```
POST /api/message/upload_and_send_image
```

**响应：**

```json
{
  "success": true,
  "message_id": "12345678901234567890",
  "timestamp": 1625123456
}
```

### 3.3 发送语音消息

```
POST /api/message/send_voice
```

**请求参数：**

```json
{
  "target_id": "wxid_example",
  "voice_path": "/path/to/voice.mp3",
  "room_id": "12345678@chatroom" // 可选
}
```

**响应：**

```json
{
  "success": true,
  "message_id": "12345678901234567890",
  "timestamp": 1625123456
}
```

### 3.4 发送视频消息

```
POST /api/message/send_video
```

**请求参数：**

```json
{
  "target_id": "wxid_example",
  "video_path": "/path/to/video.mp4",
  "room_id": "12345678@chatroom" // 可选
}
```

**响应：**

```json
{
  "success": true,
  "message_id": "12345678901234567890",
  "timestamp": 1625123456
}
```

### 3.5 发送文件

```
POST /api/message/send_file
```

**请求参数：**

```json
{
  "target_id": "wxid_example",
  "file_path": "/path/to/file.pdf",
  "room_id": "12345678@chatroom" // 可选
}
```

**响应：**

```json
{
  "success": true,
  "message_id": "12345678901234567890",
  "timestamp": 1625123456
}
```

### 3.6 获取消息历史

```
GET /api/message/history
```

**请求参数：**

```
contact_id: wxid_example 或 12345678@chatroom
limit: 50 (默认20)
offset: 0
start_time: 1625123456 (可选，Unix时间戳)
end_time: 1625123456 (可选，Unix时间戳)
```

**响应：**

```json
{
  "total": 100,
  "offset": 0,
  "limit": 50,
  "messages": [
    {
      "id": "12345678901234567890",
      "sender": "wxid_sender",
      "receiver": "wxid_receiver",
      "room_id": "12345678@chatroom",
      "content": "消息内容",
      "type": 1,
      "timestamp": 1625123456
    }
    // 更多消息...
  ]
}
```

## 4. 联系人相关 API

### 4.1 获取联系人列表

```
GET /api/contact/list
```

**请求参数：**

```
type: all|friend|group (默认all)
limit: 50 (默认20)
offset: 0
keyword: 搜索关键词 (可选)
```

**响应：**

```json
{
  "total": 100,
  "offset": 0,
  "limit": 50,
  "contacts": [
    {
      "wxid": "wxid_example",
      "nickname": "用户昵称",
      "remark": "备注名",
      "avatar": "头像URL",
      "type": "friend"
    }
    // 更多联系人...
  ]
}
```

### 4.2 获取群成员列表

```
GET /api/contact/group_members
```

**请求参数：**

```
group_id: 12345678@chatroom
```

**响应：**

```json
{
  "group_id": "12345678@chatroom",
  "group_name": "群名称",
  "member_count": 50,
  "members": [
    {
      "wxid": "wxid_example",
      "nickname": "用户昵称",
      "display_name": "群内显示名",
      "avatar": "头像URL"
    }
    // 更多成员...
  ]
}
```

### 4.3 获取联系人详情

```
GET /api/contact/detail
```

**请求参数：**

```
wxid: wxid_example 或 12345678@chatroom
```

**响应：**

```json
{
  "wxid": "wxid_example",
  "nickname": "用户昵称",
  "remark": "备注名",
  "avatar": "头像URL",
  "gender": 1, // 1=男, 2=女, 0=未知
  "signature": "个性签名",
  "region": "地区",
  "type": "friend"
}
```

## 5. 文件相关 API

### 5.1 上传文件

```
POST /api/file/upload
```

使用 multipart/form-data 格式上传文件。

**请求参数：**

```
file: 文件数据
type: image|voice|video|file (默认file)
```

**响应：**

```json
{
  "success": true,
  "file_id": "file_12345678",
  "file_path": "/uploads/file_12345678.pdf",
  "file_name": "document.pdf",
  "file_size": 1024,
  "file_type": "application/pdf"
}
```

### 5.2 获取文件列表

```
GET /api/file/list
```

**请求参数：**

```
type: all|image|voice|video|file (默认all)
limit: 50 (默认20)
offset: 0
```

**响应：**

```json
{
  "total": 100,
  "offset": 0,
  "limit": 50,
  "files": [
    {
      "file_id": "file_12345678",
      "file_path": "/uploads/file_12345678.pdf",
      "file_name": "document.pdf",
      "file_size": 1024,
      "file_type": "application/pdf",
      "upload_time": 1625123456
    }
    // 更多文件...
  ]
}
```

### 5.3 删除文件

```
DELETE /api/file/delete
```

**请求参数：**

```json
{
  "file_id": "file_12345678"
}
```

**响应：**

```json
{
  "success": true
}
```

## 6. 插件相关 API

### 6.1 获取插件列表

```
GET /api/plugin/list
```

**响应：**

```json
{
  "plugins": [
    {
      "name": "ExamplePlugin",
      "display_name": "示例插件",
      "description": "这是一个示例插件",
      "version": "1.0.0",
      "author": "开发者名称",
      "enabled": true
    }
    // 更多插件...
  ]
}
```

### 6.2 启用/禁用插件

```
POST /api/plugin/toggle
```

**请求参数：**

```json
{
  "plugin_name": "ExamplePlugin",
  "enabled": true
}
```

**响应：**

```json
{
  "success": true,
  "plugin_name": "ExamplePlugin",
  "enabled": true
}
```

### 6.3 获取插件配置

```
GET /api/plugin/config
```

**请求参数：**

```
plugin_name: ExamplePlugin
```

**响应：**

```json
{
  "plugin_name": "ExamplePlugin",
  "config": {
    "setting1": "value1",
    "setting2": 123,
    "setting3": true
  }
}
```

### 6.4 更新插件配置

```
POST /api/plugin/config
```

**请求参数：**

```json
{
  "plugin_name": "ExamplePlugin",
  "config": {
    "setting1": "new_value",
    "setting2": 456
  }
}
```

**响应：**

```json
{
  "success": true,
  "plugin_name": "ExamplePlugin"
}
```

## 7. 系统相关 API

### 7.1 获取系统状态

```
GET /api/system/status
```

**响应：**

```json
{
  "status": "running",
  "uptime": 86400, // 秒
  "memory_usage": {
    "total": 8192, // MB
    "used": 1024, // MB
    "percent": 12.5
  },
  "cpu_usage": 5.2, // 百分比
  "bot_info": {
    "wxid": "wxid_bot",
    "nickname": "机器人昵称",
    "status": "online",
    "last_active": 1625123456
  },
  "message_stats": {
    "today": 1234,
    "total": 123456
  }
}
```

### 7.2 重启系统

```
POST /api/system/restart
```

**响应：**

```json
{
  "success": true,
  "message": "系统正在重启，请稍后..."
}
```

### 7.3 获取系统日志

```
GET /api/system/logs
```

**请求参数：**

```
level: all|debug|info|warning|error (默认all)
limit: 100 (默认50)
offset: 0
start_time: 1625123456 (可选，Unix时间戳)
end_time: 1625123456 (可选，Unix时间戳)
```

**响应：**

```json
{
  "total": 1000,
  "offset": 0,
  "limit": 100,
  "logs": [
    {
      "timestamp": 1625123456,
      "level": "INFO",
      "module": "bot_core",
      "message": "系统启动成功"
    }
    // 更多日志...
  ]
}
```

## 8. 提醒相关 API

### 8.1 创建提醒

```
POST /api/reminder/create
```

**请求参数：**

```json
{
  "target_id": "wxid_example",
  "room_id": "12345678@chatroom", // 可选
  "content": "提醒内容",
  "time": "2023-12-31 23:59:59",
  "repeat_type": "none", // none, daily, weekly, monthly
  "repeat_value": "" // 对于weekly可以是"1,3,5"表示周一三五
}
```

**响应：**

```json
{
  "success": true,
  "reminder_id": "reminder_12345678"
}
```

### 8.2 获取提醒列表

```
GET /api/reminder/list
```

**请求参数：**

```
target_id: wxid_example (可选)
status: all|active|completed (默认all)
limit: 50 (默认20)
offset: 0
```

**响应：**

```json
{
  "total": 100,
  "offset": 0,
  "limit": 50,
  "reminders": [
    {
      "id": "reminder_12345678",
      "target_id": "wxid_example",
      "room_id": "12345678@chatroom",
      "content": "提醒内容",
      "time": "2023-12-31 23:59:59",
      "repeat_type": "none",
      "repeat_value": "",
      "status": "active",
      "created_at": 1625123456
    }
    // 更多提醒...
  ]
}
```

### 8.3 删除提醒

```
DELETE /api/reminder/delete
```

**请求参数：**

```json
{
  "reminder_id": "reminder_12345678"
}
```

**响应：**

```json
{
  "success": true
}
```

## 9. 积分相关 API

### 9.1 获取用户积分

```
GET /api/points/user
```

**请求参数：**

```
wxid: wxid_example
```

**响应：**

```json
{
  "wxid": "wxid_example",
  "nickname": "用户昵称",
  "points": 1000,
  "rank": 5,
  "sign_in_days": 7,
  "last_sign_in": "2023-06-01"
}
```

### 9.2 获取积分排行榜

```
GET /api/points/leaderboard
```

**请求参数：**

```
limit: 50 (默认20)
offset: 0
```

**响应：**

```json
{
  "total": 100,
  "offset": 0,
  "limit": 50,
  "leaderboard": [
    {
      "rank": 1,
      "wxid": "wxid_example1",
      "nickname": "用户1",
      "points": 2000
    },
    {
      "rank": 2,
      "wxid": "wxid_example2",
      "nickname": "用户2",
      "points": 1800
    }
    // 更多用户...
  ]
}
```

### 9.3 调整用户积分

```
POST /api/points/adjust
```

**请求参数：**

```json
{
  "wxid": "wxid_example",
  "points": 100, // 正数为增加，负数为减少
  "reason": "管理员奖励"
}
```

**响应：**

```json
{
  "success": true,
  "wxid": "wxid_example",
  "points_before": 1000,
  "points_after": 1100,
  "points_change": 100
}
```

## 10. 错误处理

所有 API 在发生错误时会返回相应的 HTTP 状态码和错误信息：

```json
{
  "error": true,
  "code": "UNAUTHORIZED",
  "message": "认证失败，请重新登录"
}
```

常见错误码：

| HTTP 状态码 | 错误码            | 描述             |
| ----------- | ----------------- | ---------------- |
| 400         | BAD_REQUEST       | 请求参数错误     |
| 401         | UNAUTHORIZED      | 未认证或认证失败 |
| 403         | FORBIDDEN         | 权限不足         |
| 404         | NOT_FOUND         | 资源不存在       |
| 429         | TOO_MANY_REQUESTS | 请求过于频繁     |
| 500         | INTERNAL_ERROR    | 服务器内部错误   |

## 11. 使用示例

### 11.1 Python 示例

```python
import requests
import json

# 认证
def get_token(base_url, username, password):
    url = f"{base_url}/api/auth/token"
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=data)
    return response.json()["access_token"]

# 发送消息
def send_message(base_url, token, target_id, content, room_id=None):
    url = f"{base_url}/api/message/send_text"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "target_id": target_id,
        "content": content
    }
    if room_id:
        data["room_id"] = room_id

    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 使用示例
if __name__ == "__main__":
    base_url = "http://localhost:9090"
    token = get_token(base_url, "admin", "admin123")

    # 发送私聊消息
    result = send_message(base_url, token, "wxid_example", "你好，这是一条测试消息")
    print(json.dumps(result, indent=2))

    # 发送群聊消息
    result = send_message(base_url, token, "wxid_example", "大家好，这是一条测试消息", "12345678@chatroom")
    print(json.dumps(result, indent=2))
```

### 11.2 JavaScript 示例

```javascript
// 认证
async function getToken(baseUrl, username, password) {
  const response = await fetch(`${baseUrl}/api/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      password,
    }),
  });

  const data = await response.json();
  return data.access_token;
}

// 发送消息
async function sendMessage(baseUrl, token, targetId, content, roomId = null) {
  const url = `${baseUrl}/api/message/send_text`;
  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const data = {
    target_id: targetId,
    content,
  };

  if (roomId) {
    data.room_id = roomId;
  }

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });

  return response.json();
}

// 使用示例
(async () => {
  const baseUrl = "http://localhost:9090";
  const token = await getToken(baseUrl, "admin", "admin123");

  // 发送私聊消息
  const result1 = await sendMessage(
    baseUrl,
    token,
    "wxid_example",
    "你好，这是一条测试消息"
  );
  console.log(JSON.stringify(result1, null, 2));

  // 发送群聊消息
  const result2 = await sendMessage(
    baseUrl,
    token,
    "wxid_example",
    "大家好，这是一条测试消息",
    "12345678@chatroom"
  );
  console.log(JSON.stringify(result2, null, 2));
})();
```

## 12. API 限制

- 请求频率限制：每个 IP 每分钟最多 60 次请求
- 上传文件大小限制：图片最大 10MB，语音最大 2MB，视频最大 50MB，其他文件最大 100MB
- 消息内容长度限制：文本消息最大 2000 字符

## 13. 注意事项

1. 所有 API 请求都需要通过 HTTPS 进行（生产环境）
2. 访问令牌有效期为 1 小时，过期后需要重新获取
3. 敏感操作（如发送消息、管理联系人）需要管理员权限
4. 请合理控制请求频率，避免触发限流措施
5. 文件上传后会在服务器保留一段时间，系统会定期清理长期未使用的文件

## 14. 更新日志

### v1.0.0 (2023-06-01)

- 初始版本发布
- 支持基本的消息、联系人、文件和系统管理 API

### v1.1.0 (2023-07-15)

- 添加提醒相关 API
- 添加积分相关 API
- 改进认证机制，增加令牌刷新功能

### v1.2.0 (2023-09-01)

- 添加插件管理 API
- 优化文件上传和下载功能
- 增加批量操作支持
