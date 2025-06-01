# XBot 授权验证系统

本文档介绍了 XBot 授权验证系统的工作原理、部署方法和使用说明。

## 1. 系统概述

XBot 授权验证系统由两部分组成：

1. **客户端验证模块**：集成在 XBot 中，启动时进行授权验证
2. **授权服务器**：独立部署的 Flask 应用，负责授权管理和验证

### 工作流程：

1. 首次启动 XBot 时，系统会自动向授权服务器请求一个唯一的授权码。
2. 授权服务器根据机器码生成授权，并返回授权信息。
3. XBot 将授权信息保存在本地文件中（license.json）。
4. 下次启动时，XBot 会读取本地授权信息，并向服务器验证其有效性。
5. 如果验证通过，XBot 正常启动；否则，程序退出。

## 2. 部署授权服务器

### 2.1 安装依赖

```bash
pip install flask flask-cors werkzeug
```

### 2.2 启动服务器

```bash
python license_server.py
```

服务器默认在 5000 端口运行。你可以通过修改配置文件（`license_data/config.json`）来更改端口。

### 2.3 配置说明

首次启动服务器会在 `license_data` 目录下生成以下文件：

- `config.json`: 服务器配置
- `admin.json`: 管理员账号信息
- `licenses.json`: 所有授权信息

默认的管理员账号为：`admin/admin123`

### 2.4 服务器配置项

| 配置项               | 说明                   | 默认值 |
| -------------------- | ---------------------- | ------ |
| `license_valid_days` | 授权有效期（天）       | 365    |
| `automatic_approval` | 是否自动批准新授权     | true   |
| `blacklist`          | 机器 ID 黑名单         | []     |
| `whitelist`          | 机器 ID 白名单         | []     |
| `max_activations`    | 每个授权码最大激活次数 | 3      |
| `server_port`        | 服务器端口             | 5000   |

## 3. 客户端配置

在 XBot 的 `main.py` 中，已添加授权验证逻辑。你需要修改以下内容：

1. 更新 `license_server_url` 为你的授权服务器地址：

```python
verifier = LicenseVerifier(license_server_url="https://your-server.com")
```

改为：

```python
verifier = LicenseVerifier(license_server_url="http://your-actual-server:5000")
```

## 4. 授权管理

### 4.1 Web 界面

访问授权服务器的根路径（如 `http://localhost:5000`）可以查看 API 文档。

### 4.2 API 端点

| 端点                                | 方法 | 说明           |
| ----------------------------------- | ---- | -------------- |
| `/api/license/new`                  | POST | 请求新的授权   |
| `/api/license/verify`               | POST | 验证授权       |
| `/api/admin/login`                  | POST | 管理员登录     |
| `/api/admin/licenses`               | GET  | 获取所有授权   |
| `/api/admin/licenses/{license_key}` | PUT  | 更新授权状态   |
| `/api/admin/config`                 | GET  | 获取服务器配置 |
| `/api/admin/config`                 | PUT  | 更新服务器配置 |

### 4.3 管理授权

你可以通过以下方式管理授权：

1. **禁用特定授权**：

   ```
   PUT /api/admin/licenses/{license_key}
   {"status": "revoked"}
   ```

2. **添加机器到黑名单**：

   ```
   PUT /api/admin/config
   {"blacklist": ["machine_id1", "machine_id2"]}
   ```

3. **修改授权有效期**：
   ```
   PUT /api/admin/config
   {"license_valid_days": 30}
   ```

## 5. 安全建议

1. **更改默认管理员密码**：首次部署后立即修改默认密码。
2. **使用 HTTPS**：在生产环境中，建议使用 HTTPS 保护授权服务器。
3. **访问控制**：限制授权服务器的访问范围，可以考虑使用防火墙或反向代理。
4. **备份授权数据**：定期备份 `license_data` 目录下的文件。
5. **日志监控**：添加日志记录和监控，及时发现异常活动。

## 6. 常见问题

### 6.1 "无法连接授权服务器"

- 检查服务器是否正常运行
- 检查网络连接和防火墙设置
- 确认 `license_server_url` 配置正确

### 6.2 "授权验证失败"

- 检查授权是否过期
- 查看授权状态是否被管理员修改
- 确认机器码是否被列入黑名单

### 6.3 "达到最大激活次数"

默认情况下，每个授权最多可以在 3 台不同的机器上激活。如需增加，请修改服务器配置的 `max_activations` 值。

## 7. 进阶定制

本授权系统设计为模块化，你可以根据需要扩展功能：

1. **添加更多验证维度**：如网络 MAC 地址、硬盘序列号等。
2. **实现更复杂的授权策略**：如按功能模块授权、按使用时间计费等。
3. **增强安全性**：添加授权加密、动态校验等机制。
4. **开发管理界面**：为授权管理添加完整的 Web 界面。

---

如有其他问题，请联系技术支持。
