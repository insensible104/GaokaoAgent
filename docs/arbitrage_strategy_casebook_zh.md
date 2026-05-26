# 志愿套利策略案例簿与实现路线

日期：2026-05-20

这份文档用于整理最近讨论过的案例和建模思路。目标不是复述成功故事，而是把“他到底怎么做的”反推成 GaokaoAgent 可以实现、可以回测、可以解释的后端算法。

## 1. 一句话结论

这些案例背后不是神秘大模型，而是一套人工机会扫描流程：

```text
先判断学生愿意让出什么
再扫描哪些院校专业组因为这些让利条件被市场打折
然后比较同分段常规结果
最后把高跃迁机会放进志愿组合
```

换句话说：

```text
志愿套利 = 用学生可承受的让利，换取高于同分段常规选择的学校层级、行业身份或组内好专业。
```

让利包括：

- 地区让利：接受偏远地区、非热门城市、非省会。
- 专业让利：接受冷门专业、非热门专业、专业组混搭。
- 学费让利：接受中外合作、高收费、艺术类路径。
- 校区让利：接受异地校区、非本部。
- 路径让利：接受艺术类、体育类、行业院校、小众赛道。
- 调剂让利：接受一定组内不确定性。
- 就业确定性让利：接受短期就业路径不标准，换平台、身份、圈层。

## 2. 他大概率是怎么做的

从截图和案例反推，他的方法更像“人工 + Excel + 规则扫描 + 经验判断”，不是纯大模型。

### 2.1 先做学生画像

他会先判断这个学生能不能吃某类折价：

| 学生条件 | 能吃的折价 |
| --- | --- |
| 家里有钱，重牌子/面子 | 中外合作、高学费、艺术类、小众路径 |
| 不挑专业，重学校层级 | 冷门专业、专业组混搭、服从调剂 |
| 能去外地 | 地区折价、非热门城市、异地校区 |
| 想保公办/老本科 | 专业和地区让利，换公办层级 |
| 家庭有行业资源 | 艺术管理、体育管理、文化产业等非标准路径 |

这一步非常关键。因为同一个专业组，对一个学生是机会，对另一个学生是坑。

### 2.2 再找市场打折项

他会在招生计划和往年录取表里找这些信号：

- 好学校，但是中外合作学费高。
- 好学校，但是异地校区。
- 好学校，但是专业冷门。
- 专业组里有好专业，也混了劝退专业。
- 新增专业，往年没有精确分数线。
- 专业组拆分或合并，旧位次不可比。
- 往年某专业线很高，吓退高分考生。
- 低关注地区、行业院校、小众专业。
- 去年爆冷但今年可能反弹，需要判断热度。

这不是简单看“去年最低分”。他看的是：

```text
为什么去年/今年会低？
这个低的原因是否还存在？
这个学生是否能承受这个低分背后的代价？
```

### 2.3 再比较同分段常规结果

真正的“捡漏”不是绝对上名校，而是相对同分段跃迁。

例如：

- 二本线附近：从民办/弱公办跃迁到老牌公办本科。
- 一本线附近：从普通公办跃迁到老一本/双一流。
- 211 边缘：从普通一本跃迁到 211/强行业校。
- 985 边缘：从普通 211 跃迁到 985 冷门/中外/异地校区。
- 高分段：通过单列、拆组、历史锚定误判进入更强专业或更高平台。

所以我们不能固定写：

```text
名校 = 985/211
```

而应该写：

```text
名校 = 相对该学生分数段显著高一层的学校/专业组。
```

### 2.4 最后判断组内好专业概率

大连理工案例最关键：不是只进了组，而是低于往年线还可能进组内前排专业。

这说明他可能在判断：

```text
高分考生会不会因为历史高线/中外合作/校区/专业组标签而不填？
如果高分考生不填，那么这个学生进入组后，在组内排序是否足够靠前？
前排专业 quota 是否足够？
尾部专业是否还能接受？
```

也就是说，真正要算的是两段概率：

```text
P(进入专业组)
P(进入组内好专业 | 已进入专业组)
```

## 3. 我们讨论过的案例如何归类

| 案例 | 机会类型 | 主要让利 | 换来的东西 | 系统要学习什么 |
| --- | --- | --- | --- | --- |
| 大连理工盘锦中外合作 | `brand_discount_front_major_arbitrage` | 学费、校区、中外合作、组内混搭 | 985 品牌 + 组内前排专业 | 低于旧线也可能命中好专业 |
| 中央美术学院艺术管理 | `symbolic_capital_opportunity` | 非标准就业路径、艺术类成本 | 行业头部身份、家庭门面、社会资本 | 有钱且重面子的家庭效用不同 |
| 聊城大学/老牌本科 | `public_floor_lift_opportunity` | 专业、地区 | 从民办/弱校跃迁到老牌公办本科 | 低分段最重要的是层级和公办属性 |
| 北京体育大学中外合作 | `tuition_campus_brand_discount` | 高学费、海南校区、专业限制 | 强品牌、行业校身份 | 高学费和校区可以造成筛选折价 |
| 人大法学单列 | `standalone_major_anchor_discount` | 历史线不可比风险 | 强专业机会 | 高分考生被旧高线吓退 |
| 武大/上财等专业机会 | `historical_line_overdeterrence` | 历史锚定不确定性 | 高价值专业低位成交 | 旧线不等于今年真实市场价格 |

## 4. 我们应该实现的核心模型

### 4.1 CounterfactualBaseline

先算同分同位次普通填报会得到什么。

输出：

```json
{
  "baseline_school_tier": "普通公办本科",
  "baseline_public_private": "公办/民办",
  "baseline_major_quality": "普通专业",
  "baseline_city_tier": "普通地市",
  "baseline_cost_type": "普通公办学费"
}
```

没有这个基准，就不知道推荐结果到底是不是跃迁。

### 4.2 StudentValueModel

把学生和家庭的真实需求数学化。

核心变量：

```text
brand_face_weight
employment_roi_weight
public_school_preference
cost_sensitivity
major_strictness
city_flexibility
campus_tolerance
adjustment_tolerance
pathway_tolerance
regret_sensitivity
```

它回答：

```text
这个学生愿意用什么换什么？
```

### 4.3 SacrificeVector

每个专业组有自己的让利成本：

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

学生有对应承受能力：

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

代价函数：

```text
SacrificeCost(student, group)
= sum(sacrifice_k * (1 - tolerance_k) * weight_k)
```

### 4.4 OpportunityRadar

识别专业组为什么被市场打折。

信号包括：

- `cold_major_discount`
- `tuition_filter`
- `campus_discount`
- `region_discount`
- `new_major_uncertainty`
- `group_restructure_score`
- `historical_anchor_overdeterrence`
- `standalone_major_anchor_discount`
- `low_attention_signal`
- `sentiment_shock_discount`
- `quota_expansion_score`

输出：

```json
{
  "opportunity_type": "brand_discount_front_major_arbitrage",
  "market_discount_score": 0.78,
  "evidence_strength": 0.66,
  "rebound_risk": 0.42,
  "evidence_notes": ["中外合作", "异地校区", "旧专业线不可比"]
}
```

### 4.5 AssignmentOpportunityModel

专门算调剂和组内好专业。

普通推荐只算：

```text
P(进入专业组)
```

我们要多算：

```text
P(进入组内好专业 | 已进入专业组)
P(落到尾部专业 | 已进入专业组)
```

需要的特征：

- 组内每个专业 quota。
- 组内每个专业历史位次。
- 专业冷热程度。
- 新增专业比例。
- 前排专业是否小众/难理解。
- 高分考生是否被历史高线吓退。
- 是否中外合作/异地校区/高学费。
- 是否被主播或机构集中宣传。
- 学生位次相对预测组线的 margin。

前排专业套利分：

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

### 4.6 PortfolioPlanner

最后不是单点押注，而是放进组合。

池子应该分成：

- `front_major_arbitrage_pool`
- `relative_tier_lift_pool`
- `symbolic_capital_pool`
- `public_floor_lift_pool`
- `employment_roi_pool`
- `target_core_pool`
- `safe_anchor_pool`

志愿表里应该同时有：

```text
大套利机会
普通冲刺
目标
稳妥
保底
```

## 5. 反向推导 2025 数据的方法

用 2025 录取结果做标签，但特征只能用录取前可知道的信息。

每个样本长这样：

```json
{
  "student_rank": 18888,
  "candidate_group": "大连理工大学盘锦校区03组",
  "features_before_admission": {
    "historical_group_min_rank": 15356,
    "historical_front_major_min_rank": 11058,
    "quota_total": 0,
    "front_major_quota_share": 0.0,
    "tuition_level": "high",
    "campus_discount": 1,
    "cooperation_discount": 1,
    "new_major_ratio": 0.4,
    "major_mix_dispersion": 0.7,
    "historical_anchor_overdeterrence": 0.8
  },
  "labels_2025": {
    "group_admitted": true,
    "assigned_major": "数理基础科学",
    "front_major_hit": true,
    "tail_assignment": false
  }
}
```

然后回测：

```text
2021-2024 历史 + 2025 招生计划 -> 预测 2025
再用 2025 实际录取结果判卷
```

不能偷看 2025 录取结果来生成推荐。

## 6. 和现有代码的关系

现有项目已经有：

- 专业组 item，而不是学校级 item。
- 2025 招生计划对齐。
- `admission_prob` 录取概率。
- `major_utility_mean/min/dispersion` 组内专业效用。
- `tail_assignment_risk` 调剂尾部风险。
- `quota_stability_score` quota 稳定性。
- `variance_opportunity_score` 高波动机会代理。
- `crowding_risk` 简单拥挤风险。
- `first_hit_prob` 志愿表首命中概率。
- 2025 backtest / ablation。

还缺：

- 同分段常规结果基准。
- 学生让利承受向量。
- 专业组让利成本向量。
- 相对层级跃迁分。
- 组内好专业命中概率。
- 主播/宣传/热度造成的反弹风险。
- 按机会类型分池的组合规划。

## 7. 研究叙事

更准确的项目表述：

```text
GaokaoAgent is not a score-line predictor.
It is a personalized opportunity discovery system for college-admission markets.
It estimates whether a student can exchange acceptable sacrifices for a higher-tier,
higher-utility admission result than same-rank conventional choices.
```

中文表述：

```text
GaokaoAgent 不是简单预测分数线，而是做个体化志愿机会发现。
它先判断同分段普通选择是什么，再识别招生计划、专业组结构、学费、地区、校区、
专业冷热和市场宣传造成的折价，最后判断这个学生是否正好能承受这些让利，
并在控制调剂和滑档风险的前提下，把机会放进志愿组合。
```

## 8. 下一步落地顺序

1. 先实现 `CounterfactualBaseline`。
2. 再实现 `StudentValueModel` 和 `SacrificeVector`。
3. 然后实现 `OpportunityRadar` 的透明规则版。
4. 再实现 `AssignmentOpportunityModel`，重点算组内好专业和尾部专业。
5. 最后接入 `PortfolioPlanner` 和 2025 回测。

第一版不要追求复杂机器学习。先用透明规则 + 2025 回测校准，等标签稳定后再做 logistic/GBDT。

