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

在 Windows 环境下，需要手动赋予 entrypoint.sh 执行权限：

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

## 五、Linux 平台构建指南

Linux 平台是 Docker 的原生环境，构建过程通常比 Windows 更顺畅。

### 1. 安装 Docker 和 Docker Compose

**Ubuntu/Debian:**

```bash
# 安装 Docker
sudo apt update
sudo apt install docker.io

# 安装 Docker Compose
sudo apt install docker-compose

# 将当前用户加入 docker 组（避免每次都需要 sudo）
sudo usermod -aG docker $USER
# 需要重新登录才能生效
```

**CentOS/RHEL:**

```bash
# 安装 Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户加入 docker 组
sudo usermod -aG docker $USER
# 需要重新登录才能生效
```

### 2. 设置文件权限

在 Linux 平台，设置文件权限更为直观：

```bash
# 只给 entrypoint.sh 添加执行权限
chmod +x entrypoint.sh

# 或者，如果需要给所有脚本添加执行权限
find . -name "*.sh" -exec chmod +x {} \;
```

### 3. 其他 Linux 特有优化

1. **设置内核参数**：对于高负载场景，可以调整以下参数：

   ```bash
   # 在 /etc/sysctl.conf 中添加
   net.core.somaxconn=4096
   vm.max_map_count=262144
   ```

   然后执行 `sudo sysctl -p` 使设置生效

2. **清理 Docker 资源**：

   ```bash
   # 删除所有停止的容器
   docker container prune -f

   # 清理未使用的镜像
   docker image prune -f

   # 清理未使用的卷
   docker volume prune -f
   ```

## 六、macOS 平台构建指南

macOS 平台使用 Docker Desktop 提供 Docker 环境。

### 1. 安装 Docker Desktop

1. 下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. 启动 Docker Desktop 应用程序
3. 等待 Docker 引擎完全启动（状态栏图标变为静态）

### 2. 性能优化

macOS 上的 Docker 使用虚拟化技术，可能存在性能问题，可以通过以下设置优化：

1. **增加资源分配**：

   - 打开 Docker Desktop
   - 点击右上角齿轮图标进入设置
   - 在 "Resources" 中，根据你的电脑配置增加 CPU、内存和交换空间的分配

2. **优化文件挂载性能**：
   - 对于 Intel Mac：在 Docker Desktop 设置的 "File sharing" 部分，只添加必要的目录
   - 对于 M1/M2 Mac：使用 VirtioFS（在 Docker Desktop 设置的 "Experimental features" 中启用）

### 3. 文件权限设置

macOS 与 Linux 类似，可以直接使用命令行设置权限：

```bash
# 设置 entrypoint.sh 执行权限
chmod +x entrypoint.sh

# 如果有多个脚本文件需要执行权限
find . -name "*.sh" -type f -exec chmod +x {} \;
```

### 4. Mac 特有问题处理

1. **时区问题**：Mac 上的 Docker 容器可能会遇到时区不同步问题

   ```yaml
   # 在 docker-compose.yml 中添加环境变量
   environment:
     - TZ=Asia/Shanghai
   ```

2. **文件系统大小写敏感问题**：macOS 默认文件系统大小写不敏感，可能导致问题
   ```bash
   # 检查是否有文件名大小写冲突
   find . -type f | grep -i [文件名] | sort
   ```

## 七、其他有用的命令

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

## 八、配置说明

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
