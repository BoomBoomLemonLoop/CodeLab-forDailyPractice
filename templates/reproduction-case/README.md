# <paper-id>: <明确的复现目标>

状态：Planned。复制本目录到 `reproductions/papers/<paper-id>/` 后逐项填写。
PowerShell: `Copy-Item -Recurse templates/reproduction-case reproductions/papers/<paper-id>`。
WSL: `cp -r templates/reproduction-case reproductions/papers/<paper-id>`。
将占位符换为实际 id；未开展的数据与脚本目录按需创建，不放空占位文件。

## Reference

- DOI / 稳定 URL：unknown
- 标题、作者、年份、版本：unknown
- 原文/补充材料访问方式、数据与代码许可证：unknown

## Objective

目标图/表/数值、工况、范围：unknown。一个案例先选择一个可验收目标。

## Equations

控制方程、闭合模型、变量与单位、假设与不适用条件：unknown。

## Configuration

参数、网格、初始/边界条件、求解器、格式、时间步、容差：unknown。
将确定参数写到 `config/`，注明论文页码；未知项保留 unknown。

## Environment

OS、软件精确版本、依赖冻结、硬件、随机种子、Git commit：unknown。

## Execution

尚无可运行命令。实现后提供从干净环境出发的安装、计算和后处理命令，
注明预期时间、内存与输出路径。

## Verification

实现测试、解析/制造解、守恒、网格/时间步/容差敏感性与预定阈值：unknown。

## Validation / Comparison

参考来源、提取方法、SHA256 与许可；误差指标、单位、阈值依据：unknown。
非零标量可评估相对误差，近零值使用绝对容差；不能默认所有指标 ±5%。
记录实际误差与未通过项，不以代码运行成功替代复现。

## Limitations

未重建条件、模型差异、数据不确定度、资源约束：unknown。

## 按需目录约定

`config/` 参数；`data/reference/` 获授权的小型参考数据及来源；`scripts/` 执行程序；
`results/` 小型最终汇总；`notes/` 推导与研究日志。
`results/intermediate/`、`data/raw/` 和 `outputs/` 已被根 .gitignore 忽略。
新增结果后写清“问题 → 方法 → 计算 → 核查 → 解释”的结论和证据链接。
