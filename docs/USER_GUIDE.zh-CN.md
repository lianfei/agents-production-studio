# 用户安装手册（中文）

适用对象：第一次接触本项目、希望照着步骤跑起来的新手用户。

## 1. 你会得到什么

安装完成后，你可以：

- 在浏览器中打开一个向导式页面
- 按步骤填写任务信息
- 先预览 PLAN.md，再生成最终 AGENTS.md
- 查看结果页、案例页和复制按钮
- 按需开启或关闭模型增强

## 2. 安装前准备

请先准备：

- Python 3.10 或更高版本
- 一个可以打开终端的环境
- 一个现代浏览器

建议环境：

- macOS
- Linux
- Windows + PowerShell 或 WSL

## 3. 获取代码

你可以通过两种方式获取项目：

1. 从 GitHub 克隆仓库
2. 解压发布包

进入项目根目录后，再继续下一步。

## 4. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

如果你使用的是 Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 5. 安装项目

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

说明：

- 本项目运行时不依赖重量级第三方库
- `requirements.txt` 会安装当前项目本身

## 6. 可选：准备环境变量

如果你只是想先把页面跑起来，这一步可以先跳过。

如果你后面想在页面里“保存模型配置”或“启用系统默认模型”，建议先准备 `.env`：

```bash
cp .env.example .env
```

最常用的变量有：

- `AGENTS_ADMIN_TOKEN`
  作用：允许你在页面里执行模型配置写操作
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
  作用：让“系统默认模型”模式可用

如果你不准备使用模型增强，可以把这些变量全部留空。

## 7. 启动服务

在项目根目录执行：

```bash
set -a
[ -f ./.env ] && . ./.env
set +a
agents-corpus serve-api --source-root . --output-dir ./tmp --host 127.0.0.1 --port 8765
```

说明：

- `--source-root .` 表示以当前项目目录作为工作根目录
- `--output-dir ./tmp` 表示所有生成结果和日志输出到 `tmp/`
- `--port 8765` 是默认示例端口，可以换成其他端口

## 8. 打开浏览器

服务启动后，访问：

```text
http://127.0.0.1:8765
```

如果页面能正常打开，说明服务已经跑起来了。

## 9. 第一次使用时你会看到什么

首次启动时，以下现象都属于正常：

- 案例库为空
- 结果页为空
- 如果你没有配置模型，右上角会显示模型未启用或未配置

你可以直接从“创建”开始，不需要先准备任何语料。

## 10. 如果你想启用模型

推荐顺序：

1. 先确认不用模型也能正常打开页面并生成草稿
2. 再设置 `AGENTS_ADMIN_TOKEN`
3. 打开页面右上角“模型优化”入口
4. 选择开启或禁用
5. 如需系统默认模型，确保启动前已设置 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`OPENAI_MODEL`
6. 如需自定义模型接口，可直接在页面内填写并验证

注意：

- 没有 `AGENTS_ADMIN_TOKEN` 时，模型配置页是只读的
- 禁用模型优化时，不需要填写任何模型接入配置

## 11. 如何停止服务

如果你是在当前终端前台运行，直接按：

```text
Ctrl + C
```

## 12. 常见问题

### 页面打不开

检查：

- 终端里服务是否还在运行
- 端口是否被其他程序占用
- 访问地址是否与启动端口一致

### 模型配置保存时报管理员令牌错误

说明服务端开启了管理员校验，但你没有：

- 设置 `AGENTS_ADMIN_TOKEN`
- 或输入了错误令牌

### 我没有任何语料，还能用吗

可以。

本项目可以直接基于你填写的任务信息生成结果。  
如果你额外提供自己的 AGENTS 语料，它会进一步增强能力目录和参考能力匹配。

如果你要启用语料分析，请准备这样的目录结构：

```text
你的工作目录/
  agents_process/
    contents/
    contents_zh/
```

然后用这个工作目录作为 `--source-root` 启动服务。

### 案例库为什么是空的

因为案例库只展示“本系统生成过的结果”。  
你第一次运行时还没有生成历史，所以是空的。

## 13. 下一步看什么

- 想知道每一步该怎么填：看 [`FILLING_GUIDE.zh-CN.md`](./FILLING_GUIDE.zh-CN.md)
- 想部署到服务器：看 [`../deployment/README.zh-CN.md`](../deployment/README.zh-CN.md)
- 想导出发版包：执行 `bash deployment/scripts/package_release.sh`
