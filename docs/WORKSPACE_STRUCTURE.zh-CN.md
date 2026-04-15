# 工作区结构说明

这个仓库按“公开区 / 本地区”拆分：

## 公开区

以下目录和文件适合直接进入 GitHub：

- `agents_corpus_workflow/`
- `tests/`
- `docs/`
- `examples/`
- `deployment/`
- `README.md`
- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `requirements.txt`

## 本地区

以下内容不建议公开：

- 原始语料
- 内部参考资料
- 本地调试日志
- 运行产物
- 本地导出的发布包

这些内容应统一放到：

- `.workspace-local/`

该目录已被 `.gitignore` 忽略。
