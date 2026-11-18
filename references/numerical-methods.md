# 数值方法阅读记录要求

按扩散 → 对流扩散 → Upwind/Central/TVD → 瞬态 → 压力速度耦合 → 二维 NS 推进。
每种方法记录一致性、守恒性、稳定性、有界性、精度阶数和边界处理。
当前扩散的解析参考为 `sin(pi*x)`，由代入本案例方程直接得到，不依赖外部数据。
矩阵/算子研究可参考 [CrouzeixConjecture 的审计记录结构](https://github.com/jinshanmu/CrouzeixConjecture)，
仅学习论证留痕，不将候选证明当数值方法的已确立依据。
