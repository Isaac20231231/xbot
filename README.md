# 🤖 xbot 机器人项目 🤖

> ## ⚠️ 免责声明
>
> **本项目仅供学习交流使用，严禁用于商业用途！**
> 使用本项目所产生的一切法律责任和风险，由使用者自行承担，与项目作者无关。
> 请遵守相关法律法规，合法合规使用本项目。

## 📝 项目概述

xbot 是一个智能机器人系统，提供了丰富的交互体验。
本项目只用于学习交流，不在提供 wechat 协议。可自行拓展接入微信企业官方机器人，钉钉，飞书等机器人。

## 📚 项目文档

- [**系统架构文档**](docs/系统架构文档.md) - 系统组件和架构详解
- [**插件开发指南**](docs/插件开发指南.md) - 如何开发自定义插件
- [**配置指南**](docs/配置指南.md) - 系统配置详细说明
- [**用户手册**](docs/用户手册.md) - 用户使用指南
- [**API 文档**](docs/API文档.md) - 系统 API 接口文档

### 🔄 双协议支持与框架模式

本系统现已支持多种微信协议：

#### 协议版本支持

- **pad 协议**
- **ipad 协议**
- **mac 协议**

#### 框架模式支持

- **wechat**：

通过在 `main_config.toml` 文件中设置 `Protocol.version` 和 `Framework.type` 参数，系统会自动选择相应的服务和 API 路径。详细配置方法请参见[协议配置](#协议配置)部分。

选择不同的协议版本和框架模式，可以满足不同用户的需求，提供更灵活的交互体验。

#### 🔧 协议配置

在 `main_config.toml` 文件中，配置 `Protocol.version` 和 `Framework.type` 参数来选择协议版本和框架模式：

```toml
[Protocol]
version = "ipad"  # 可选值：pad, ipad, Mac
```

## 🚀 快速开始

<table>
  <tr>
    <td width="50%">
      <h3>💬 加入 xbot 交流群</h3>
      <p>扫描右侧的二维码加入官方交流群，获取：</p>
      <ul>
        <li>💡 <strong>最新功能更新</strong>和使用技巧</li>
        <li>👨‍💻 <strong>技术支持</strong>和问题解答</li>
        <li>👥 与其他用户<strong>交流经验</strong></li>
        <li>📝 <strong>插件开发</strong>和定制化帮助</li>
      </ul>
    </td>
    <td width="25%" align="center">
      <img src="https://github.com/user-attachments/assets/39f6eff3-bcaa-4bdf-87f2-fd887c26a4e7" alt="关注公众号进群" width="220">
      <p><strong>xbot 交流群</strong></p>
    </td>
  </tr>
</table>

## ✨ 主要特性

### 1. 💻 管理后台

- 📊 **控制面板**：系统概览、机器人状态监控
- 🔌 **插件管理**：安装、配置、启用/禁用各类功能插件
- 📁 **文件管理**：上传、查看和管理机器人使用的文件
- 📵 **联系人管理**：微信好友和群组联系人管理
- 📈 **系统状态**：查看系统资源占用和运行状态

### 2. 💬 聊天功能

- 📲 **私聊互动**：与单个用户的一对一对话
- 👥 **群聊响应**：在群组中通过@或特定命令触发
- 📞 **聊天室模式**：支持多人持续对话，带有用户状态管理
- 💰 **积分系统**：对话消耗积分，支持不同模型不同积分定价
- 📸 **朋友圈功能**：支持查看、点赞和评论朋友圈

### 3. 🤖 智能对话

- 🔍 **多模型支持**：可配置多种 AI 模型，支持通过关键词切换
- 📷 **图文结合**：支持图片理解和多媒体输出
- 🖼️ **[引用图片识别](引用图片识别功能说明.md)**：通过引用图片消息让 AI 分析图片内容
- 🎤 **语音交互**：支持语音输入识别和语音回复
- 😍 **语音撒娇**：支持甜美语音撒娇功能

### 4. 🔗 插件系统

- 🔌 **插件管理**：支持加载、卸载和重载插件
- 🔧 **自定义插件**：可开发和加载自定义功能插件
- 🤖 **Dify 插件**：集成 Dify API，提供高级 AI 对话能力
- ⏰ **定时提醒**：支持设置定时提醒和日程管理
- 👋 **群欢迎**：自动欢迎新成员加入群聊
- 🌅 **早安问候**：每日早安问候功能

## 📍 安装指南

### 📦 系统要求

- 🐍 Python 3.11+
- 📱 WX 客户端
- 🔋 Redis（用于数据缓存）
- 🎥 FFmpeg（用于语音处理）
- 🐳 Docker（可选，用于容器化部署）

### 📝 安装步骤

#### 🔹 方法一：直接安装

1. **克隆代码库**

   ```bash
   git clone https://github.com/NanSsye/xbot.git
   cd xbot
   ```

2. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

3. **安装 Redis**

   - Windows: 下载 Redis for Windows
   - Linux: `sudo apt-get install redis-server`
   - macOS: `brew install redis`

4. **安装 FFmpeg**

   - Windows: 下载安装包并添加到系统 PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

5. **配置**

   - 复制 `main_config.toml.example` 为 `main_config.toml` 并填写配置
   - 设置管理员 ID 和其他基本参数

   **设置管理员：**

   在 `main_config.toml` 文件中的 `[XYBot]` 部分设置管理员：

   ```toml
   [XYBot]
   # 管理员微信ID，可以设置多个，用英文逗号分隔
   admins = ["wxid_l2221111", "wxid_l111111"]  # 管理员的wxid列表，可从消息日志中获取
   ```

   **设置 GitHub 加速代理：**

   在 `main_config.toml` 文件中的 `[XYBot]` 部分设置 GitHub 加速代理：

   ```toml
   [XYBot]
   # GitHub加速服务设置
   # 可选值: "", "https://ghfast.top/", "https://gh-proxy.com/", "https://mirror.ghproxy.com/"
   # 空字符串表示直连不使用加速
   # 注意: 如果使用加速服务，请确保以"/"结尾
   github-proxy = "https://ghfast.top/"
   ```

   **设置系统通知功能：**

   在 `main_config.toml` 文件中配置系统通知功能（微信离线、重连、重启等通知）：

   ```toml
   # 系统通知设置
   [Notification]
   enabled = true                      # 是否启用通知功能
   token = "your_pushplus_token"       # PushPlus Token，必须在这里设置！
   channel = "wechat"                  # 通知渠道：wechat(微信公众号)、sms(短信)、mail(邮件)、webhook、cp(企业微信)
   template = "html"                   # 通知模板
   topic = ""                          # 群组编码，不填仅发送给自己

   # 通知触发条件
   [Notification.triggers]
   offline = true                      # 微信离线时通知
   reconnect = true                    # 微信重新连接时通知
   restart = true                      # 系统重启时通知
   error = true                        # 系统错误时通知

   # 通知模板设置
   [Notification.templates]
   offlineTitle = "警告：微信离线通知 - {time}"  # 离线通知标题
   offlineContent = "您的微信账号 <b>{wxid}</b> 已于 <span style=\"color:#ff4757;font-weight:bold;\">{time}</span> 离线，请尽快检查您的设备连接状态或重新登录。"  # 离线通知内容
   reconnectTitle = "微信重新连接通知 - {time}"  # 重连通知标题
   reconnectContent = "您的微信账号 <b>{wxid}</b> 已于 <span style=\"color:#2ed573;font-weight:bold;\">{time}</span> 重新连接。"  # 重连通知内容
   restartTitle = "系统重启通知 - {time}"  # 系统重启通知标题
   restartContent = "系统已于 <span style=\"color:#1e90ff;font-weight:bold;\">{time}</span> 重新启动。"  # 系统重启通知内容
   ```

   ❗ **重要提示：**

   - PushPlus Token 必须在 `main_config.toml` 文件中直接设置，而不是通过网页界面设置
   - 如果通过网页界面设置，可能会导致容器无法正常启动
   - 请先在 [PushPlus 官网](http://www.pushplus.plus/) 注册并获取 Token

   <h3 id="协议配置">协议配置</h3>

   在 `main_config.toml` 文件中添加以下配置来选择微信协议版本：

   ```toml
   [Protocol]
   version = "ipad"  # 可选值：pad, ipad, Mac
   ```

- **pad 协议**
- **ipad 协议**
- **mac**

系统会根据配置的协议版本自动选择正确的服务路径和 API 路径前缀。

   <h3 id="框架配置">框架配置</h3>

在 `main_config.toml` 文件中添加以下配置来选择框架模式：

```toml
[Framework]
type = "wechat"
```

6. **启动必要的服务**

   **需要先启动 Redis 和 PAD 服务**（注意启动顺序！）：

   ### 🏠 Windows 用户

   - ❗ **第一步**：启动 Redis 服务 🔋

     - 进入 `redis` 目录，双击 `redis-server.exe` 文件
     - 等待窗口显示 Redis 启动成功

   - ❗ **第二步**：启动 PAD 服务 📱

     - 根据你的协议版本选择相应的服务：
       - 直接启动 docker 容器：xbot-wechat
       - 映射 9011 和 9088 两个端口

   - ⚠️ 请确保这两个服务窗口始终保持打开状态，不要关闭它们！

     **然后启动主服务**：

   ```bash
   python main.py
   ```

   ### 💻 Linux 用户

   - ❗ **第一步**：启动 Redis 服务 🔋

     ```bash
     # 进入Redis目录
     cd redis

     # 使用Linux配置文件启动Redis
     redis-server redis.linux.conf
     ```

     - 如果 Redis 未安装，需要先安装：

     ```bash
     # Ubuntu/Debian
     sudo apt-get update
     sudo apt-get install redis-server

     # CentOS/RHEL
     sudo yum install redis
     ```

   - ❗ **第二步**：启动 PAD 服务 📱

     根据你的协议版本选择相应的服务：

     - 直接启动 docker 容器：xbot-wechat
     - 映射 9011 和 9088 两个端口

   - ⚠️ 请确保这两个服务进程保持运行状态，可以使用如下命令检查：

     ```bash
     # 检查Redis服务
     ps aux | grep redis

     ```

   **然后启动主服务**：

   ```bash
   python main.py
   ```

#### 🔺 方法二：Docker 安装 🐳

1. **使用 Docker Compose 一键部署**

   ```bash
   # 克隆代码库
   git clone https://github.com/NanSsye/xbot.git
   cd xbot

   # 启动服务
   docker-compose up -d
   ```

   这将自动拉取最新的镜像并启动服务，所有数据将保存在 Docker 卷中。

2. **更新到最新版本**

   替换群里的框架压缩包到容器中（xbot）

3. **启动协议容器**

下载容器 xbot-wechat
映射端口 9011 和 9088

#### WechatAPIServer 配置设置

```bash
# 克隆代码库
[WechatAPIServer]
host = "127.0.0.1"      # WechatAPI服务器地址，为xbot-wechat所在主机的ip地址
port = 9011                # WechatAPI服务器端口，默认9011
mode = "release"           # 运行模式：release(生产环境)，debug(调试模式)
redis-host = "127.0.0.1"   # Redis服务器地址，本地使用127.0.0.1
redis-port = 6379          # Redis端口，使用系统Redis服务的默认端口
redis-password = ""        # Redis密码，如果有设置密码则填写
redis-db = 0               # Redis数据库编号，默认0
ws-url = "ws://127.0.0.1:9088/ws"  #为xbot-wechat所在主机ip+9088端口
message-mode = "ws"        # 可选 ws 或 http，决定消息读取方式
```

### 🔍 访问后台

- 🌐 打开浏览器访问 `http://localhost:9090` 进入管理界面
- 👤 默认用户名：`admin`
- 🔑 默认密码：`admin1234`

### 🤖 Dify 插件配置

```toml
[Dify]
enable = true
default-model = "model1"
command-tip = true
commands = ["ai", "机器人", "gpt"]
admin_ignore = true
whitelist_ignore = true
http-proxy = ""
voice_reply_all = false
robot-names = ["机器人", "小助手"]
remember_user_model = true
chatroom_enable = true

[Dify.models.model1]
api-key = "your_api_key"
base-url = "https://api.dify.ai/v1"
trigger-words = ["dify", "小d"]
price = 10
wakeup-words = ["你好小d", "嘿小d"]
```

## 📖 使用指南

详细使用指南请参考[用户手册](docs/用户手册.md)。

## 🔌 插件开发

想要开发自己的插件？请参考[插件开发指南](docs/插件开发指南.md)了解详细信息。

## 🔴 常见问题

1. **安装依赖失败** 💻

   - 尝试使用 `pip install --upgrade pip` 更新 pip
   - 可能需要安装开发工具: `apt-get install python3-dev`

2. **语音识别失败** 🎤

   - 确认 FFmpeg 已正确安装并添加到 PATH
   - 检查 SpeechRecognition 依赖是否正确安装

3. **无法连接微信** 📱

   - 确认微信客户端和接口版本是否匹配
   - 检查网络连接和端口设置
   - 如果使用 PAD 协议，确认 PAD 服务是否正常运行
   - ⚠️ Windows 用户请确认是否按正确顺序启动服务：先启动 Redis，再启动 PAD
   - 检查 `main_config.toml` 中的协议版本设置是否正确（849 用于 iPad，855 用于安卓 PAD）

4. **Redis 连接错误** 🔋

   - 确认 Redis 服务器是否正常运行
   - 🔴 Windows 用户请确认是否已启动 `849/redis` 目录中的 `redis-server.exe`
   - 检查 Redis 端口和访问权限设置
   - 确认配置文件中的 Redis 端口是否为 6378
   - 💡 提示：Redis 窗口应显示"已就绪接受指令"或类似信息

5. **Dify API 错误** 🤖

   - 验证 API 密钥是否正确
   - 确认 API URL 格式和访问权限

6. **Docker 部署问题** 🐳

   - 确认 Docker 容器是否正常运行：`docker ps`
   - 查看容器日志：`docker logs xbot`
   - 重启容器：`docker-compose restart`
   - 查看卷数据：`docker volume ls`
   - 💡 注意：Docker 容器内会自动启动 PAD 和 Redis 服务，无需手动启动
   - 如果需要切换协议版本，只需修改 `main_config.toml` 中的 `Protocol.version` 设置并重启容器
   - ⚠️ Windows 用户注意：Docker 容器使用的是 Linux 环境，不能直接使用 Windows 版的可执行文件

7. **无法访问管理后台** 🛑

   - 确认服务器正常运行在 9090 端口
   - 尝试使用默认账号密码: admin/admin1234
   - 检查防火墙设置是否阻止了端口访问

## 🏗️ 技术架构

详细架构信息请参考[系统架构文档](docs/系统架构文档.md)。

## 📜 协议和许可

本项目基于 [MIT 许可证](LICENSE) 开源，您可以自由使用、修改和分发本项目的代码，但需保留原始版权声明。

### ⚠️ 重要免责声明

- **本项目仅供学习和研究使用，严禁用于任何商业用途**
- **使用前请确保符合微信和相关服务的使用条款**
- **使用本项目所产生的一切法律责任和风险，由使用者自行承担，与项目作者无关**
- **请遵守相关法律法规，合法合规使用本项目**
- **如果您使用了本项目，即表示您已阅读并同意上述免责声明**

## 🙏 鸣谢

本项目的开发离不开以下作者和项目的支持与贡献：

<table style="border-collapse: collapse; border: none;">
  <tr style="border: none;">
    <td width="180" align="center" style="border: none; padding: 10px;">
      <div style="border-radius: 50%; overflow: hidden; width: 120px; height: 120px; margin: 0 auto;">
        <img src="https://avatars.githubusercontent.com/u/83214045" width="120" height="120">
      </div>
      <br>
      <strong style="font-size: 16px;">HenryXiaoYang</strong>
      <br>
      <a href="https://github.com/HenryXiaoYang" style="text-decoration: none; color: #0366d6;">个人主页</a>
    </td>
    <td style="border: none; padding: 10px;">
      <p style="margin-bottom: 8px; font-size: 15px;">项目：<a href="https://github.com/HenryXiaoYang/XYBotV2" style="text-decoration: none; color: #0366d6;">XYBotV2</a> - 本项目的重要参考源</p>
      <p style="margin-top: 0; font-size: 15px;">提供了微信机器人的基础架构和核心功能，为本项目的开发提供了宝贵的参考。</p>
    </td>
  </tr>
  <tr style="border: none;">
    <td width="180" align="center" style="border: none; padding: 10px;">
      <div style="border-radius: 50%; overflow: hidden; width: 120px; height: 120px; margin: 0 auto;">
        <img src="https://avatars.githubusercontent.com/u/178422005" width="120" height="120">
      </div>
      <br>
      <strong style="font-size: 16px;">heaven2028</strong>
      <br>
      <a href="https://github.com/heaven2028" style="text-decoration: none; color: #0366d6;">个人主页</a>
    </td>
    <td style="border: none; padding: 10px;">
      <p style="margin-bottom: 8px; font-size: 15px;">与本项目作者共同完成的开发工作</p>
      <p style="margin-top: 0; font-size: 15px;">在功能扩展、界面设计和系统优化方面做出了重要贡献。</p>
    </td>
  </tr>
</table>

同时感谢所有其他贡献者和使用的开源项目。

## 📞 联系方式

- **GitHub**: [https://github.com/NanSsye](https://github.com/NanSsye)
- **官方交流群**：请查看上方[快速开始](#快速开始)部分的二维码

## 💻 管理后台界面展示

<table>
  <tr>
    <td width="50%" align="center">
      <img src="https://github.com/user-attachments/assets/2f716d30-07df-4e50-8b2d-d18371a7b4ed" width="400">
    </td>
    <td width="50%" align="center">
      <img src="https://github.com/user-attachments/assets/50bc4c43-930b-4332-ad07-aaeb432af37f" width="400">
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="https://github.com/user-attachments/assets/a60c5ce4-bae4-4eed-82a6-e9f0f8189b84" width="400">
    </td>
    <td width="50%" align="center">
      <img src="https://github.com/user-attachments/assets/5aaa5450-7c13-43a1-9310-471af304408d" width="400">
    </td>
  </tr>
</table>

# 已还原为同步消息处理方式，无需 Celery 和 Redis 队列，消息由主循环直接分发处理。
