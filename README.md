# Agents Production Studio

浏览器里的 AGENTS.md 生产工作台。它提供向导式信息收集、PLAN.md 预览、AGENTS.md 生成、案例回看，以及可选的模型增强配置。

Agents Production Studio is a browser-based workspace for collecting task context, previewing a PLAN.md, generating AGENTS.md, reviewing generated cases, and optionally enabling model-assisted refinement.

## 中文快速开始

1. 准备 Python 3.10 及以上环境。
2. 在项目根目录创建虚拟环境并安装：

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. 如需在页面中保存模型配置，先准备管理员令牌：

   ```bash
   cp .env.example .env
   ```

   然后按需编辑 `.env`。如果你不需要模型增强，可以跳过这一步。

4. 启动服务：

   ```bash
   set -a
   [ -f ./.env ] && . ./.env
   set +a
   agents-corpus serve-api --source-root . --output-dir ./tmp --host 127.0.0.1 --port 8765
   ```

5. 浏览器访问 `http://127.0.0.1:8765`。

6. 首次进入时，如果案例库为空，这是正常现象。你可以直接从“创建”开始。

## English Quick Start

1. Use Python 3.10 or later.
2. Create a virtual environment and install the project:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. If you want to save model settings from the UI, copy and edit the environment file:

   ```bash
   cp .env.example .env
   ```

4. Start the service:

   ```bash
   set -a
   [ -f ./.env ] && . ./.env
   set +a
   agents-corpus serve-api --source-root . --output-dir ./tmp --host 127.0.0.1 --port 8765
   ```

5. Open `http://127.0.0.1:8765` in your browser.

## Core Capabilities

- 向导式创建流程：按步骤收集模板、目标、环境、约束、补充问答和 PLAN.md。
- 可选模型增强：默认可关闭；启用后可优先读取系统默认模型，或切换自定义 OpenAI 兼容接口。
- 结果页与案例库：查看生成结果、回看系统创建案例、复用输入、一键复制。
- 时间戳记录：关键产物、日志和生成结果默认写入 `tmp/` 并带时间戳。
- 可选语料分析：如果你提供自己的 AGENTS 语料目录，可使用语料扫描、规则打标和能力目录构建能力。

## Included In This Open-Source Release

- 应用源码：[`agents_corpus_workflow`](./agents_corpus_workflow)
- 测试：[`tests`](./tests)
- 开源协作说明：[`CONTRIBUTING.md`](./CONTRIBUTING.md)
- 安全说明：[`SECURITY.md`](./SECURITY.md)
- 行为准则：[`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)
- 版本记录：[`CHANGELOG.md`](./CHANGELOG.md)
- 用户安装手册：[`docs/USER_GUIDE.zh-CN.md`](./docs/USER_GUIDE.zh-CN.md)
- 英文用户手册：[`docs/USER_GUIDE.en.md`](./docs/USER_GUIDE.en.md)
- 中文填写手册：[`docs/FILLING_GUIDE.zh-CN.md`](./docs/FILLING_GUIDE.zh-CN.md)
- 英文填写手册：[`docs/FILLING_GUIDE.en.md`](./docs/FILLING_GUIDE.en.md)
- 示例填写数据：[`examples/form_inputs`](./examples/form_inputs)
- 生产部署模板：[`deployment`](./deployment)

## Not Included By Default

- 当前工作区里的原始语料
- 本地运行日志和临时产物
- 私有模型密钥或管理员令牌

这意味着你拿到开源包后可以直接运行 Web 服务，但“案例库为空”或“没有现成能力目录”属于正常现象。

## Optional Corpus Analysis

If you want to use your own AGENTS corpus for labeling and capability mining, prepare a source root that contains:

```text
agents_process/
  contents/
  contents_zh/
```

Then run the service or CLI against that source root, for example:

```bash
agents-corpus serve-api --source-root /path/to/your/workspace --output-dir /path/to/your/workspace/tmp
```

## Model Configuration

- 默认推荐：先以“禁用模型增强功能”启动，确认产品流程可用，再决定是否开启模型。
- 如果你希望“系统默认模型”可用，请在启动前设置：
  - `OPENAI_BASE_URL`
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
- 如果你只想在页面里手动接入模型，则只需要设置 `AGENTS_ADMIN_TOKEN`，然后在右上角“模型优化”入口中完成配置。

## Project Layout

```text
agents_corpus_workflow/   Application code
docs/                     End-user and release documentation
examples/                 Example form inputs
deployment/               Production deployment templates
tests/                    Unit tests
.github/                  CI and GitHub collaboration templates
README.md                 Project overview
pyproject.toml            Package metadata
requirements.txt          Install helper
```

## Public vs Local Workspace

To keep the repository safe for open source use:

- public project files stay in the repository root
- local corpora, internal references, logs, and release leftovers should live under `.workspace-local/`
- `.workspace-local/` is ignored by Git

See [`docs/WORKSPACE_STRUCTURE.zh-CN.md`](./docs/WORKSPACE_STRUCTURE.zh-CN.md).

## Common Commands

启动 Web 服务：

```bash
agents-corpus serve-api --source-root . --output-dir ./tmp --host 127.0.0.1 --port 8765
```

运行测试：

```bash
python -m unittest discover -s tests
```

导出发版包：

```bash
bash deployment/scripts/package_release.sh
```

## Documentation Index

- 中文安装手册：[`docs/USER_GUIDE.zh-CN.md`](./docs/USER_GUIDE.zh-CN.md)
- English user guide: [`docs/USER_GUIDE.en.md`](./docs/USER_GUIDE.en.md)
- 中文填写手册：[`docs/FILLING_GUIDE.zh-CN.md`](./docs/FILLING_GUIDE.zh-CN.md)
- English filling guide: [`docs/FILLING_GUIDE.en.md`](./docs/FILLING_GUIDE.en.md)
- 生产部署说明：[`deployment/README.zh-CN.md`](./deployment/README.zh-CN.md)
- 发版准备日志：[`docs/RELEASE_PREPARATION_LOG.zh-CN.md`](./docs/RELEASE_PREPARATION_LOG.zh-CN.md)
- 工作区结构说明：[`docs/WORKSPACE_STRUCTURE.zh-CN.md`](./docs/WORKSPACE_STRUCTURE.zh-CN.md)

## License

MIT. See [`LICENSE`](./LICENSE).
