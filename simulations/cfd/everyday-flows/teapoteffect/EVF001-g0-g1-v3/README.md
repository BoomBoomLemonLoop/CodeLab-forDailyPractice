# EVF-001 / v3：三角侧面实体与动态几何求交

后续执行依据已更新为 [G2/G3 固定入口与固定壶嘴方案](../EVF001_G2G3_固定入口与固定壶嘴实施方案.md)。
本目录保留 G0/G1 历史；新增 `export_g2_state.py` 仅提取出水快照，生成常量姿态、重力和入口几何，
不将倾倒时间序列传给 G3。G3 不使用移动网格或时变倾角。

本目录是唯一当前 G0/G1 工程。依据 2026-11-19 用户后续明确条件修订。
**Implemented / numerically Tested；未进行真实水壶实验 Validated，也没有进行 CFD。**
当前 G0/G1 只处理实体、姿态、水平面截交与几何度量。G2 上游速度模型、G3 VOF 均未开展。
原任务书把 VOF 编为 G2；此处遵循用户最新 G0/G1 → G2/G3 的分期，不混称已完成速度边界。

先看 [结果与局限](REPORT.md)、[几何四视图](artifacts/geometry_views.png)、
[三维动画](artifacts/immersion_3d.gif)、[曲线](artifacts/immersion_curves.png)、
[Case 2 敏感性](artifacts/case2_depth_sensitivity.png)。

## 1. 运行与文件

在仓库根目录 PowerShell 运行：

```powershell
.venv/Scripts/python.exe -m pip install -r simulations/cfd/everyday-flows/teapoteffect/EVF001-g0-g1-v3/requirements.txt
.venv/Scripts/python.exe simulations/cfd/everyday-flows/teapoteffect/EVF001-g0-g1-v3/run_all.py
```

第一条仅在缺依赖时执行。`run_all.py` 顺序执行单元测试、解析/细化验证、旧文件哈希检查和全量生成；任一子命令失败立即停止。全过程约数分钟，日志直接写入 `artifacts/`。
也可在本目录用已装依赖的 Python 运行：

```text
python -m unittest discover -s . -p test_geometry.py -v
python verify_numerics.py
python run_g0.py --samples 61
python run_g0.py --no-animation --out artifacts_preview
```

默认输出在本目录 `artifacts/`，重跑更新这些产物。输出路径必须处于本独立目录内。
修改 `parameters.json` 后重跑；`--config <json>` 可载入另一份参数。测试中某些断言针对本次约定的 60°、R5、45 mm、两组姿态，改变研究定义后需相应解释并更新基准，不能简单删掉失败断言。

| 文件 | 作用 |
| --- | --- |
| `parameters.json` | SI 参数；示例与暂定项均标注；长度由高度和 70° 导出 |
| `geometry.py` | 三角裁切、法向偏移、独立包边、旋转、截交、截面度量 |
| `run_g0.py` | CSV、曲线、几何图、GIF、敏感性、ParaView 序列、审计 JSON |
| `vtk_export.py` | 不依赖 VTK Python 的 VTP/PVD 写出 |
| `test_geometry.py` | 几何与事件的单元数值验证 |
| `verify_numerics.py` | 独立解析体积、离散细化、68 个既有文件 SHA-256 检查 |
| `verify_artifacts.py` | 独立曲面积分对照、VTP/PVD 结构及图片/GIF 解码检查 |
| `run_all.py` | 一键运行及实际日志 |
| `G1_boundary_contract.json` | 运动学时间与粒子时间分离；未来流场输入保持 null |
| `legacy_manifest.json` | 本轮修改前既有文件的相对路径及哈希，不包含新工程 |

不执行 Git add/commit/push/merge。旧参考项目和任务书保持原样。
项目新文件可由用户自主选择上传；`.mplcache/`、`__pycache__/` 为本地缓存，不应上传。

## 2. 几何定义：两个三角面，不是定截面挤出槽

局部壶嘴坐标记为 **S=(s,y,w)**：s 沿圆角低洼母线向出口，y 横向，w 垂直于母线的槽深方向。
这三个轴不是世界竖直坐标；尤其 w 不应误读为 Z_world。

45 mm 暂按“直立姿态中，圆角低洼母线起点与出口内壁接缝最低点的竖直高差”解释：

\[
L=0.045/\sin70^\circ=0.04788799976\;\mathrm m.
\]

这不是横截面槽深，也不是水平投影长度。若实际 45 mm 指的是完整尖棱锥顶点至基面高度，
该定义需另行修订；当前解释遵循用户明确允许的两端高差约定。
横截面出口深度 **D=25 mm** 独立暂定，不能从现有高度与夹角唯一推出。

记半内夹角 a=30°，中央内圆角 R=5 mm，φ_max=π/2−a=60°。
内圆角为以 `(y,w)=(0,R)` 为圆心的圆柱面：

\[
y=R\sin\phi,\quad w=R(1-\cos\phi),\quad |\phi|\le\phi_{max}.
\]

相切侧面为 `w=|y|cot(a)+R−R/sin(a)`，相切高度 w_t=2.5 mm、横向坐标 |y_t|=4.330127 mm。
**整个内表面用 `0≤s≤L` 且 `w≤D s/L` 裁切。**
每一侧保留下来的平面确实是三角面：

- 上游相切顶点 `(L w_t/D, ±y_t, w_t)`；
- 出口相切点 `(L, ±y_t, w_t)`；
- 出口上缘 `(L, ±y_max, D)`，y_max=17.320508 mm。

中央圆柱面也受同一三角边界裁切，从 `(0,0,0)` 展开，两侧接缝光滑。
不存在“把同一个 V 截面水平挤出”的建模步骤。
未圆角的两平面可延伸到虚拟尖棱锥顶点 `(-L*5/25,0,-5) mm`（长度先统一换成 mm）。
固定 R5 与保留零半径尖点不相容；当前用圆柱面裁去该尖点，并将剩余圆角母线的起点设为事件 A。
这里只保留两片面及其连接，不生成完整封闭棱锥的四壁流道。

内表面指向流体的单位法向为 n；外壁为 `p_out=p_in−0.0012 n`。
因此圆角外半径为 6.2 mm，侧面法向间距为 1.2 mm，绝非简单沿 w 方向减 1.2 mm。
实体上缘用封口面闭合；上缘并未额外圆角。该封口不代表真实壶腔连接。

出口包边独立定义半径 h=0.6 mm，沿出口截面点 p 的半圆为：

\[
p_{lip}(\theta)=p-hn+h\cos\theta\,n+h\sin\theta\,e_s,
\quad 0\le\theta\le\pi.
\]

它与内外壁相切。半圆接 1.2 mm 等厚壁要求 `2h=t_wall`，所以 h 独立于 R5，但在此特定半圆模型中不独立于壁厚。
若要独立改变 h 而保持壁厚，需改成另一种光滑过渡，当前配置明确拒绝不相容值。
STL 是三角离散表面，解析模型 C1 相切不意味着 STL 有连续面法向；尚未生成 STEP 或 CAD 内核 B-rep。

## 3. 统一旋转与水平面

壶体坐标 B 采用直立参考姿态。绕 y 轴的右手旋转记为 R_y：

\[
r_B=R_y(-70^\circ)r_S,\quad
r_W=R_y(70^\circ-\beta(t))(r_B-p_B)+p_W.
\]

默认 p_B=p_W=0，是运动学坐标规约，**不要求或假装知道实物转轴**。
于是世界高度 `Z=s sinβ+w cosβ`，横向坐标 Y=y。
世界液面为 `Z=H(t)`，浸没判据为 `Z≤H(t)`。
纯俯仰下，在固定 s 的 y–w 截面中：

\[
w=(H-s\sin\beta)/\cos\beta,
\]

与 y 无关。所以草图的 45°/15° 不会自动成为这个横截面里的斜液面线。
若草图是另一观察平面或投影，需要另行定义那个平面；本轮不强迫三维截交满足未定义的二维图角。

## 4. 两个事件与显式液面插值

**事件 A**：液面接触圆角母线起点 `(0,0,0)`，Case 1 t=0，β=55°，H=0。

**事件 B**：液面到达圆滑出口的最低越流门槛。
这里“门槛”不是外壁最低点，也不是简单取 s=L 接缝的最低点，而是从内侧跨过包边路径的最高点，再在各横向路径中取最低者（minimax）。
对当前纯俯仰、对称几何，最低路径在 y=0，包边最高点 θ=β：

\[
H_B(\beta)=L\sin\beta+h(1-\cos\beta).
\]

数值测试用整条出口截面的各路径峰值检查这一最小值。
事件 B 是**几何越流门槛**；没有压力、毛细或惯性模型，不能宣称该时刻已经计算出正流量。
在门槛恰好相等时，临界路径刚接触，有限通量仍未知。

| 条件 | Case 1 | Case 2 |
| --- | --- | --- |
| β(t) | 55°−10°/s·t | 70°−10°/s·t，用户指定暂定姿态 |
| 时长 T | 3 s | 1.5 s |
| 结束 β | 25° | 55° |
| H(0) | 0 | 示例 10 mm；扫描 5/10/15 mm |
| H(T) | H_B(25°) | H_B(55°) |

采用明确的 `H(t)=H(0)+(H(T)−H(0))t/T`。
这仅是连接两个几何事件的插值，不是储水体积守恒求出的液位。
中间位置并不唯一；当前也没有假定液面前沿沿母线匀速。
每一时间样本检查出口门槛尚未到达/恰好到达，Case 2 初始母线浸没长度为 H(0)/sin70°>0。

侧缘被同一水平面淹没是允许的几何判据；本模型不阻止真实水沿侧缘离开，也不包含连接壶体的围挡。
所以事件 B 是**指定出口**的门槛，不能声称一定是整个真实壶体的首次漏水事件。
这一边界已写入 CSV 的 `max_side_rim_submergence_m`，不因此要求真实储水量或阻止当前几何研究。

## 5. 输出量与速度区别

两个 `case*_history.csv` 默认各 81 个样本：61 个均匀时间点加上出口接缝接触至门槛之间的 21 个点（结束点去重）。
这段短时间窗先用二分法定位，避免仅有一个非零出口样本而画出假渐变。
[出口放大图](artifacts/outlet_detail.png) 单独显示门槛前的毫秒级时间窗。
长度 m、面积 m²、体积 m³、时间 s、角度 deg：

- `P_upstream/mid/outlet_m`：s/L=0.1、0.5、1 的**内壁截面几何浸没弧长**。起点 s=0 退化为一点，不拿它作有宽度入口。
- `b_*_m`：该截面浸没曲线的横向跨度，不是出口流束宽度。
- `A_*_m2`：内壁截面与其两上缘连线围成区域中、液面以下的面积；液面超过上缘时截断至该截面，不推断上方液体面积。
- `inner_submerged_area_m2`：被水平面裁切的三维**内壁表面积**。不是外壁动态润湿面积。
- `intersection_length_inner_m`：三维平面/内壁交线长度，不能与某个截面的 P 混用。重复三角公共边去重。
- `V_submerged_trough_m3`：上述有界截面面积沿 s 数值积分，几何体积而非真实壶内总水量。
- `valley_front_s_m`：水平面与直母线交点裁至 [0,L]；`extrapolated_plane_valley_s_m` 保留直线延长线交点。
- `geometric_front_ds_dt_m_s_NOT_FLUID_U`：直母线交点的有限差分，仅在交点位于 [0,L) 时输出。进入包边后 CSV 留空、JSON 为 null，避免把截断位置的假减速当作前沿动力学；它不追踪包边上的弧长前沿。差分受时间离散影响。
- `lip_crest_clearance_m`：门槛高度减 H；事件 B 为 0。

由于包边门槛高于内壁接缝，事件 B 时 `P_outlet`（**s=L 接缝截面**）通常已有小的非零值；
而门槛处仍是刚刚接触。不能把二者混为同一截面，也不能为了漂亮曲线强行扩大湿周。

交线速度由 `Z(s,t)=H(t)` 求导可得（在直母线上，转轴规约为 0）：

\[
\dot s=\dot H/\sin\beta-H\cos\beta\,\dot\beta/\sin^2\beta.
\]

这是几何事件轨迹。流体速度需要粒子轨迹与动量方程，例如
`Du_s/Dτ=−(1/ρ)∂p/∂s+g_s+…`；本几何向出口上坡，`g_s=−g sinβ`，不能把它一律当正加速。
3 s 不是粒子运动时间 τ，L/3 不给出真实出口速度。
没有生成速度场、Q、液膜厚度、0.7 mm 均匀膜、抛物线速度场或 Weber 数。

真实三相接触线还取决于液体是否存在、流场、润湿性、接触角和历史。
此处橙色线只叫水平面/固体几何截交线，蓝色仅叫几何浸没区。

## 6. 查看与验证

VS Code 可直接预览本目录 Markdown、PNG、GIF、SVG、CSV。
标准 STL 文件使用 **m**，STL 本身不记录单位；导入毫米制 CAD 时需主动乘 1000。

ParaView：打开 `artifacts/paraview/case1.pvd` 或 `case2.pvd`，Apply、Reset Camera、播放。
每组输出 21 个真实时间样本，part 0=内壁，1=截交线，2=水平面，3=低分辨率实体显示网格。
可 Extract Block 分开显示；`z_minus_H_m` 是几何有符号高差，不是 alpha.water。
用它作 Contour=0 可复核内壁交线，用 Clip≤0 可复核内壁浸没区。
显示网格低于主 STL 分辨率，仅用于预览；两者都不是 CFD 体网格。

GIF 两幅共享真实时钟，Case 2 到 1.5 s 后保持终帧，Case 1 继续到 3 s。
`intersection_initial/middle/arrival.png` 分别比较各自进度的 0%、50%、100%，标题保留实际时刻，
因此 middle 图两组不是同一时间；不要把静态进度对比误解成同步时刻。

测试覆盖解析 R5、法向壁厚、相切、闭合边邻接、Euler 特征、定向正体积、非退化三角形、
坐标变换、纯俯仰截面、两组事件、门槛最小路径、三角裁切、解析圆弧/圆段面积。
额外独立解析实体体积与四级离散细化见 `numerical_verification.json`。
这些都是数值 verification，不是实验 validation。ParaView XML 可做结构检查；是否打开过 GUI 以报告为准，不冒称 GUI 测试。

## 7. 本轮停止点

请先审查：45 mm 的定义、25 mm 横截面出口深度、三角侧面边界、R5 起端裁切、0.6 mm 包边、
Case 2 的暂定姿态和浸没深度、显式 H 插值、出口门槛定义。
之后另开 G2 流动模型讨论，再考虑独立 OpenFOAM v2606 三维 VOF 工程。
未要求提供真实储水体积、实物转轴或实测 H 才能推进当前工作。

本轮实际阅读：父目录任务书全文、根 AGENTS 与学习映射/进度文件；旧 `kettle-spout-vof` README 与 `make_cases.py` 前 180 行。
不存在的 rounded-valley-v2 与 rounded-V-spout-interFoam 未读取；不影响本轮。
没有读取或引用任务书提及论文的原文，未新增外部文献结论。当前代码为本项目原创，没有复制或供应外部仓库。
