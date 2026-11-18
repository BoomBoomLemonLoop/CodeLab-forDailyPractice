# 教材学习框架整合记录

日期：2026-11-18。分支：`codex/textbook-learning-framework`。
基于已有 `3b8d3ab` 研究框架；开始前 fetch 后远端 main 仍是空基线 `90b41c8`，
因此本轮 PR 以 `codex/research-scaffold` 为目标，只展示教材整合增量。
先审核/合并 PR #1，再将本轮 PR 的目标改为 main（或确认 GitHub 已自动调整）；本轮不自动合并。

## 输入与比较

用户提供目录 `CodeLab-for-DailyPractice-study-scaffold/` 与最新
`CodeLab-for-DailyPractice-study-scaffold (1).zip` 中每个文件内容完全一致。
ZIP SHA256：`01c7639ab353bbc74dbb5fd284aadddccae912cc668524d5a143c41e30d882cb`。
原目录完整保留本地，根 .gitignore 仅排除这一输入目录，避免将第二套项目、依赖和测试误提交。

| 更新版内容 | 整合决定 |
| --- | --- |
| README / AGENTS 的学习约定 | 增量加入现有文档，保留工程、验证和 Git 规则 |
| docs/study-map.md / weekly-rhythm.md | 按实际读书进度与现有路径重写；章节号注明版次待核对 |
| docs/roadmap.md | 不创建平行路线；更新原 learning-roadmap 的优先级，保留能力清单 |
| fundamentals/cfd/anderson、cfdpython | 建立学习说明，不生成算法答案或 Notebook |
| fundamentals/fvm/moukalled | 归入现有 finite-volume-method/moukalled，避免 fvm 与原目录并列 |
| fundamentals/combustion/turns | 建立理论笔记入口，执行代码链接到现有 Cantera 根目录 |
| simulations/combustion/cantera | 采用现有 simulations/cantera；新增总览、thermochemistry 与 zero-d-reactors 说明 |
| ignition-delay/run.py（CH4/gri30） | 不导入；保留原 H2/h2o2 ignition.py，两个工况不能视为同一数据 |
| poiseuille_fd.py、metrics.py 及随附测试 | 本轮范围为框架，不新增这些计算；原稿留在本地输入目录，未删除任何已有测试 |
| pyproject.toml | 保留现有包名、依赖、Ruff 和可选 integration 标记，不覆盖配置 |
| research / reproduction 模板与目录 | 继续用已有 research 和 reproductions/papers 体系，不创建 TVC 的平行命名 |
| references/starred-github.md | 加入学习用途表，技术与许可继续链接原 references/README.md |
| 未来每日任务 | 新建 study-tasks.md 的工作方式和单条记录模板；没有批量实例化任务 |

## 当前归属

```text
fundamentals/
  cfd/anderson/ch07-quasi-1d-nozzle/  # 新增说明，学习进行中、代码 Planned
  cfd/cfdpython/                    # 新增说明
  combustion/turns/                 # 新增理论入口
  finite-volume-method/
    01-diffusion/                   # 原案例不变
    moukalled/                     # 新增教材笔记入口
simulations/cantera/
  README.md                        # 统一总览
  thermochemistry/                 # Planned，无代码
  zero-d-reactors/                  # 模型导航，无重复实现
  zero-dimensional-ignition/        # 原程序与运行路径不变
docs/
  study-map.md / weekly-rhythm.md / study-tasks.md
  learning-roadmap.md               # 保留长期清单、更新当前优先级
  textbook-integration.md           # 本记录
references/starred-github.md         # 学习用途，未同步完整私人 Stars
```

原 `reproductions`、`research`、`tests`、`src` 保留。新版学习入口均为说明文档；
Planned 不代表已经有可运行代码。教材目录不保存版权 PDF，未复制上游源码。

## 实际回归检查

Windows / Python 3.12.14 / Cantera 3.2.0，使用现有 `.venv`。
整合前后基础测试均为 13 passed / 2 deselected；集成测试均为 2 passed / 13 deselected。

| 命令（本机 python 为 .venv/Scripts/python.exe） | 结果 |
| --- | --- |
| `python -m pytest` | 13 passed，2 deselected |
| `python -m pytest -m integration` | 2 passed，13 deselected，无 warning |
| `python -m ruff check .` | 通过 |
| `python -m ruff format --check .` | 通过 |
| `python fundamentals/finite-volume-method/01-diffusion/diffusion.py` | 40 单元 RMS 0.000363594644987886，与原结果一致 |
| `python simulations/cantera/zero-dimensional-ignition/ignition.py` | 点火延迟 0.000305 s，与原结果一致 |
| Markdown 相对链接检查 | 全部目标存在 |
| 对比基线代码、tests/src、pyproject、CI 与 verification-results.json | 无修改 |

没有为纯文档整合新增镜像式单元测试；保留全部原测试。
本轮不增加新的物理验证结论。远端执行结果以本轮 PR checks 为准。
