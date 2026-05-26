# 2026-05-20 晚间志愿套利讨论整理

日期：2026-05-20 晚

本文整理今晚围绕“高考志愿套利 / 大捡漏 / 个体化机会发现”的讨论。目标不是保存聊天流水账，而是把分散案例和想法收敛成 GaokaoAgent 后续可实现、可回测、可解释的研究路线。

## 1. 今晚讨论的主线

今晚的核心问题从“这些主播案例到底讲了什么”逐步推进到：

```text
怎样用数据和算法识别只有特定学生能承受、能兑现、能讲清楚的志愿套利机会？
```

我们最终形成的判断是：

```text
高考分数不是终点，志愿填报是第二次选拔。
第一次选拔做题能力，第二次选拔信息差、风险识别、家庭资源、价值偏好和博弈能力。
```

因此项目不应只是预测分数线，而应转向：

```text
Personalized Opportunity Discovery
个体化升学机会发现
```

即：

```text
先判断同分段普通结果是什么，
再找招生计划、专业组结构、学费、地区、校区、冷门专业、宣传热度造成的市场折价，
再判断这个学生是否正好能承受这些让利，
最后在控制调剂和滑档风险的前提下，把机会放进志愿组合。
```

## 2. 我们修正过的核心概念

### 2.1 不是“考什么分上什么大学”

传统逻辑：

```text
分数 / 位次 -> 匹配学校
```

我们的新逻辑：

```text
分数 / 位次 = 入场筹码
志愿填报 = 市场博弈和个体化资源配置
```

同一个分数，因为家庭资源、专业偏好、地域接受度、学费承受力、面子需求和调剂承受力不同，最优方案完全不同。

### 2.2 名校是相对概念

我们纠正了“名校=985/211”的固定理解。

对不同分数段，“更好的学校”不一样：

| 分数段 | 相对名校 / 层级跃迁 |
| --- | --- |
| 顶尖段 | 清北 / 华五 / 人大强专业 / 单列强专业 |
| 高分段 | 更高 985、强 211、冷门专业或异地校区机会 |
| 一本线附近 | 双一流、老一本、省属强校、行业老校 |
| 二本线附近 | 老牌公办本科、低关注地市公办 |
| 本科线边缘 | 避免高费民办或专科，争取低成本本科 |

因此算法应计算：

```text
RelativePrestigeLift(student, school)
= school_tier_score - expected_school_tier_at_student_rank
```

而不是只看绝对标签。

### 2.3 大捡漏不是免费午餐，而是让利交换

今晚明确了“让利”是套利模型的核心。

让利包括：

- 地区让利：接受偏远地区、非热门城市、非省会。
- 专业让利：接受冷门专业、专业组混搭、非热门专业。
- 学费让利：接受中外合作、高收费、艺术类成本。
- 校区让利：接受异地校区、非本部。
- 路径让利：接受艺术类、体育类、行业院校、小众路径。
- 调剂让利：接受组内不确定性。
- 就业确定性让利：接受短期就业路径不标准，换平台、身份、圈层。

数学化为：

```text
SacrificeVector =
[
  region_sacrifice,
  major_sacrifice,
  tuition_sacrifice,
  campus_sacrifice,
  pathway_sacrifice,
  adjustment_sacrifice,
  employment_uncertainty_sacrifice
]
```

学生对应有：

```text
ToleranceVector =
[
  region_tolerance,
  major_tolerance,
  tuition_tolerance,
  campus_tolerance,
  pathway_tolerance,
  adjustment_tolerance,
  employment_uncertainty_tolerance
]
```

真正的套利成立条件是：

```text
市场因为这些让利条件打折，
而该学生正好能承受这些让利。
```

## 3. 今晚讨论的案例与机制

### 3.1 四张基础案例图

前面四张图被整理成四类机会机制：

| 案例机制 | 建模名称 | 核心含义 |
| --- | --- | --- |
| 同一专业被拆进不同组，录取位次大幅波动 | `group_partition_mispricing` | item 必须是 `school + major_group`，不能只看学校或专业 |
| 上财 / 武大等高价值专业低位成交 | `historical_line_overdeterrence` | 历史高线会吓退考生，尤其在组改、quota 变动后 |
| 人大法学单列导致高分考生不敢填 | `standalone_major_anchor_discount` | 强专业单列后旧线不可比，可能出现低估 |
| 川大电气受舆情冲击 | `sentiment_shock_discount` | 舆情是市场信号，不等于学校真实价值下降 |

这些已沉淀到：

- `docs/opportunity_radar_modeling_notes.md`

### 3.2 大连理工盘锦中外合作案例

用户重点追问：

```text
为什么 18888 位能录到往年 11058 位左右的大连理工中外合作数理基础科学？
```

我们反推的机制：

- 大连理工学校品牌强。
- 盘锦校区带来校区折价。
- 中外合作带来高学费过滤。
- 组内新增专业和专业混搭降低家长信心。
- 往年数理基础科学高线可能吓退高分考生。
- 高分考生不填或排序靠后，实际入组人群变弱。
- 学生不只是进组，还可能进入组内前排专业。

这推动我们提出两阶段模型：

```text
P(final success)
= P(group admitted)
  * P(front major hit | group admitted)
```

也就是不能只算“能不能进专业组”，还要算：

```text
能不能进组内好专业？
会不会落到尾部专业？
```

### 3.3 中央美术学院艺术管理案例

用户纠正：右侧录取通知书是中央美术学院，不是华东师范大学。

该案例被定义为：

```text
symbolic_capital_opportunity
```

核心不是就业 ROI，而是：

- 行业头部高校身份。
- 家庭门面。
- 艺术圈层入场券。
- 北京和艺术产业资源。
- 有钱家庭能承受非标准就业路径。

模型上对应：

```text
Prestige / Face / Social Capital Opportunity
```

该案例帮助我们明确：

```text
同一个志愿，对不同家庭不是同一个商品。
```

有些家庭买的是专业就业现金流，有些家庭买的是品牌、身份、圈层和长期期权。

### 3.4 聊城大学 / 老牌本科案例

用户给出“二本民办线，不选择专业，选择到老牌一本专业”的案例。

我们将其定义为：

```text
public_floor_lift_opportunity
```

核心不是好专业，而是：

```text
用专业让渡和地区让渡，换取公办 / 老本科 / 更高学校层级。
```

这类机会尤其适合：

- 二本线附近学生。
- 家庭预算有限。
- 强烈偏好公办。
- 专业不挑。
- 能接受地市院校。
- 希望获得本科底座、考公/考研/就业基本盘。

### 3.5 北京体育大学中外合作案例

图中展示北体 03 组中外合作，学费高、海南陵水校区、专业限制较多，出现“本科线 + 1 分录北体”的叙事。

我们判断：

这类机会不是简单看去年低分，而是由多个折价因子叠加：

- 强品牌。
- 高学费。
- 异地校区。
- 专业冷门。
- 语言/体检/单科限制。
- 家长对路径不理解。
- 传播后可能反弹。

对应机会类型：

```text
tuition_campus_brand_discount
```

### 3.6 聊天截图：研究别人行为并找到漏洞

最后一张聊天图 OCR 不完全可靠，用户提醒“有些文字识别错了”。

我们保留机制，不保留不确定逐字内容。

可保留的机制是：

- 普通家长依赖公开资料和招生大本。
- 很多人不会系统对比去年和今年招生计划。
- 机会来自研究其他家长的行为漏洞。
- 成功案例会通过家长感谢和转介绍传播。
- 传播本身会提高下一年的反弹风险。

对应模型变量：

```text
public_data_visibility_low
manual_plan_diff_signal
average_parent_blind_spot
applicant_behavior_gap
case_spread_heat
rebound_risk
```

这推动我们补充：

```text
ApplicantBehaviorModel
```

即不仅判断专业组本身是否便宜，还要判断：

```text
普通家长会不会看见？
普通家长会不会敢填？
主播/机构会不会讲热？
这个机会会不会因传播而反弹？
```

## 4. 今晚形成的统一数学框架

最终推荐的核心分数可以写成：

```text
ArbitrageScore(student, group)
= RelativeLift(student, group)
  * AdmissionFeasibility(student, group)
  * PersonalAcceptability(student, group)
  * AssignmentOpportunity(student, group)
  - SacrificeCost(student, group)
  - TailAssignmentRisk(student, group)
  - ReboundRisk(group)
```

其中：

```text
RelativeLift
= 候选结果相对同分段常规结果的层级跃迁
```

```text
PersonalAcceptability
= 学生/家庭是否能承受地区、专业、学费、校区、路径、调剂等让利
```

```text
AssignmentOpportunity
= 进入组后命中好专业或可接受专业的概率
```

```text
ReboundRisk
= 该机会是否已被主播、机构、成功案例传播填平
```

对于大连理工这类“组内好专业”案例，单独定义：

```text
FrontMajorArbitrageScore =
  P(group_admitted)
  * P(front_major_hit | group_admitted)
  * FrontMajorValue
  * RelativeLift
  - SacrificeCost
  - TailAssignmentRisk
  - ReboundRisk
```

## 5. 今晚明确的后端模块

我们把后续实现拆成 7 个非 Agent Harness 核心模块：

### 5.1 CounterfactualBaseline

计算同分同位次普通填报结果：

- 常规学校层级。
- 公办 / 民办。
- 常规专业质量。
- 常规城市层级。
- 常规学费水平。

没有这个基准，就无法判断是否真的“捡漏”。

### 5.2 StudentValueModel

学习学生/家庭价值函数：

- 品牌和面子。
- 就业 ROI。
- 公办偏好。
- 成本敏感度。
- 专业严格程度。
- 城市灵活度。
- 校区接受度。
- 调剂接受度。
- 路径接受度。
- 后悔敏感度。

### 5.3 SacrificeVector

给每个专业组标注让利成本：

- 地区。
- 专业。
- 学费。
- 校区。
- 特殊路径。
- 调剂。
- 就业确定性。

### 5.4 OpportunityRadar

识别市场折价：

- 冷门专业折价。
- 中外合作 / 高学费过滤。
- 异地校区折价。
- 新增专业不确定性。
- 专业组重构。
- 历史锚定吓退。
- 单列专业锚定折价。
- 舆情折价。
- 低关注机会。

### 5.5 AssignmentOpportunityModel

预测：

- 进入专业组概率。
- 进入组内好专业概率。
- 落入尾部专业概率。

这是今晚最重要的新需求，因为用户强调：

```text
他们的方法甚至能够算进去比去年分数线低的，然后进入最好的专业。
```

### 5.6 ApplicantBehaviorModel

预测普通家长和市场会怎么反应：

- 公开资料是否容易看见。
- 招生大本是否隐藏了关键信息。
- 普通家长是否会对比去年和今年。
- 主播是否集中宣传。
- 成功案例是否已传播。
- 今年是否高反弹。

### 5.7 PortfolioPlanner

把机会放进组合，而不是单点押注：

- 大套利机会。
- 普通冲刺。
- 目标校。
- 稳妥校。
- 保底校。

## 6. 已创建或更新的记录文件

今晚新增或重点使用的文档：

| 文件 | 用途 |
| --- | --- |
| `docs/opportunity_radar_modeling_notes.md` | 记录四张图的机会雷达建模：组拆分、历史锚定、单列专业、舆情折价 |
| `docs/arbitrage_reverse_inference_model.md` | 记录反向推导模型：让利、同分段基准、组内好专业概率、2025 标签 |
| `docs/arbitrage_strategy_casebook_zh.md` | 中文案例簿：整理他大概率怎么做、我们该如何实现 |
| `docs/2026-05-20_evening_arbitrage_discussion_summary.md` | 本文：今晚聊天总整理 |

## 7. 对现有项目的定位修正

现有项目已经有：

- 专业组级推荐。
- 2025 招生计划对齐。
- admission probability。
- 组内专业 utility。
- tail assignment risk。
- quota stability / variance opportunity。
- crowding risk proxy。
- first-hit 志愿表。
- 2025 backtest / ablation。

今晚讨论后，项目的下一阶段重点应改为：

```text
从“专业组推荐系统”
升级为
“个体化志愿套利发现系统”
```

重点不再是继续堆 Agent，而是补后端模型：

```text
CounterfactualBaseline
StudentValueModel
SacrificeVector
OpportunityRadar
AssignmentOpportunityModel
ApplicantBehaviorModel
PortfolioPlanner
```

## 8. 下一步建议

建议按这个顺序落代码：

1. 实现 `CounterfactualBaseline`：先能算同分段常规结果。
2. 实现 `StudentValueModel`：把家庭价值观和让利承受力结构化。
3. 实现 `SacrificeVector`：给每个专业组标注地区、专业、学费、校区、路径、调剂成本。
4. 实现透明规则版 `OpportunityRadar`：先不用复杂 ML。
5. 实现 `AssignmentOpportunityModel`：重点解决“进组后能否进好专业”。
6. 加入 `ApplicantBehaviorModel`：处理主播宣传、案例传播、普通家长盲区和反弹风险。
7. 接入 2025 backtest / ablation：验证 tier lift、front-major hit、tail risk 是否改善。

第一版不要追求复杂模型。先用透明规则 + 2025 真实回测校准，等标签稳定后再做 logistic / GBDT / ranking model。

## 9. 最终研究表述

今晚形成的最准确表述是：

```text
GaokaoAgent 不是简单的分数线预测器，而是个体化志愿机会发现系统。
它将志愿填报视为第二次选拔：在同分段常规选择之外，系统识别招生计划、
专业组结构、学费、地区、校区、专业冷热、历史锚定和市场宣传造成的折价，
并判断某个学生是否正好能承受这些让利，从而在控制调剂、滑档和反弹风险的前提下，
获得更高层级、更高效用或更好组内专业的结果。
```

