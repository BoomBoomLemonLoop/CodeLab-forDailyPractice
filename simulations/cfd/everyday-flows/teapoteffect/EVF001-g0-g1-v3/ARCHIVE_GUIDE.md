# GitHub选择性存档

本次准备文件，不自动stage、commit、push或merge。旧案例、网格与时间场原地保留。

在仓库根目录运行：

```powershell
.venv/Scripts/python.exe simulations/cfd/everyday-flows/teapoteffect/EVF001-g0-g1-v3/archive_selected.py
```

输出到本目录被Git忽略的archive_local/。ZIP名称由清单哈希确定，已有同名包不覆盖；包内ARCHIVE_MANIFEST.json记录逐文件SHA256、大小及当前HEAD。未提交工作树由文件哈希刻画，HEAD本身不能代表这些新增内容。

包括：研究方案、v3代码/参数/测试/复现脚本、G2小型数据与验证、两组固定姿态字典与汇总指标、关键结果图。原始10°/s parameters.json及5°/s派生参数均保留。原始10°/s是几何历史，不是动态倾倒VOF；5°/s没有独立动力学VOF结果，也没有此类求解器任务在等待。

不包括：旧draft和早期参考工程、大型STL/完整网格、processor目录、时间场、postProcessing原始序列、逐时VTP、完整求解日志、Python/WSL环境。它不是完整重启备份；仅靠包内字典不能直接续算40ms，需要依照运行说明重建网格、映射入口并重新求解。legacy_manifest中的历史文件哈希保留用于追溯，其外部旧文件未随包分发。

推荐上传方式：

1. 若仅存档，自己将ZIP作为GitHub Release附件上传，说明“探索性非稳态结果，非实验验证”；ZIP不是便于网页阅读的源码目录。
2. 若希望网页读代码，将ZIP解压到独立临时目录，按其teapoteffect相对结构选择文件放入仓库；不要解压覆盖当前计算目录。提交前检查diff与文件大小，不使用覆盖整个工作区的git add .。
3. 原始10°/s与5°/s都保留，学习入口为LEARNING_ORDER.md；不要把固定姿态Case 1/2分别改名为10°/s与5°/s，两者指的是25°/55°组合工况。

脚本只按显式目录/类型筛选科研文件，并做大小、CRC与SHA256检查；这不等于完整的隐私、许可证审查。上传前仍应审阅清单和文本。源码是唯一维护源，archive_local只是导出的快照，不应在解压副本继续开发。
