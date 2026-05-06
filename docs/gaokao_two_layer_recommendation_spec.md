# GaokaoAgent 两层推荐重构 SPEC：进组概率与组内专业风险

## 1. 背景纠偏

广东高考志愿的实际填写单元不是“学校”或“单专业”，而是志愿表中的一行：

```text
院校代码 + 院校名称 + 院校专业组代码 + 专业代码1-6 + 是否服从专业调剂
```

因此系统最终不应该只输出“推荐某个院校专业组”，而应该输出一张可执行的志愿草表。每个志愿行要同时回答两个问题：

1. 考生能不能被投进这个院校专业组。
2. 投进组之后，能不能进入自己填的专业；如果服从调剂，最差可能到什么专业。

一句话记忆：

> 广东志愿推荐的最小输出不是学校，也不是专业组，而是一行完整志愿：专业组 + 6 个专业排序 + 是否服从调剂。

## 2. 两层重构的核心定义

项目应拆成两个决策层。

| 层级 | 解决的问题 | 推荐对象 | 核心输出 |
| --- | --- | --- | --- |
| Layer 1: Group Admission | 能不能进院校专业组 | 院校专业组 | `P(投档进组)`、冲稳保标签、位次风险 |
| Layer 2: Major Assignment | 进组后能不能去想去的专业 | 组内专业排序与调剂选择 | 6 个专业志愿顺序、`P(调剂)`、最差专业风险 |

这两个层级不能混在一起。第一层看的是“专业组投档线”，第二层看的是“组内专业分配”。很多志愿失败不是因为进不了组，而是因为进组后专业分配不符合预期，或者不服从调剂导致退档。

一句话记忆：

> 第一层问能不能上车，第二层问上车后会被带到哪里。

## 2.1 共享特征层：高考价值与实际价值错位

两层推荐之间还需要一个共享特征层，用来识别“高考录取价格”和“专业实际价值”的错位。这里的高考价值不是价值判断，而是市场价格：某个学校、专业组或专业在广东考生中的录取位次、分数、热度和拥挤程度。实际价值则来自学科实力、培养质量、就业出口、城市机会、行业周期、课程体系和长期发展。

系统要显式建模这类错位：

```text
高考价值 = 录取位次价格 + 热门拥挤 + 学校/城市/专业叙事
实际价值 = 学科实力 + 就业质量 + 培养资源 + 行业前景 + 用户适配
value_gap = 实际价值 - 高考价值
```

如果一个专业实际质量不错，但录取位次相对同层次、同专业方向更低，它可能是低估机会；如果一个专业被短期热门叙事推高，但实际培养、就业和用户适配一般，它可能是高估风险。

一句话记忆：

> 高考分数线是市场价格，不等于专业真实价值。

### 2.1.1 为什么这是特征工程核心

传统填报常把往年最低位次当成价值本身，但这会混淆两个问题：

1. 这个专业为什么贵。
2. 这个专业值不值得这么贵。

例如，某些综合性大学的计算机类可能因为学校不是传统工科标签、校区位置、专业组捆绑方式、招生计划变化或考生认知不足，录取位次低于同层次理工院校；但这不代表它的培养和就业一定弱。反过来，有些热门标签专业可能因为群体追逐而被抬高，实际性价比不一定更好。

这就是推荐系统能做出差异化价值的地方：不是简单追高分专业，而是发现“价格、质量、风险、用户偏好”之间的错位。

### 2.1.2 建议特征

| 特征 | 含义 |
| --- | --- |
| `admission_price_score` | 用录取位次、分数、近年上移幅度表示高考市场价格 |
| `major_quality_score` | 专业培养质量，来自学科评估、专业评级、课程体系、科研平台等证据 |
| `employment_outcome_score` | 就业去向、升学质量、行业匹配、薪酬区间等证据 |
| `school_brand_score` | 学校整体声誉和平台价值 |
| `city_opportunity_score` | 城市产业、实习、就业网络 |
| `industry_cycle_score` | 行业处于上行、稳定、退潮或拥挤阶段 |
| `recognition_bias_score` | 考生对学校/专业的刻板印象导致的低估或高估 |
| `crowding_risk_score` | 今年可能被热门叙事继续追高的风险 |
| `value_gap_score` | 实际价值相对高考价格的差值 |
| `undervaluation_reason` | 为什么可能被低估 |
| `overvaluation_reason` | 为什么可能被高估 |

示例：

```json
{
  "school_name": "厦门大学",
  "major_name": "计算机类",
  "admission_price_score": 0.72,
  "major_quality_score": 0.82,
  "school_brand_score": 0.88,
  "city_opportunity_score": 0.76,
  "crowding_risk_score": 0.54,
  "value_gap_score": 0.16,
  "value_gap_label": "possibly_undervalued",
  "undervaluation_reason": [
    "综合性大学工科标签弱于传统理工院校",
    "同层次计算机方向录取位次可能存在折价",
    "学校整体平台和专业实际出口仍有支撑"
  ]
}
```

这里的数值先不需要伪装成绝对真理。第一版可以用规则和证据打分，后续再用专家标注或历史录取结果做校准。

### 2.1.3 数据来源

实际价值不能只靠 LLM 常识，必须有证据来源。

| 数据源 | 用途 |
| --- | --- |
| 招生计划与历史录取 | 计算高考价格、热度、位次趋势 |
| 学科评估/专业评级 | 计算专业质量 |
| 高校就业质量报告 | 计算就业和升学出口 |
| 专业培养方案/学院官网 | 判断课程、实验班、培养方向 |
| 城市产业数据 | 判断实习和就业机会 |
| 招生章程和专业备注 | 判断校区、中外合作、收费、英语授课、身体限制 |
| 专家规则/人工标注 | 校准低估/高估判断 |

Deep Research Agent 在这里的作用不是直接替代排序模型，而是给 `major_quality_score`、`employment_outcome_score` 和 `undervaluation_reason` 提供证据。

一句话记忆：

> LLM 不负责拍脑袋判断好坏，而负责把“为什么可能低估”找出证据。

## 2.2 捆绑招生与专业组价值拆解

专业组不仅是投档单位，也是一种捆绑招生结构。一个组里可能把高热度专业和低热度专业放在一起，也可能把强势专业、冷门专业、中外合作、校区差异和收费差异混在一起。系统不能只看组名或组内最热门专业，而要拆解整个 bundle。

需要识别四类捆绑：

| 类型 | 含义 | 风险/机会 |
| --- | --- | --- |
| `pure_high_fit_bundle` | 组内大多数专业都符合用户偏好 | 适合作为稳妥/保底 |
| `anchor_plus_drag_bundle` | 一个热门锚点专业带多个低偏好专业 | 容易误导用户，需要强风险提示 |
| `hidden_value_bundle` | 组内有被低估但实际价值不错的专业 | 可能是性价比机会 |
| `high_variance_bundle` | 专业差异大、计划数小或历史波动大 | 适合冲刺，不适合保底 |

建议新增特征：

```json
{
  "bundle_type": "anchor_plus_drag_bundle",
  "anchor_majors": ["计算机类"],
  "drag_majors": ["土木类", "材料科学与工程"],
  "hidden_value_majors": ["自动化类", "通信工程"],
  "bundle_purity_score": 0.42,
  "anchor_dependency_score": 0.81,
  "drag_major_ratio": 0.25,
  "hidden_value_score": 0.34,
  "tail_regret_risk": 0.47
}
```

一句话记忆：

> 专业组不是专业集合，而是学校设计出来的招生 bundle；推荐系统要拆包，而不是只看包装上的热门专业。

## 2.3 省内熟悉度溢价与省外认知折价

广东考生面对省内和省外院校时，认知环境不同。省内学校更容易被家长、老师、同学和本地媒体反复讨论，学校名气、就业去向、城市位置和生活成本更可感知，因此容易形成“本地熟悉度溢价”。省外学校，尤其是非顶尖但有真实学科或平台价值的 211、双一流、强双非一本，可能因为距离、认知不足、招生计划少、学校名字不熟、城市不熟而出现“省外认知折价”。

这不是说省外一定更好，也不是说省内一定虚高，而是要把地域认知差异变成可计算特征：

```text
local_familiarity_premium = 省内知名度 + 本地就业认知 + 家庭接受度 + 信息充分度
outprovince_recognition_discount = 距离惩罚 + 学校认知不足 + 小计划低曝光 + 城市陌生度
outprovince_opportunity_score = 实际价值 - 高考价格 + 认知折价 + 小计划波动机会
```

一句话记忆：

> 省内学校常有熟悉度溢价，省外学校常有认知折价；捡漏来自这个差价，但风险也来自这个差价。

### 2.3.1 省内/省外不能简单加减分

需要区分四种情况：

| 类型 | 表现 | 推荐策略 |
| --- | --- | --- |
| `local_premium_safe` | 省内名校/热门一本，认知充分、分数稳定、就业路径清楚 | 可作为稳妥或保底，但注意是否被本地热度推高 |
| `local_overheated` | 省内知名但专业/平台一般，被本地熟悉度推高 | 降低性价比分，提示高估风险 |
| `outprovince_hidden_value` | 省外 211/双一流/强双非，学科或专业强，但广东录取位次相对低 | 加入机会池，适合冲稳之间的“价值发现” |
| `outprovince_low_info_trap` | 省外分数低，但原因是位置弱、专业弱、校区/收费/就业出口差 | 不当作捡漏，必须解释低分原因 |

### 2.3.2 建议特征

| 特征 | 含义 |
| --- | --- |
| `school_province` | 学校所在省份 |
| `is_in_province` | 是否广东省内 |
| `distance_from_home_score` | 距离、交通、家庭接受度 |
| `local_awareness_score` | 广东考生/家长对学校的熟悉程度 |
| `local_employment_network_score` | 在广东就业、实习、校友网络可见度 |
| `outprovince_recognition_discount` | 省外认知不足造成的录取价格折扣 |
| `outprovince_quota_scarcity` | 省外在粤招生名额少造成的低曝光和高波动 |
| `outprovince_opportunity_score` | 省外低估机会分 |
| `province_preference_risk` | 用户和家庭是否接受离省 |
| `return_to_guangdong_risk` | 如果未来回广东就业，该校/专业在广东的认可度风险 |

示例：

```json
{
  "school_name": "某省外211大学",
  "school_province": "湖北",
  "is_in_province": false,
  "school_tier": "mid211",
  "major_name": "计算机类",
  "group_quota": 8,
  "local_awareness_score": 0.36,
  "outprovince_recognition_discount": 0.24,
  "outprovince_quota_scarcity": 0.71,
  "major_quality_score": 0.78,
  "admission_price_score": 0.58,
  "outprovince_opportunity_score": 0.19,
  "province_preference_risk": 0.42,
  "recommendation_role": "high_variance_opportunity",
  "explanation": "该校在广东认知度低、招生计划少，录取价格可能低于实际专业价值，但也存在信息不充分和离省适应风险。"
}
```

### 2.3.3 省外捡漏的必要条件

省外院校不能因为分低就判断为捡漏。必须同时满足：

```text
1. 学校层次或专业质量有支撑：211 / 双一流 / 强行业院校 / 强专业双非。
2. 广东录取价格相对偏低：同层次、同专业、同城市机会下位次更友好。
3. 招生计划少或认知不足造成低曝光：不是因为专业、校区、收费、就业明显劣势。
4. 用户能接受离省、城市、气候、生活成本和未来就业路径。
5. 专业组 bundle 的尾部风险可控。
```

如果只满足“分数低”，系统应该标记为：

```text
low_price_not_necessarily_value
```

一句话记忆：

> 分低不是捡漏；有真实价值支撑的分低才是捡漏。

### 2.3.4 与捆绑招生的关系

省外小计划专业组经常同时具备两个特征：

```text
认知不足 -> 可能低估
招生少 -> 波动变大
```

这会产生机会，也会产生风险。系统应把它们拆成两个指标，而不是混成一个“推荐/不推荐”：

| 指标 | 方向 |
| --- | --- |
| `outprovince_opportunity_score` | 发现低估机会 |
| `outprovince_uncertainty_score` | 提醒小计划和信息不足风险 |

Portfolio 里应该把这类学校放在“冲稳之间的机会位”，而不是直接当保底。除非它同时满足高投档概率、组内专业可接受、家庭接受离省、就业路径清楚。

一句话记忆：

> 省外小计划是机会仓，不是天然保底仓。

## 2.4 LLM-first 的特征补全与证据验证

省内外认知、学校实际价值、专业口碑、城市产业和就业网络不适合全部手工结构化维护。更合理的工程方案是：结构化数据只保存硬约束和高频字段，复杂背景判断由 Deep Research / Agent 按需补全，并且要求证据、置信度和缓存。

硬约束必须来自结构化数据：

```text
院校代码
院校名称
专业组代码
专业序号
专业名称
计划招数
批次
科类
选科要求
学费
校区/中外合作/英语授课/身体限制等专业备注
历年最低分和最低位次
```

软特征可以由 LLM + Deep Research 生成：

```text
学校所在省份和城市
学校层次和行业标签
专业实际实力
广东考生认知度
省外认知折价原因
回广东就业认可度
城市产业机会
专业组是否存在隐藏价值或包装风险
```

但 LLM 不能直接拍结论。每个软特征都要输出 evidence card：

```json
{
  "feature": "outprovince_recognition_discount",
  "value": 0.24,
  "confidence": 0.72,
  "evidence": [
    {
      "source_type": "admission_data",
      "claim": "该校在广东招生计划较少，历史录取位次波动较大"
    },
    {
      "source_type": "official_or_research_source",
      "claim": "该专业有学科/平台/就业证据支撑"
    }
  ],
  "uncertainty": "缺少广东本地就业认可度的强证据，因此只作为机会候选，不作为保底依据"
}
```

一句话记忆：

> 静态表管硬约束，Deep Research 管软判断，Verifier 管证据和置信度。

### 2.4.1 Agent 分工

这一层适合使用多个 agent，但每个 agent 要有清晰产物，不是为了显得复杂。

| Agent | 输入 | 输出 | 作用 |
| --- | --- | --- | --- |
| Candidate Scout | Layer 1 候选池 | 需要研究的省外/低估/捆绑候选 | 只挑不确定但有价值的候选 |
| Deep Research Agent | 学校、专业、专业组、城市 | evidence cards | 查证学校层次、专业实力、就业和城市机会 |
| Geo-Awareness Agent | 用户所在地、学校所在地、家庭偏好 | 省内外认知与离省风险 | 判断省内熟悉度溢价和省外认知折价 |
| Bundle Analyst | 专业组内全部专业 | bundle type 和 tail risk | 拆解捆绑招生 |
| Verifier / Critic | 全部特征和证据 | pass / revise / reject | 检查证据是否支撑结论 |
| Feature Cache | evidence cards | 可复用特征 | 避免重复研究同一学校/专业 |

推荐调用策略：

```text
1. 对大部分候选只用结构化特征快速排序。
2. 对高分段、高不确定、省外小计划、疑似低估和疑似捆绑风险候选，触发 Deep Research。
3. Deep Research 只补证据，不直接决定最终排序。
4. Verifier 检查证据是否足够；证据不足则降低置信度，而不是强行推荐。
5. 研究结果写入 cache，下次相同学校/专业复用。
```

一句话记忆：

> Agent 不是主流程的装饰，而是给高价值、高不确定候选做证据增强。

## 3. Layer 1：专业组投档层

### 3.1 输入

用户输入：

```json
{
  "province": "广东",
  "subject_track": "物理",
  "score": 620,
  "rank": 12000,
  "batch": "本科批",
  "selected_subjects": ["物理", "化学", "生物"],
  "preferred_cities": ["广州", "深圳", "杭州"],
  "preferred_major_categories": ["计算机", "电子信息", "自动化"],
  "blacklist_major_categories": ["土木", "环境", "材料"],
  "risk_preference": "balanced"
}
```

系统输入：

```text
2021-2024 历史录取数据：
- 院校代码
- 院校名称
- 专业组
- 专业/类
- 最低分
- 最低分平均排位
- 录取人数
- 备注

2025 招生计划：
- 院校代码
- 院校名称
- 批次
- 科类
- 专业组代码
- 专业序号
- 专业名称
- 专业备注
- 选科要求
- 计划招数
- 2021-2024 最低分/最低位次
```

### 3.2 处理流程

```text
1. 过滤不可填专业组
   - 科类不匹配
   - 批次不匹配
   - 选科要求不满足
   - 身体条件/单科要求明显不满足

2. 专业组候选召回
   - 按用户位次窗口召回
   - 按学校层次召回
   - 按城市偏好召回
   - 按专业大类召回
   - 按小计划高波动机会召回
   - 按稳定保底召回
   - 按省外认知折价机会召回
   - 按省内熟悉度溢价风险召回

3. 专业组投档概率估计
   - 使用历史最低位次
   - 使用招生计划 quota
   - 使用位次波动
   - 使用趋势项
   - 使用 Monte Carlo / fallback probability
   - 识别高考价格和实际价值错位

4. 专业组粗排与精排
   - admission probability
   - rank_diff
   - rank_ci
   - volatility
   - quota_stability
   - school/city preference
   - value_gap_score
   - bundle_type
   - outprovince_opportunity_score
   - province_preference_risk

5. 输出专业组候选池
```

### 3.3 输出 Schema

```json
{
  "school_code": "10008",
  "school_name": "北京科技大学",
  "major_group_code": "214",
  "batch": "本科批",
  "subject_track": "物理",
  "school_province": "北京",
  "is_in_province": false,
  "subject_requirement": "化学",
  "group_quota": 37,
  "historical_min_ranks": {
    "2024": 14724,
    "2023": 14082,
    "2022": 11055,
    "2021": null
  },
  "admission_prob": 0.74,
  "rank_diff": 2724,
  "rank_ci_lower": 11800,
  "rank_ci_upper": 16800,
  "volatility_level": "medium",
  "quota_bucket": "medium",
  "value_gap_score": 0.16,
  "value_gap_label": "possibly_undervalued",
  "bundle_type": "anchor_plus_drag_bundle",
  "outprovince_opportunity_score": 0.18,
  "province_preference_risk": 0.35,
  "strategy_tag": "target",
  "group_admission_reasons": [
    "2024专业组最低位次低于用户位次约2700名",
    "招生计划37人，稳定性中等",
    "该组计算机方向可能存在相对低估机会，但组内存在混搭风险",
    "近年组内不同专业位次有分化，需进入第二层评估"
  ]
}
```

### 3.4 这一层不要做什么

Layer 1 不能直接得出“推荐计算机类”。它只能说用户是否有机会被投到某个院校专业组。因为在广东模式下，专业组投档成功不等于专业录取成功。

一句话记忆：

> Layer 1 只判断进组，不承诺进专业。

## 4. Layer 2：组内专业分配层

### 4.1 输入

Layer 2 的输入是 Layer 1 通过筛选的专业组，以及该组的全部专业行。

```json
{
  "candidate_group": {
    "school_code": "10008",
    "school_name": "北京科技大学",
    "major_group_code": "214",
    "admission_prob": 0.74
  },
  "major_items": [
    {
      "major_code": "10",
      "major_name": "土木类",
      "quota": 3,
      "historical_min_ranks": {
        "2024": 14724,
        "2023": 15515,
        "2022": 15634
      }
    },
    {
      "major_code": "18",
      "major_name": "计算机类",
      "quota": 5,
      "historical_min_ranks": {
        "2024": 14724,
        "2023": 14082,
        "2022": 11055
      }
    }
  ],
  "user_preference": {
    "preferred_major_categories": ["计算机", "电子信息", "自动化"],
    "blacklist_major_categories": ["土木", "环境", "材料"],
    "risk_preference": "balanced"
  }
}
```

### 4.2 每个专业的评分

对组内每个专业计算四类分数。

| 分数 | 含义 | 示例 |
| --- | --- | --- |
| `major_fit_score` | 专业和用户偏好是否匹配 | 计算机类高，土木类低 |
| `major_admission_score` | 用户进组后进入该专业的相对机会 | 热门专业、计划少则更难 |
| `major_penalty_score` | 黑名单、身体限制、单科要求、学费等惩罚 | 黑名单专业直接高惩罚 |
| `major_regret_score` | 如果被录到该专业，用户后悔风险 | “只想计算机”却到土木，高后悔 |
| `major_value_gap_score` | 专业实际价值相对录取价格是否低估 | 综合大学强专业低估 |

建议先用规则模型，后续再换模型：

```text
major_fit_score =
  explicit_preference_match
+ category_similarity
+ career_goal_match
+ school_strength_bonus
+ value_gap_bonus
- blacklist_penalty
- misconception_penalty
```

```text
major_assignment_difficulty =
  normalized_major_rank_gap
+ popularity_penalty
+ small_quota_penalty
+ historical_volatility
```

### 4.3 组内专业排序

系统要给出 1-6 个专业代码排序。排序目标不是简单把用户喜欢的专业放前面，而是在“喜欢程度”和“录取机会”之间平衡。

推荐规则：

```text
专业1-2：用户最想去，且有一定机会的专业
专业3-4：仍然可接受，录取难度略低的专业
专业5-6：用户可接受的兜底专业，尽量避免黑名单
```

如果组内可接受专业不足 6 个，也不要硬填满。系统应该标记：

```text
该专业组可接受专业不足，不适合作为稳妥/保底志愿。
```

### 4.4 是否服从调剂

这是第二层最关键的决策。

| 情况 | 建议 |
| --- | --- |
| 组内几乎都是可接受专业 | 建议服从 |
| 组内有少量低偏好专业，但不触碰黑名单 | 谨慎服从 |
| 组内包含明确黑名单专业，且调剂概率不低 | 不建议服从，甚至不建议填该组 |
| 用户不服从调剂且专业竞争激烈 | 提醒退档风险 |
| 该组作为保底，但低偏好专业很多 | 不能作为保底 |

需要区分两个风险：

```text
服从调剂风险：可能被分到不喜欢的专业。
不服从调剂风险：专业录不上时可能退档，且本批次后续志愿不再投档。
```

一句话记忆：

> 服从调剂保录取，不服从调剂保专业；系统要告诉用户保的到底是什么。

### 4.5 输出 Schema

```json
{
  "school_code": "10008",
  "school_name": "北京科技大学",
  "major_group_code": "214",
  "recommended_major_order": [
    {
      "rank": 1,
      "major_code": "18",
      "major_name": "计算机类",
      "major_fit_score": 0.95,
      "major_assignment_difficulty": 0.72,
      "reason": "用户强偏好，组内热门，建议放第1志愿"
    },
    {
      "rank": 2,
      "major_code": "19",
      "major_name": "通信工程",
      "major_fit_score": 0.82,
      "major_assignment_difficulty": 0.58,
      "reason": "与计算机方向接近，可作为第二选择"
    },
    {
      "rank": 3,
      "major_code": "16",
      "major_name": "自动化类",
      "major_fit_score": 0.78,
      "major_assignment_difficulty": 0.55,
      "reason": "工科方向相关，可接受度较高"
    }
  ],
  "adjustment_recommendation": "cautious_obey",
  "adjustment_risk": 0.42,
  "non_obey_dropout_risk": 0.31,
  "worst_case_acceptable": false,
  "worst_case_majors": ["土木类", "材料科学与工程"],
  "bundle_risk_level": "high_mixed",
  "value_gap_reasons": [
    "计算机类在该校整体平台和专业方向上有实际价值支撑",
    "该组录取价格低于部分同层次强工科院校，但不能忽略组内混搭"
  ],
  "major_assignment_reasons": [
    "该组包含计算机类，但也包含土木类、材料科学与工程",
    "用户黑名单包含土木/材料，服从调剂存在后悔风险",
    "若不服从调剂，热门专业满额时存在退档风险"
  ]
}
```

## 5. 两层合并后的志愿行

最终输出应是 `VolunteerSlot`，也就是一行可填到志愿表里的结构。

```json
{
  "volunteer_index": 12,
  "strategy_role": "target",
  "school_code": "10008",
  "school_name": "北京科技大学",
  "major_group_code": "214",
  "major_codes": ["18", "19", "16", "14", "15", "11"],
  "major_names": [
    "计算机类",
    "通信工程",
    "自动化类",
    "机械类",
    "能源动力类",
    "储能科学与工程"
  ],
  "obey_adjustment": "cautious",
  "group_admission_prob": 0.74,
  "major_satisfaction_prob": 0.52,
  "value_gap_score": 0.16,
  "bundle_type": "anchor_plus_drag_bundle",
  "dropout_if_not_obey_prob": 0.31,
  "tail_major_risk": 0.47,
  "final_recommendation": "可作为稳妥偏冲志愿，但不能作为低风险保底",
  "explanation": "该专业组投档概率尚可，但组内包含土木类、材料科学与工程。若用户只接受计算机方向，不建议把该组作为保底。"
}
```

一句话记忆：

> 最终不是输出 top-k 专业组，而是输出一张带风险解释的志愿草表。

## 6. Portfolio 层：45 个志愿如何组合

两层模型评估单个志愿行，Portfolio 层负责把多行志愿组合成一张表。

组合目标：

```text
1. 冲稳保比例合理。
2. 每个层级都不能只有“进组概率”，还要看组内专业风险。
3. 保底志愿必须同时满足高进组概率和低组内尾部风险。
4. 冲刺志愿可以接受较高进组风险，但不能隐藏灾难性调剂风险。
5. 同一学校多个专业组可以同时出现，但要解释排序原因。
```

错误示例：

```text
把某个高进组概率、但组内全是用户黑名单专业的专业组当保底。
```

正确示例：

```text
保底项不仅进组概率高，而且组内 6 个专业大部分可接受，服从调剂后的最差结果仍在用户底线内。
```

一句话记忆：

> 保底不是“能进去”，而是“进去以后也不会后悔”。

## 7. 推荐系统视角

两层结构对应推荐系统的两个排序目标。

```text
Recall:
  召回可能投档成功的专业组，也召回可能被市场低估的专业组；单独保留省外认知折价候选池。

Group Rank:
  对专业组按投档概率、位次、quota、波动、学校城市偏好、value gap、bundle type 和省内外认知差异排序。

Major Rerank:
  对组内专业按用户偏好、专业风险、录取难度和实际价值错位排序。

Slate Rerank:
  把多个志愿行组合成冲稳保志愿表。

Critic:
  检查是否误导用户、是否隐藏调剂风险、是否保底失效、是否把高考价格误当真实价值。
```

这比原来的“多 Agent 推荐”更清楚，因为每个模块都有明确输入输出。

一句话记忆：

> 粗排排专业组，精排排组内专业，重排排整张志愿表。

## 8. 当前实现和目标实现的差距

| 当前实现 | 问题 | 重构目标 |
| --- | --- | --- |
| `search_major_groups` 聚合历史专业组 | 主要服务进组概率 | 保留为 Layer 1 |
| `MajorGroupRow.major_list` 只存专业名 list | 缺专业代码、计划数、历史专业线、组内风险 | 新增 `MajorItem` |
| `adjustment_risk = 0.15 if len(major_list) < 6 else 0.05` | 专业数量不能代表调剂风险 | 改为基于低偏好专业比例、黑名单、组内分化 |
| `major_list[:6]` 作为推荐专业 | 没有真正排序 6 个专业志愿 | 新增 `MajorAssignmentPlanner` |
| `comprehensive_score` 平均所有专业 | 容易掩盖“计算机 + 土木”的混搭风险 | 同时输出均值、下限、方差和尾部风险 |
| 缺少高考价值/实际价值错位特征 | 只能追随分数线，不能发现低估机会 | 新增 `ValueGapFeatureBuilder` |
| 缺少捆绑招生类型识别 | 不能区分纯净组、锚点拖拽组、隐藏价值组 | 新增 `BundleAnalyzer` |
| 省内/省外只当城市偏好处理 | 无法识别省内熟悉度溢价和省外认知折价 | 新增 LLM-first 的 `GeoAwarenessFeatureBuilder` |
| 缺少证据验证 | LLM 可能把软判断说得过满 | 新增 evidence card、confidence 和 verifier |
| 报告讲录取概率多 | 对“服从/不服从调剂”的代价解释不够 | 报告必须解释组内专业分配 |

## 9. 建议的数据结构改造

### 9.1 MajorItem

```python
class MajorItem(BaseModel):
    major_code: str
    major_name: str
    major_category: str
    quota: int
    subject_requirement: str | None = None
    tuition: float | None = None
    notes: str | None = None
    historical_min_ranks: dict[int, int | None] = {}
    fit_score: float = 0.0
    assignment_difficulty: float = 0.0
    value_gap_score: float = 0.0
    quality_evidence: list[str] = []
    regret_risk: float = 0.0
    is_blacklist: bool = False
```

### 9.2 MajorGroupCandidate

```python
class MajorGroupCandidate(BaseModel):
    school_code: str
    school_name: str
    school_province: str | None = None
    is_in_province: bool = False
    major_group_code: str
    batch: str
    subject_track: str
    group_quota: int
    major_items: list[MajorItem]
    admission_prob: float
    rank_diff: int
    volatility_level: str
    value_gap_score: float = 0.0
    value_gap_label: str = "neutral"
    bundle_type: str = "unknown"
    bundle_purity_score: float = 0.0
    anchor_majors: list[str] = []
    drag_majors: list[str] = []
    hidden_value_majors: list[str] = []
    local_awareness_score: float = 0.0
    outprovince_recognition_discount: float = 0.0
    outprovince_opportunity_score: float = 0.0
    province_preference_risk: float = 0.0
    evidence_cards: list[dict] = []
    feature_confidence: dict[str, float] = {}
    strategy_tag: str
```

### 9.3 MajorAssignmentPlan

```python
class MajorAssignmentPlan(BaseModel):
    recommended_major_order: list[MajorItem]
    obey_adjustment: str
    adjustment_risk: float
    non_obey_dropout_risk: float
    worst_case_majors: list[str]
    bundle_risk_level: str
    explanation: list[str]
```

### 9.4 VolunteerSlot

```python
class VolunteerSlot(BaseModel):
    volunteer_index: int
    strategy_role: str
    school_code: str
    school_name: str
    major_group_code: str
    major_codes: list[str]
    major_names: list[str]
    obey_adjustment: str
    group_admission_prob: float
    major_satisfaction_prob: float
    tail_major_risk: float
    dropout_if_not_obey_prob: float
    final_recommendation: str
    explanation: str
```

## 10. 建议模块拆分

```text
backend/src/recommendation/
  schemas.py
  data_adapter.py
  group_recall.py
  group_admission_ranker.py
  value_gap_features.py
  geo_awareness_features.py
  evidence_enricher.py
  feature_cache.py
  bundle_analyzer.py
  major_categorizer.py
  major_assignment_planner.py
  adjustment_policy.py
  volunteer_slate_optimizer.py
  critic_rules.py
```

职责：

| 模块 | 职责 |
| --- | --- |
| `data_adapter.py` | 统一 2021-2024 历史数据和 2025 招生计划字段 |
| `group_recall.py` | 召回候选专业组 |
| `group_admission_ranker.py` | 计算专业组投档概率 |
| `value_gap_features.py` | 计算高考价值和实际价值错位 |
| `geo_awareness_features.py` | 基于 LLM/Deep Research 证据计算省内外认知差异 |
| `evidence_enricher.py` | 为低估机会、学校实力、就业出口生成 evidence cards |
| `feature_cache.py` | 缓存学校/专业/城市研究结果，避免重复调用 |
| `bundle_analyzer.py` | 识别纯净组、锚点拖拽组、隐藏价值组和高波动组 |
| `major_categorizer.py` | 把专业名映射到专业大类 |
| `major_assignment_planner.py` | 组内 6 专业排序 |
| `adjustment_policy.py` | 判断是否建议服从调剂 |
| `volunteer_slate_optimizer.py` | 生成整张志愿表 |
| `critic_rules.py` | 检查误导性推荐和保底失效 |

## 11. 评估指标

### 11.1 Layer 1 指标

```text
专业组投档命中率
冲稳保分层准确性
预测最低位次误差
候选召回覆盖率
保底专业组失效率
低估机会召回率
高估风险识别率
省外低估机会识别率
省内过热风险识别率
```

### 11.2 Layer 2 指标

```text
用户高偏好专业覆盖率
黑名单专业暴露率
尾部专业风险识别率
服从调剂建议准确性
组内专业排序满意度
```

### 11.3 Portfolio 指标

```text
整张志愿表录取安全性
保底有效性
专业满意度下限
解释完整性
专家盲评通过率
性价比解释通过率
```

一句话记忆：

> 第一层评估录取，第二层评估满意，整张表评估后悔风险。

## 12. 重构路线

### P0：先修数据层

目标：让 2025 招生计划真正进入系统。

需要做：

```text
1. 映射 2025 字段：
   专业名称 -> major
   计划招数 -> quota
   专业组代码 -> major_group
   2024_最低位次 -> historical rank

2. 保留专业序号/专业代码：
   专业序号 -> major_code

3. 不要在清洗阶段把 2025 招生计划 drop 掉。
```

### P1：补 MajorItem

目标：每个专业组不再只有 `major_list`，而是有完整 `major_items`。

### P2：实现价值错位和捆绑招生特征

目标：在排序前先补共享特征层。

需要做：

```text
1. 新增 `value_gap_features.py`：
   - admission_price_score
   - major_quality_score
   - school_brand_score
   - city_opportunity_score
   - crowding_risk_score
   - value_gap_score

2. 新增 LLM-first 的 `geo_awareness_features.py`：
   - 不手工维护完整地理大表
   - 对学校省份、城市、离省风险先由 LLM 推理
   - 对关键候选触发 Deep Research 验证
   - 输出 evidence card 和 confidence
   - 缓存高频学校/专业结果
   - 计算 local_awareness_score、outprovince_recognition_discount、outprovince_opportunity_score、province_preference_risk

3. 新增 `bundle_analyzer.py`：
   - bundle_type
   - bundle_purity_score
   - anchor_majors
   - drag_majors
   - hidden_value_majors
   - tail_regret_risk

4. 新增 `evidence_enricher.py` 和 `feature_cache.py`：
   - Deep Research 生成证据
   - Verifier 检查证据是否支撑结论
   - 证据不足时降低 confidence
   - 排序使用 feature value × confidence
```

### P3：实现 Layer 1

目标：保留现有 Monte Carlo / fallback probability，但输出更清楚的 `MajorGroupCandidate`。

### P4：实现 Layer 2

目标：新增组内专业排序和调剂决策。

### P5：实现 VolunteerSlot

目标：最终输出志愿表行，而不是只输出专业组推荐。

### P6：更新 Report 和 Critic

目标：报告和审计必须显式检查：

```text
1. 是否把专业组误说成单专业。
2. 是否解释了组内混搭。
3. 是否说明服从调剂和不服从调剂的代价。
4. 保底志愿是否同时低投档风险和低专业尾部风险。
5. 是否把高分数线误当成高实际价值。
6. 是否识别了低估机会和捆绑招生风险。
7. 是否解释了省内熟悉度溢价、省外认知折价和离省风险。
```

## 13. 面试表述

30 秒版本：

> 后来我把项目重新拆成两层。第一层是专业组投档层，解决考生能不能进入某个院校专业组；第二层是组内专业分配层，解决进组后 6 个专业怎么排序、是否服从调剂、最差可能被分到什么专业。这样更贴近广东志愿表的真实结构，因为一行志愿不是单个专业，而是院校专业组、组内 6 个专业和一个调剂选择。

1 分钟版本：

> 广东采用院校专业组模式，一个专业组是一个投档单位，但组内可以包含多个专业。系统如果只推荐专业组，会漏掉一个关键风险：用户可能能进组，但进不了自己想去的专业，甚至因为服从调剂被分到低偏好专业。所以我把项目拆成两层：Layer 1 基于历史最低位次、招生计划、位次波动和 Monte Carlo 估计专业组投档概率；Layer 2 基于组内专业列表、专业代码、计划数、历史专业线、用户偏好和黑名单，生成 1-6 个专业志愿排序，并判断是否建议服从调剂。最终输出的是一张可执行志愿草表，而不是一个泛泛的推荐列表。

价值错位版本：

> 另外我会显式区分高考价值和实际价值。高考价值可以理解为录取市场价格，由位次、热度和拥挤决定；实际价值来自学科实力、培养质量、就业出口、城市机会和用户适配。比如有些综合性大学的计算机方向，录取位次可能低于同层次强工科院校，但实际培养和平台并不弱，这就是潜在低估机会。系统会把这种 value gap 做成特征，而不是简单追随往年分数线。

省内外版本：

> 我还会单独建模省内和省外的认知差异。广东省内学校因为家长和考生更熟悉，可能有本地熟悉度溢价；省外一些 211、双一流或强双非一本，因为距离远、招生名额少、学校名字不熟，可能在广东录取价格偏低。系统不会简单给省外加分，而是判断它是不是有真实专业价值支撑、是不是小计划高波动、用户家庭能不能接受离省，以及专业组捆绑风险是否可控。这样才能把“省外捡漏”从经验判断变成特征工程。

一句话记忆：

> 这个项目真正推荐的是“志愿表行”，并且要区分市场价格、实际价值和捆绑风险。

省内外一句话记忆：

> 省外低分不等于捡漏，省内高分不等于稳值；关键是认知差价、真实价值和尾部风险是否匹配。

## 14. 当前实现与逐步重构计划

这一节把“现在怎么做”和“接下来怎么改”对齐到代码层，避免 SPEC 只停留在概念。

## 14.1 当前主流程

当前 LangGraph 主链路是：

```text
Router
-> Profiling
-> Game Agent
-> Risk / Opportunity / Evidence Advisors
-> Deliberation Coordinator
-> Report
-> Critic
```

另外有可选慢循环：

```text
Deep Research -> Report -> Critic
```

当前主推荐逻辑集中在 `backend/src/agents/game_agent.py` 的 `game_agent_node`。它现在实际做的是：

```text
1. 加载 GaokaoQuantEngine。
2. 根据用户位次搜索候选专业组。
3. 对每个专业组计算投档概率。
4. 计算学校/专业综合分。
5. 做黑名单专业检查。
6. 做城市偏好调整。
7. 创建 MajorGroupRow。
8. Pareto 筛选候选。
9. Runtime RL 调整冲稳保配比。
10. 组合优化选最终推荐。
11. 写入 GameMatrix。
```

一句话记忆：

> 现在的核心是一个“大 GameAgent”：能算进组概率和组合，但没有正式生成志愿表行。

## 14.2 当前已有能力

| 能力 | 现有位置 | 状态 |
| --- | --- | --- |
| 用户画像 | `agents/profiling_agent.py` | 已有 |
| 专业组候选召回 | `engines/quant_engine.py::search_major_groups` | 已有，但主要基于旧历史数据 |
| 进组概率估计 | `engines/monte_carlo_sim.py` + `engines/probability.py` | 已有 |
| 冲稳保标签 | `engines/probability.py::classify_strategy_tag` | 已有 |
| 学校/专业综合评分 | `utils/school_major_scoring.py` | 已有规则版 |
| 城市偏好 | `utils/city_mapping.py` | 已有简化版 |
| 黑名单检查 | `agents/game_agent.py` | 已有粗规则 |
| Pareto 筛选 | `engines/pareto_optimizer.py` | 已有 |
| 组合优化 | `rl/volunteer_combination_optimizer.py` | 已有 |
| Runtime RL 配比 | `rl/runtime_policy.py` | 已有 |
| 专业分配预测原型 | `engines/major_assignment_predictor.py` | 有原型，但未接入主流程 |
| 调剂模拟原型 | `engines/adjustment_sim.py` | 有简化函数，未成为主逻辑 |
| Deep Research | `agents/deep_research_agent.py` | 有慢循环，但不是候选级证据增强 |
| Report | `agents/report_agent.py` | 已有，但仍是专业组推荐报告 |
| Critic | `agents/critic_agent.py` | 已有保底、黑名单、RAG 硬规则检查 |

一句话记忆：

> 代码里已有很多零件，缺的是统一的志愿表数据结构和候选级证据链。

## 14.3 当前主要问题

| 问题 | 具体表现 | 后果 |
| --- | --- | --- |
| 2025 招生计划未充分进入推荐结构 | `quant_engine` 主要映射旧字段：`专业/类`、`最低分平均排位`、`录取人数`、`专业组` | 专业序号、计划招数、2025 专业组结构没有稳定进入主流程 |
| `MajorGroupRow` 太薄 | 只有 `major_list`，没有 `MajorItem`、专业代码、计划数、专业历史线 | 不能生成 1-6 个专业志愿顺序 |
| Layer 1 和 Layer 2 混在一起 | `game_agent` 同时召回、算概率、打分、排序、组合 | 难以解释，也难以测试 |
| 调剂风险过粗 | 当前有 `adjustment_risk=0.15 if len(major_list)<6 else 0.05` 这类逻辑 | 专业数量不能代表尾部调剂风险 |
| 小计划逻辑有误导风险 | 曾用 `major_count <= 3` 近似小招生规模 | 专业数不是招生计划数 |
| 专业组 bundle 未拆解 | 只展示 `major_list[:6]` | 无法识别“计算机 + 土木/材料”的捆绑风险 |
| value gap 未实现 | 只有学校/专业规则分 | 无法发现省外低估、综合大学强专业低估 |
| Deep Research 粒度太粗 | 现在更像按用户问题做研究报告 | 没有给候选学校/专业生成 evidence card |
| Report 输出不是志愿表 | 报告推荐的是专业组，不是志愿表行 | 不贴近广东实际填报表 |
| Critic 不检查证据链 | 主要查保底概率、黑名单、硬规则 | 不会审计价值错位、捆绑风险、证据置信度 |

一句话记忆：

> 当前系统能推荐“哪些专业组值得看”，但还不能可靠回答“这一行志愿该怎么填”。

## 14.4 目标实现的最小闭环

目标不是一次性做完所有智能体，而是先形成最小可用闭环：

```text
UserProfile
-> DataAdapter
-> GroupRecall
-> GroupAdmissionRanker
-> MajorItemBuilder
-> BundleAnalyzer
-> MajorAssignmentPlanner
-> VolunteerSlotBuilder
-> SlateOptimizer
-> EvidenceEnricher
-> Critic
-> Report
```

最终输出：

```json
{
  "volunteer_index": 12,
  "school_code": "10008",
  "school_name": "北京科技大学",
  "major_group_code": "214",
  "major_codes": ["18", "19", "16", "14", "15", "11"],
  "major_names": ["计算机类", "通信工程", "自动化类", "机械类", "能源动力类", "储能科学与工程"],
  "obey_adjustment": "cautious",
  "group_admission_prob": 0.74,
  "major_satisfaction_prob": 0.52,
  "tail_major_risk": 0.47,
  "value_gap_score": 0.16,
  "bundle_type": "anchor_plus_drag_bundle",
  "evidence_cards": [],
  "explanation": "该组投档概率尚可，但组内含低偏好专业，不能作为低风险保底。"
}
```

一句话记忆：

> 最小闭环不是更复杂，而是让系统第一次输出可执行志愿行。

## 14.5 分阶段实现路线

### Step 1：数据适配层

目标：先让 2025 招生计划和历史数据统一成标准结构。

新增：

```text
backend/src/recommendation/schemas.py
backend/src/recommendation/data_adapter.py
```

要做：

```text
1. 定义 MajorItem、MajorGroupCandidate、VolunteerSlot、EvidenceCard。
2. 映射 2025 字段：
   专业名称 -> major_name
   专业序号 -> major_code
   计划招数 -> quota
   专业组代码 -> major_group_code
   2024_最低位次 -> historical_min_ranks[2024]
3. 映射 2021-2024 历史字段：
   专业/类 -> major_name
   专业组 -> major_group_code
   最低分平均排位 -> min_rank
   录取人数 -> quota
4. 按 school_code + school_name + subject_track + batch + major_group_code 聚合成专业组。
5. 每个专业组保留完整 major_items，而不是只保留 major_list。
```

验收：

```text
北京科技大学 214 专业组可以返回完整专业列表、专业序号、计划数、历年位次。
厦门大学 219 / 221 专业组可以区分本部和马来西亚分校备注。
```

一句话记忆：

> 先不要改推荐算法，先让数据结构能表达真实志愿表。

### Step 2：影子接入，不改变原推荐结果

目标：把 `MajorItem` 接进主流程，但先不改变排序。

修改：

```text
backend/src/models/game_matrix.py
backend/src/agents/game_agent.py
```

要做：

```text
1. `MajorGroupRow` 增加 `major_items`、`quota`、`group_quota`、`risk_reasons` 等字段。
2. `game_agent` 仍然用原来的 admission_prob / comprehensive_score 排序。
3. 但每个 row 同时携带完整专业组结构。
4. 保留原 `major_list`，保证前端和旧测试不崩。
```

验收：

```text
旧接口输出数量和冲稳保大体不变。
新增字段能在 debug/test 里看到。
```

一句话记忆：

> 第二步只加信息，不改决策，降低重构风险。

### Step 3：拆出 Layer 1

目标：把“能不能进组”从 `game_agent` 大函数里拆出来。

新增：

```text
backend/src/recommendation/group_recall.py
backend/src/recommendation/group_admission_ranker.py
```

要做：

```text
1. `group_recall.py` 负责候选专业组召回。
2. `group_admission_ranker.py` 负责 Monte Carlo / fallback probability。
3. 输出 `MajorGroupCandidate`。
4. `game_agent` 只负责调用和编排。
```

保留：

```text
现有 `GaokaoQuantEngine.search_major_groups`
现有 `monte_carlo_admission_probability`
现有 `calculate_admission_probability`
```

验收：

```text
同一个用户输入，Layer 1 输出的候选组和当前 game_agent 基本一致。
```

一句话记忆：

> Layer 1 只回答进组概率，不碰 6 个专业怎么填。

### Step 4：实现 Layer 2 的专业组拆包

目标：真正解决“进组以后去哪”。

新增：

```text
backend/src/recommendation/major_categorizer.py
backend/src/recommendation/bundle_analyzer.py
backend/src/recommendation/major_assignment_planner.py
backend/src/recommendation/adjustment_policy.py
```

可以复用：

```text
engines/major_assignment_predictor.py
engines/adjustment_sim.py
```

但要注意它们现在只是原型，不能直接当最终主逻辑。

要做：

```text
1. 为每个 MajorItem 打专业类别和用户偏好分。
2. 识别 bundle_type：
   pure_high_fit_bundle
   anchor_plus_drag_bundle
   hidden_value_bundle
   high_variance_bundle
3. 对组内专业排序，生成 1-6 个专业志愿。
4. 计算 tail_major_risk、blacklist_ratio、acceptable_major_ratio。
5. 判断 obey_adjustment：
   obey / cautious / not_recommended。
```

验收：

```text
含计算机+土木/材料的组，必须显示 anchor 和 drag。
黑名单专业多的组，不能作为低风险保底。
可接受专业不足 6 个时，不能硬说稳定。
```

一句话记忆：

> Layer 2 的核心不是调剂概率，而是最差结果是否能接受。

### Step 5：实现 value gap 和省内外机会识别

目标：把“低估机会”从经验判断变成特征。

新增：

```text
backend/src/recommendation/value_gap_features.py
backend/src/recommendation/geo_awareness_features.py
```

要做：

```text
1. 结构化部分先算：
   admission_price_score
   quota_scarcity
   historical_rank_trend
   crowding_risk_score
   school_tier_score
   major_quality_rule_score

2. LLM-first 部分按需补：
   省内/省外认知差异
   学校行业标签
   专业实际实力
   广东就业认可度
   城市产业机会
```

触发条件：

```text
省外 211 / 双一流 / 强双非一本
省外小计划
录取价格明显低于同层次同专业
专业组 bundle 风险或机会明显
用户明确关心学校实际价值
```

一句话记忆：

> 低估机会不是分低，而是分低且有真实价值证据。

### Step 6：候选级 Deep Research 与证据缓存

目标：让多个 agent 真正服务推荐，而不是只生成泛报告。

新增：

```text
backend/src/recommendation/evidence_enricher.py
backend/src/recommendation/feature_cache.py
backend/src/recommendation/verifier.py
```

Agent 分工：

```text
Candidate Scout：挑出值得调研的候选。
Deep Research Agent：查证学校、专业、就业、城市。
Geo-Awareness Agent：判断省内外认知差异。
Bundle Analyst：解释专业组捆绑。
Verifier：检查证据是否支撑分数。
Feature Cache：缓存 evidence cards。
```

规则：

```text
1. 大部分候选不触发 Deep Research。
2. 只对高价值、高不确定候选触发。
3. LLM 输出必须带 evidence card。
4. 排序使用 feature_value * confidence。
5. 证据不足只降低置信度，不强行推荐。
```

一句话记忆：

> Agent 不负责拍板，Agent 负责补证据。

### Step 7：生成 VolunteerSlot 和整张志愿表

目标：从“推荐专业组”升级为“生成志愿表行”。

新增：

```text
backend/src/recommendation/volunteer_slot_builder.py
backend/src/recommendation/volunteer_slate_optimizer.py
```

要做：

```text
1. 每个候选组生成 VolunteerSlot。
2. VolunteerSlot 包含：
   院校代码
   院校名称
   专业组代码
   1-6 个专业代码
   1-6 个专业名称
   是否服从调剂
   进组概率
   专业满意概率
   尾部专业风险
   证据卡
3. Slate Optimizer 组合多个 VolunteerSlot。
4. 支持参数化输出：
   demo_top_n = 10 / 30
   full_gaokao_slots = 45
```

一句话记忆：

> 最终产物不是推荐列表，而是志愿草表。

### Step 8：升级 Report 和 Critic

目标：报告和审计跟上两层推荐。

Report 必须展示：

```text
1. 每行志愿的进组概率。
2. 6 个专业排序原因。
3. 是否服从调剂及代价。
4. 专业组 bundle 类型。
5. 低估机会或高估风险。
6. 省内外认知差异。
7. evidence card 和 confidence。
```

Critic 必须检查：

```text
1. 是否把专业组误说成单专业。
2. 保底是否同时满足高进组概率和低尾部风险。
3. 是否隐藏黑名单专业。
4. 是否把省外低分误判为捡漏。
5. 是否把省内高认知误判为高价值。
6. LLM 证据是否支撑 value_gap。
7. 服从调剂建议是否与组内专业结构一致。
```

一句话记忆：

> Report 负责讲清楚，Critic 负责防止讲过头。

### Step 9：评测和回归

目标：每改一步都有可验证结果。

新增：

```text
backend/src/recommendation/tests/
backend/scripts/evaluate_two_layer_recommendation.py
```

最小测试集：

```text
1. 北京科技大学 214：混搭组，必须识别 anchor+drag。
2. 厦门大学 219：本部计算机类，检查 value gap。
3. 厦门大学 221：马来西亚分校，必须识别校区/收费/英文授课备注。
4. 省外小计划 211：只能进入机会池，不能直接当保底。
5. 用户黑名单土木/材料：含这些专业的组必须提高 tail risk。
6. 保底志愿：必须同时高进组概率和低专业尾部风险。
```

一句话记忆：

> 没有测试的“智能推荐”，面试里讲不硬。

## 14.6 推荐实施顺序

实际开发不要从 Agent 开始，而要按这个顺序：

```text
1. schemas.py
2. data_adapter.py
3. MajorGroupRow 扩字段，影子接入
4. group_recall.py / group_admission_ranker.py
5. bundle_analyzer.py / major_assignment_planner.py
6. volunteer_slot_builder.py
7. value_gap_features.py
8. evidence_enricher.py / feature_cache.py / verifier.py
9. volunteer_slate_optimizer.py
10. report_agent.py / critic_agent.py 升级
11. evaluation harness
```

原因：

```text
先数据结构，再算法拆分，再 LLM 证据，再报告审计。
```

一句话记忆：

> 先让系统说清楚真实对象，再让系统变聪明。

## 14.7 面试表达

推荐说法：

> 目前实现已经有 FastAPI、LangGraph、画像抽取、专业组召回、Monte Carlo 录取概率、Pareto 筛选、Runtime RL 配比、组合优化、Report 和 Critic。问题是推荐核心还集中在一个 GameAgent 里，输出对象仍然是专业组，不是广东真实志愿表行。下一步我会按两层重构：第一层专业组投档概率，第二层组内专业排序和调剂风险；再加一个 LLM-first 的证据增强层，只对省外低估、捆绑招生、高不确定候选触发 Deep Research，输出 evidence cards 和 confidence，最后由 Critic 检查证据是否支撑推荐。

一句话记忆：

> 现在系统能推荐专业组，下一版要能生成带证据和风险解释的志愿表行。
