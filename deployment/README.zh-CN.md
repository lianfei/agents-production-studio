# 生产部署说明（轻量版）

本目录提供一套适合中小规模部署的推荐模板：

- `env/agents-studio.env.example`
- `systemd/agents-studio.service`
- `nginx/agents-studio.conf`
- `docker/Dockerfile`
- `docker/compose.yaml`
- `scripts/start.sh`
- `scripts/package_release.sh`

推荐优先级：

1. 本地 Python 先跑通
2. 服务器上使用 `systemd + nginx`
3. 需要容器时再使用 Docker

## 一、推荐目录结构

```text
/opt/agents-production-studio/        应用目录
/opt/agents-production-studio/.venv/  Python 虚拟环境
/var/lib/agents-production-studio/    输出目录
/etc/agents-studio/agents-studio.env  环境变量文件
```

## 二、服务器部署步骤

### 1. 上传代码或解压发版包

将发版包放到：

```text
/opt/agents-production-studio
```

### 2. 创建虚拟环境并安装

```bash
cd /opt/agents-production-studio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. 准备环境变量

复制示例文件：

```bash
sudo mkdir -p /etc/agents-studio
sudo cp deployment/env/agents-studio.env.example /etc/agents-studio/agents-studio.env
```

按需编辑：

- `AGENTS_ADMIN_TOKEN`
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `HOST`
- `PORT`
- `OUTPUT_DIR`

### 4. 创建输出目录

```bash
sudo mkdir -p /var/lib/agents-production-studio
sudo chown -R "$USER":"$USER" /var/lib/agents-production-studio
```

### 5. 安装 systemd 服务

```bash
sudo cp deployment/systemd/agents-studio.service /etc/systemd/system/agents-studio.service
sudo systemctl daemon-reload
sudo systemctl enable agents-studio
sudo systemctl start agents-studio
```

查看状态：

```bash
sudo systemctl status agents-studio
```

### 6. 配置 nginx 反向代理

```bash
sudo cp deployment/nginx/agents-studio.conf /etc/nginx/conf.d/agents-studio.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 三、Docker 方案

在项目根目录执行：

```bash
docker compose -f deployment/docker/compose.yaml up --build -d
```

## 四、发版包导出

在项目根目录执行：

```bash
bash deployment/scripts/package_release.sh
```

生成结果会出现在：

```text
dist/
```
