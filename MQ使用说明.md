# 消息队列(MQ)监听功能使用说明

## 功能概述

本项目已成功集成消息队列监听功能，可以通过RabbitMQ接收外部系统发送的消息，并自动转发到微信。

## 配置说明

### 1. 修改配置文件

在 `main_config.toml` 中已添加了MessageQueue配置段：

```toml
# 消息队列设置
[MessageQueue]
enabled = true                      # 是否启用消息队列监听功能
host = "localhost"                  # RabbitMQ服务器地址
port = 5672                         # RabbitMQ服务器端口
queue = "message_queue"             # 队列名称
username = "guest"                  # RabbitMQ用户名
password = "guest"                  # RabbitMQ密码
```

### 2. 安装依赖

确保已安装pika依赖：

```bash
pip install pika>=1.3.0
```

或者重新安装所有依赖：

```bash
pip install -r requirements.txt
```

## 消息格式

向RabbitMQ队列发送的消息需要遵循以下JSON格式：

```json
[
  {
    "receiver_name": ["用户名或@的用户"],
    "message": "消息内容",
    "group_name": ["群聊名称"],
    "time": "2025-01-15 10:30:00"
  }
]
```

### 字段说明

- `receiver_name`: 接收者名称列表
  - 群聊消息：要@的用户名列表，空数组表示不@任何人
  - 私聊消息：目标用户名列表
  - 特殊值：`["所有人"]` 或 `["全体成员"]` 表示@全体成员
- `message`: 消息内容，支持文本和图片URL
- `group_name`: 群聊名称列表，空数组表示发送私聊消息
- `time`: 消息时间戳

## 支持的消息类型

### 1. 群聊普通消息
```json
{
  "receiver_name": [],
  "message": "这是一条群聊消息",
  "group_name": ["测试群"],
  "time": "2025-01-15 10:30:00"
}
```

### 2. 群聊@消息
```json
{
  "receiver_name": ["张三", "李四"],
  "message": "请注意这条消息",
  "group_name": ["测试群"],
  "time": "2025-01-15 10:30:00"
}
```

### 3. 群聊@全体成员
```json
{
  "receiver_name": ["所有人"],
  "message": "重要通知：会议即将开始",
  "group_name": ["测试群"],
  "time": "2025-01-15 10:30:00"
}
```

### 4. 私聊消息
```json
{
  "receiver_name": ["张三"],
  "message": "这是一条私聊消息",
  "group_name": [],
  "time": "2025-01-15 10:30:00"
}
```

### 5. 图片消息
```json
{
  "receiver_name": [],
  "message": "https://example.com/image.jpg",
  "group_name": ["测试群"],
  "time": "2025-01-15 10:30:00"
}
```

## 测试功能

项目提供了 `test_mq_sender.py` 测试脚本，可以用来验证MQ功能是否正常工作。

### 使用方法

1. **发送群聊消息**
```bash
python test_mq_sender.py --group "测试群" --message "测试消息"
```

2. **发送私聊消息**
```bash
python test_mq_sender.py --user "好友名" --message "测试消息"
```

3. **发送@消息**
```bash
python test_mq_sender.py --group "测试群" --at "用户名" --message "测试@消息"
```

4. **发送@全体成员**
```bash
python test_mq_sender.py --group "测试群" --atall --message "重要通知"
```

5. **发送图片**
```bash
python test_mq_sender.py --group "测试群" --image "https://example.com/image.jpg"
```

## 启动说明

1. **确保RabbitMQ服务正在运行**
   ```bash
   # Ubuntu/Debian
   sudo systemctl start rabbitmq-server
   
   # CentOS/RHEL
   sudo systemctl start rabbitmq-server
   
   # macOS (使用Homebrew)
   brew services start rabbitmq
   
   # Windows
   rabbitmq-service start
   ```

2. **启动主程序**
   ```bash
   python main.py
   ```

3. **查看日志确认MQ监听器是否启动成功**
   ```
   [INFO] 🔧 启动消息队列监听器...
   [SUCCESS] ✅ MQ监听器已启动: localhost:5672
   [INFO] 📨 监听队列: message_queue
   ```

## 故障排除

### 1. MQ监听器启动失败
- 检查RabbitMQ服务是否正常运行
- 验证配置文件中的连接参数是否正确
- 确认防火墙没有阻止连接

### 2. 消息发送失败
- 检查联系人数据库是否包含目标联系人
- 验证群聊名称和用户名称是否正确
- 查看日志获取详细错误信息

### 3. 图片发送失败
- 确认图片URL可访问
- 检查网络连接
- 如果图片发送失败，系统会自动回退到文本方式发送URL

## 日志查看

MQ监听器的详细日志记录在以下位置：
- 控制台输出：实时查看运行状态
- 文件日志：`logs/xbot_*.log`
- MQ专用日志：`mq_listener.log`

## 高级功能

### 1. 缓存机制
- 系统会自动缓存联系人信息，缓存有效期1小时
- 支持按需刷新缓存
- 优先从好友列表查找，找不到再从群成员列表查找

### 2. 重试机制
- 消息发送失败会自动重试，最多3次
- 使用指数退避策略，避免频繁重试
- RabbitMQ连接断开会自动重连

### 3. 性能优化
- 支持异步消息处理
- 批量处理多条消息
- 智能缓存管理，减少数据库查询

## 注意事项

1. 确保微信客户端处于登录状态
2. 联系人名称需要与数据库中的昵称或备注匹配
3. 群聊名称需要与数据库中的群名称精确匹配
4. 图片URL需要可公开访问
5. 消息发送频率不宜过高，避免触发微信风控

## 扩展开发

如需自定义消息处理逻辑，可以修改 `mq_listener.py` 中的相关方法：

- `WXAdapter.process_message()`: 消息处理主逻辑
- `WXAdapter.send_message()`: 文本消息发送
- `WXAdapter.send_image_url()`: 图片消息发送
- `WXAdapter.send_at_all()`: @全体成员消息发送 