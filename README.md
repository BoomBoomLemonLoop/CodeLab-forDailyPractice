# CodeLab-for-DailyPractice

面向 CFD、燃烧动力学、有限体积法、Python/C++ 与小型涡喷研究的渐进式科研工作台。
每天用 1–2 小时完成一个可解释、可测试的小任务，默认计算资源为个人电脑、32 GB RAM。
这是自主实现与可追溯复现的工作区，不是第三方源码镜像或空目录集合。

## 导航与状态

当前优先：**Turns → Cantera（毕业论文）**；CFD 主线为 **Anderson 第 7 章准一维喷管与 MacCormack**。
先读 [教材—案例映射](docs/study-map.md)，再按 [每周节奏](docs/weekly-rhythm.md)
与 [每日任务记录](docs/study-tasks.md) 选择一次 60–120 分钟的小任务。
核心代码由学习者编写；Codex 提供推导提示、代码检查和验证设计，除非明确要求不直接给完整答案。

| 模块 | 内容 | 当前状态 |
| --- | --- | --- |
| [FVM 扩散](fundamentals/finite-volume-method/01-diffusion/README.md) | 一维扩散、解析解、守恒与网格收敛 | Tested：解析解数值验证通过 |
| [Cantera 0D](simulations/cantera/zero-dimensional-ignition/README.md) | 绝热定容 H2/air 自燃 | Tested：守恒与采样检查通过，未做物理 validation |
| [论文复现](reproductions/papers/emu-2024-surrogate/README.md) | 等待原始论文与目标图表 | Planned |
| [复现模板](templates/reproduction-case/README.md) | 参数、出处、验证与局限记录 | Implemented |
| [仿真计划](simulations/README.md) | OpenFOAM、Fluent、旋转接口 | Planned |
| [原创研究](research/README.md) | TVC、离心压气机、代理优化 | Planned |
| [参考索引](references/README.md) | 六个上游项目与阅读路线 | 已整理，未复制源码 |
| `src/codelab/` | 可安装命名空间；有真实复用需求后才提取工具 | Implemented |

Planned = 仅计划；Implemented = 有实现但不代表通过测试；Tested = 指定环境与范围内测试通过；
Validated = 与适当参考数据按预先定义的指标比较并通过，必须注明数据和适用范围。
解析解用于 verification，不代表实验或物理 validation。状态证据集中在
[第一轮验收记录](docs/initialization-report.md)。

## 安装与运行

需要 Python 3.11+（建议 3.12）。Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python fundamentals/finite-volume-method/01-diffusion/diffusion.py --cells 40
```

若激活脚本被策略阻止，无需修改系统策略，直接用 `.\.venv\Scripts\python.exe` 替代 `python`。
WSL Ubuntu：`python3 -m venv .venv`，然后 `source .venv/bin/activate`，其余命令相同。
Windows 与 WSL 的虚拟环境不能混用；切换系统时应分别创建自己的环境目录。

可选燃烧依赖与测试：

```text
python -m pip install -e ".[dev,combustion]"
python simulations/cantera/zero-dimensional-ignition/ignition.py
python -m pytest -m integration
```

基础 CI 不安装 Cantera、OpenFOAM 或 Fluent；手动 workflow_dispatch 才运行 Cantera 集成测试。
缺少 Cantera 时示例会给出安装命令，集成测试明确 skip；skip 不代表通过数值验证。
大型输出写入被忽略的 `outputs/`，小型最终结果须附环境、命令和来源。

## 下一步

先读 [开发指南](docs/development-guide.md) 与 [可复现规范](docs/reproducibility.md)，
以 [学习映射](docs/study-map.md) 的当前读书进度为准；[长期能力路线](docs/learning-roadmap.md)
用于按需补足扩散、对流扩散和压力速度耦合，不要求重新从第一项开始。
Python（NumPy/SciPy/Matplotlib/pandas）、C++ 和其余 FVM 子目录按真实任务逐步创建。
论文标题、DOI、作者、原文和目标图表补齐之前，不开展 `emu-2024-surrogate` 的实际复现。

本仓库未选择对外发布许可证；第三方内容以各自许可证为准，不因私有仓库而免除授权要求。
