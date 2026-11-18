# 第一轮搭建验收记录

日期：2026-11-18。实际远端：`https://github.com/BoomBoomLemonLoop/CodeLab-forDailyPractice.git`。
注意远端名称无 `for-DailyPractice` 之间的额外连字符，以真实 origin 为准。

## 调查与变更

最初工作目录为空；用户连接后仅有 `.git`。成功 fetch 后，`git ls-remote origin`
未返回任何 refs，确认远端无历史、无 starter 或 Poiseuille/Cantera 成果可整合。
用户另行授权 main 上仅创建空初始化提交作为 PR 基线；全部实际文件在
`codex/research-scaffold` 分支实现。未删除已有文件或下载第三方代码。

下面列出全部交付文件（`.venv/`、`outputs/`、缓存及包元数据不提交）：

```text
CodeLab-forDailyPractice/
├── .gitattributes
├── .gitignore
├── AGENTS.md
├── README.md
├── pyproject.toml
├── .github/workflows/python.yml
├── src/codelab/__init__.py
├── tests/
│   ├── conftest.py
│   ├── test_diffusion.py
│   └── test_ignition.py
├── fundamentals/finite-volume-method/01-diffusion/
│   ├── README.md
│   └── diffusion.py
├── simulations/
│   ├── README.md
│   └── cantera/zero-dimensional-ignition/
│       ├── README.md
│       └── ignition.py
├── reproductions/papers/emu-2024-surrogate/README.md
├── templates/reproduction-case/README.md
├── research/README.md
├── references/
│   ├── README.md
│   ├── cfd-learning.md
│   ├── open-source-solvers.md
│   ├── combustion-modeling.md
│   └── numerical-methods.md
└── docs/
    ├── development-guide.md
    ├── reproducibility.md
    ├── learning-roadmap.md
    ├── verification-results.json
    └── initialization-report.md
```

## 实测环境与命令

Windows 11，Python 3.12.14；使用 Codex 随附 Python 创建项目内 `.venv`，
没有改动系统 Python 或 WSL。NumPy 2.5.5、pytest 9.2.0、Ruff 0.17.5、Cantera 3.2.0。
精确依赖、机理哈希、源码哈希与实算数值见 [verification-results.json](verification-results.json)。
确定性计算，随机种子不适用。项目可编辑安装已实际完成。

以下命令的 `python` 在本机实际为 `.\.venv\Scripts\python.exe`：

| 命令 | 实际结果 |
| --- | --- |
| `python -m pip install -e ".[dev,combustion]"` | 安装成功；沙箱 DNS 阻止后，经授权联网完成 |
| `python -m pytest` | 13 passed，2 deselected |
| `python -m pytest -m integration` | 2 passed，13 deselected，无 warning |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | 通过 |
| `python fundamentals/finite-volume-method/01-diffusion/diffusion.py --cells 80` | RMS 9.08776347e-5，Linf 1.28495610e-4 |
| `python simulations/cantera/zero-dimensional-ignition/ignition.py` | 点火延迟 0.000305 s，最终温度约 2908.62 K |

工作流使用 YAML 解析器成功读取，并检查 push/pull_request/workflow_dispatch 触发器与只读权限。
托管 CI 是否成功以 PR 的 GitHub checks 为准；本地解析不等于 GitHub 实际执行。

## 结果解释与状态

扩散 **Tested**：20/40/80 单元 RMS 约 1.456e-3、3.636e-4、9.088e-5，
加密一次误差约缩小四倍；二阶收敛、离散守恒、对称性及非法输入检查通过。
解析解提供 numerical verification，不宣称物理 Validated。

Cantera **Tested**：2001/4001 采样延迟分别 0.305/0.3055 ms，相差约 0.16%；
内能相对漂移约 2.24e-7，质量漂移为 0。短窗口未误报点火。
这里只验证所运行工况的基本性质和采样稳定性，没有实验/独立机理数据，不能标为物理 Validated。

模板与工程配置 **Implemented**；OpenFOAM、Fluent、TVC、压气机、代理优化和 emu 复现均 **Planned**。
本轮没有项目达到实验物理 **Validated** 状态。

## 限制与下一轮

- WSL2 `OpenFOAM-Ubuntu` 存在，但 Ubuntu/OpenFOAM 的实际版本和教程未核查、未运行。
- Fluent Student 的本机许可单元限制未核实；不将用户给出的约 50,000 当作确定值。
- 基础 CI 不安装外部仿真软件，手动 Cantera job 才启用 integration；未安装时 skip 不是测试通过。
- Cantera H2/air 不能替代涡喷燃油化学、热损失、混合和稳焰验证；积分容差敏感性尚待系统研究。
- 依赖范围不等于跨平台锁文件，精确实测版本仅代表本轮 Windows 环境。
- 上游部分许可证未确认，索引已明确标注；原始论文资料缺失，没有编造数据或推断论文内容。

下一轮：手推扩散边界行并绘制收敛图；补齐 emu 原文与目标图表；
扩展 0D 点火判据/容差/温压敏感性；核实 OpenFOAM 环境后只跑小型 cavity。
