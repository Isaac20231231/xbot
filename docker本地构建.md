# XBot 本地 Docker 构建指南

本文档详细说明如何在本地环境中构建和运行 XBot 的 Docker 容器，包括常见问题及解决方案。

## 前提条件

- 已安装 [Docker](https://docs.docker.com/get-docker/)
- 已安装 [Docker Compose](https://docs.docker.com/compose/install/)
- 已下载/克隆 XBot 项目代码

## 一、基本构建步骤

### 1. 进入项目根目录

```bash
cd 项目根目录路径  # 例如: cd /path/to/xbot
```

### 2. 确保 entrypoint.sh 有执行权限

在环境下，需要手动赋予 entrypoint.sh 执行权限：

**方法 1: 使用 Git Bash (推荐)**

```bash
chmod +x entrypoint.sh
```

**方法 2: 使用 PowerShell**

```powershell
# 如果你有WSL
wsl chmod +x entrypoint.sh

# 或者修改文件属性
icacls entrypoint.sh /grant Everyone:RX
```

**注意:** 这一步非常重要，否则容器会因权限问题无法启动。

### 3. 构建并启动容器

```bash
docker-compose up --build
```

该命令会执行以下操作：

- 根据 Dockerfile 构建本地镜像
- 启动 docker-compose.yml 中定义的服务
- 将控制台输出绑定到当前终端

### 4. 后台运行容器 (可选)

如果你想在后台运行容器：

```bash
docker-compose up --build -d
```

## 二、挂载方式说明

目前 docker-compose.yml 中使用了两种挂载方式：

```yaml
volumes:
  - ./:/app # 将本地目录挂载到容器的/app
  - redis_data:/var/lib/redis # 使用Docker卷存储Redis数据
```

- **代码挂载 (`./:/app`)**: 将本地代码目录挂载到容器内，方便开发调试，代码修改即时生效。
- **数据卷 (`redis_data`)**: 持久化存储 Redis 数据，即使容器删除也不会丢失。

## 三、常见问题及解决方案

### 1. "permission denied" 错误

**问题描述:**

```
Error: exec: "./entrypoint.sh": permission denied
```

**解决方案:**

- 确保在主机上给 entrypoint.sh 赋予执行权限 (见上面的步骤 2)
- 这个问题在 Windows 环境下尤为常见，因为 Windows 没有 Linux 的执行权限概念

### 2. Redis 连接问题

**问题描述:**

```
Connection refused to Redis on 127.0.0.1:6379
```

**解决方案:**

- 容器内的 Redis 服务是通过 entrypoint.sh 自动启动的
- 确保没有其他程序占用 6379 端口
- 确保 redis.conf 文件存在且配置正确

### 3. 容器无法访问/修改挂载的文件

**解决方案:**

- 可能是文件权限问题，尝试在主机上修改文件权限
- 对于开发环境，可考虑放宽权限: `chmod -R 777 ./` (不推荐用于生产环境)

## 四、生产环境最佳实践

对于生产环境，我们推荐以下配置：

1. **不挂载本地代码目录**，而是将代码复制到镜像中:

   ```yaml
   # 移除此行
   # - ./:/app
   ```

2. **只挂载必要的数据目录**，如:

   ```yaml
   volumes:
     - ./data:/app/data
     - ./logs:/app/logs
     - redis_data:/var/lib/redis
   ```

3. **预构建镜像**，避免每次部署都重新构建:
   ```bash
   docker-compose build
   docker tag xbot_xbot your-registry/xbot:version
   docker push your-registry/xbot:version
   ```
   然后在 docker-compose.yml 中使用该镜像

## 五、其他有用的命令

```bash
# 查看正在运行的容器
docker ps

# 进入容器内部
docker exec -it xbot bash

# 查看容器日志
docker-compose logs -f

# 停止并移除容器
docker-compose down

# 只重启服务，不重建
docker-compose restart
```

## 六、配置说明

### Dockerfile 重点说明

XBot 的 Dockerfile 主要完成以下操作:

- 基于 Python 镜像构建
- 安装系统依赖和 Redis
- 配置时区为 Asia/Shanghai
- 复制项目文件并安装 Python 依赖
- 设置工作目录为 /app
- 将 entrypoint.sh 作为容器启动入口

### docker-compose.yml 重点说明

- 服务名: xbot
- 本地构建镜像 (build: .)
- 容器名: xbot
- 端口映射: 9090:9090 (管理后台)
- 挂载: 代码目录和 Redis 数据

## 问题反馈

如遇到任何问题，请提交 issue 或联系开发团队。
