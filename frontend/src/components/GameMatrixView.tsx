/**
 * Game Matrix View - 专业组级别的志愿推荐展示
 * 广东省新高考规则：45个专业组，每组6个专业
 *
 * 修复P2-4: 添加React.memo和useCallback优化性能
 */
import React, { useState, useMemo, useCallback } from 'react';

export interface MajorGroupRow {
  school_name: string;
  major_group_code: string;
  major_list: string[];  // 该专业组包含的所有专业
  major_count: number;
  admission_prob: number;
  min_rank_pred: number;
  rank_ci_lower: number;
  rank_ci_upper: number;
  fear_index: number;
  volatility: 'low' | 'medium' | 'high';
  adjustment_risk: number;
  worst_case_major: string | null;
  is_blacklist_risk: boolean;
  strategy_tag: 'rush' | 'target' | 'safe';
  sentiment_score: number;
  news_summary: string | null;
  is_selected: boolean;
}

export interface GameMatrix {
  major_group_rows: MajorGroupRow[];  // 专业组推荐
  rows: unknown[];  // 旧的单专业模型（保留兼容性）
  total_rush: number;
  total_target: number;
  total_safe: number;
  expected_utility: number;
  portfolio_risk: number;
  is_balanced: boolean;
  agentic_rl_used?: boolean;
  selection_method?: string;
  optimization_summary?: {
    checkpoint_loaded?: boolean;
    policy_source?: string;
    mix?: {
      rush?: number;
      target?: number;
      safe?: number;
      total?: number;
    };
    effective_params?: {
      risk_tolerance?: number;
      diversity_weight?: number;
      prestige_weight?: number;
    };
    portfolio?: {
      generated?: boolean;
      style_name?: string;
      style_description?: string;
      admission_guarantee?: number;
      avg_admission_prob?: number;
    };
  } | null;
}

interface GameMatrixViewProps {
  gameMatrix: GameMatrix;
}

const strategyColors = {
  rush: {
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    text: 'text-orange-700',
    badge: 'bg-orange-100 text-orange-800',
    label: '冲刺'
  },
  target: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-700',
    badge: 'bg-blue-100 text-blue-800',
    label: '稳妥'
  },
  safe: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-700',
    badge: 'bg-green-100 text-green-800',
    label: '保底'
  }
};

const volatilityLabels = {
  low: '低波动',
  medium: '中波动',
  high: '高波动'
};

// 修复P2-4: 使用React.memo避免不必要的重渲染
const GameMatrixViewComponent: React.FC<GameMatrixViewProps> = ({ gameMatrix }) => {
  const [selectedStrategy, setSelectedStrategy] = useState<'all' | 'rush' | 'target' | 'safe'>('all');
  const [sortBy, setSortBy] = useState<'prob' | 'rank'>('prob');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // 使用专业组数据
  const dataSource = useMemo(
    () => gameMatrix.major_group_rows && gameMatrix.major_group_rows.length > 0
      ? gameMatrix.major_group_rows
      : [],
    [gameMatrix.major_group_rows]
  );
  const optimizationSummary = gameMatrix.optimization_summary;
  const portfolioSummary = optimizationSummary?.portfolio;

  // Filter and sort logic
  const filteredAndSortedRows = useMemo(() => {
    let filtered = dataSource;

    // Filter by strategy
    if (selectedStrategy !== 'all') {
      filtered = filtered.filter(row => row.strategy_tag === selectedStrategy);
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'prob') {
        comparison = a.admission_prob - b.admission_prob;
      } else {
        comparison = a.min_rank_pred - b.min_rank_pred;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return sorted;
  }, [dataSource, selectedStrategy, sortBy, sortOrder]);

  // 修复P2-4: 使用useCallback缓存回调函数
  const toggleExpand = useCallback((groupKey: string) => {
    setExpandedGroups(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(groupKey)) {
        newExpanded.delete(groupKey);
      } else {
        newExpanded.add(groupKey);
      }
      return newExpanded;
    });
  }, []);

  if (dataSource.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <p className="text-gray-600">暂无专业组推荐数据</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Statistics Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">专业组推荐总览</h3>
        <p className="text-sm text-gray-600 mb-4">
          广东省新高考规则：45个专业组，每组6个专业。推荐30个专业组供您选择。
        </p>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Total count */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">推荐总数</div>
            <div className="text-2xl font-bold text-gray-900">{dataSource.length}</div>
          </div>

          {/* Rush */}
          <div className="bg-orange-50 rounded-lg p-4">
            <div className="text-sm text-orange-600 mb-1">冲刺</div>
            <div className="text-2xl font-bold text-orange-700">{gameMatrix.total_rush}</div>
          </div>

          {/* Target */}
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-sm text-blue-600 mb-1">稳妥</div>
            <div className="text-2xl font-bold text-blue-700">{gameMatrix.total_target}</div>
          </div>

          {/* Safe */}
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-sm text-green-600 mb-1">保底</div>
            <div className="text-2xl font-bold text-green-700">{gameMatrix.total_safe}</div>
          </div>

          {/* Balance indicator */}
          <div className={`rounded-lg p-4 ${gameMatrix.is_balanced ? 'bg-green-50' : 'bg-yellow-50'}`}>
            <div className="text-sm text-gray-600 mb-1">策略平衡</div>
            <div className={`text-lg font-semibold ${gameMatrix.is_balanced ? 'text-green-700' : 'text-yellow-700'}`}>
              {gameMatrix.is_balanced ? '✓ 均衡' : '⚠ 待优化'}
            </div>
          </div>
        </div>
      </div>

      {optimizationSummary && (
        <div className="bg-slate-900 text-slate-50 rounded-lg shadow-md p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h4 className="text-lg font-semibold">Agentic RL 运行时策略</h4>
              <p className="text-sm text-slate-300 mt-1">
                {gameMatrix.agentic_rl_used ? '已加载学习到的checkpoint' : '未加载checkpoint，当前使用启发式回退'}
              </p>
            </div>
            <div className="text-sm text-slate-300">
              {gameMatrix.selection_method || 'pareto+runtime_rl'}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <div className="rounded-lg bg-slate-800 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">冲稳保配比</div>
              <div className="text-sm text-slate-100">
                冲刺 {optimizationSummary.mix?.rush ?? '-'} / 稳妥 {optimizationSummary.mix?.target ?? '-'} / 保底 {optimizationSummary.mix?.safe ?? '-'}
              </div>
            </div>

            <div className="rounded-lg bg-slate-800 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">策略参数</div>
              <div className="text-sm text-slate-100">
                风险 {optimizationSummary.effective_params?.risk_tolerance ?? '-'} / 多样性 {optimizationSummary.effective_params?.diversity_weight ?? '-'} / 院校权重 {optimizationSummary.effective_params?.prestige_weight ?? '-'}
              </div>
            </div>

            <div className="rounded-lg bg-slate-800 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">组合优化</div>
              <div className="text-sm text-slate-100">
                {portfolioSummary?.generated
                  ? `${portfolioSummary.style_name ?? '已生成组合'} · 保底成功率 ${Math.round((portfolioSummary.admission_guarantee ?? 0) * 100)}%`
                  : '候选不足，未生成最终志愿组合'}
              </div>
              {portfolioSummary?.style_description && (
                <p className="text-xs text-slate-400 mt-2">{portfolioSummary.style_description}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Filters and Controls */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Strategy filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">筛选:</label>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedStrategy('all')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  selectedStrategy === 'all'
                    ? 'bg-gray-800 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                全部
              </button>
              {(['rush', 'target', 'safe'] as const).map(strategy => (
                <button
                  key={strategy}
                  onClick={() => setSelectedStrategy(strategy)}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    selectedStrategy === strategy
                      ? strategyColors[strategy].badge
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {strategyColors[strategy].label}
                </button>
              ))}
            </div>
          </div>

          {/* Sort controls */}
          <div className="flex items-center gap-2 ml-auto">
            <label className="text-sm font-medium text-gray-700">排序:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'prob' | 'rank')}
              className="px-3 py-1 rounded-md border border-gray-300 text-sm"
            >
              <option value="prob">录取概率</option>
              <option value="rank">预测位次</option>
            </select>
            <button
              onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
              className="px-3 py-1 rounded-md bg-gray-100 hover:bg-gray-200 text-sm font-medium"
            >
              {sortOrder === 'asc' ? '↑ 升序' : '↓ 降序'}
            </button>
          </div>
        </div>

        <div className="mt-2 text-sm text-gray-600">
          显示 {filteredAndSortedRows.length} 个专业组
        </div>
      </div>

      {/* Major Group Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAndSortedRows.map((row, index) => {
          const colors = strategyColors[row.strategy_tag];
          const groupKey = `${row.school_name}-${row.major_group_code}`;
          const isExpanded = expandedGroups.has(groupKey);

          return (
            <div
              key={index}
              className={`${colors.bg} border-2 ${colors.border} rounded-lg p-5 hover:shadow-lg transition-all`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-gray-900 text-lg truncate">{row.school_name}</h4>
                  <p className="text-sm text-gray-600 mt-1">专业组 {row.major_group_code}</p>
                  <p className="text-xs text-gray-500 mt-1">{row.major_count} 个专业</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${colors.badge} ml-2 flex-shrink-0`}>
                  {colors.label}
                </span>
              </div>

              {/* Main metrics */}
              <div className="space-y-2 mb-3">
                {/* Admission probability */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-600">录取概率</span>
                    <span className={`text-lg font-bold ${colors.text}`}>
                      {(row.admission_prob * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        row.strategy_tag === 'rush'
                          ? 'bg-orange-500'
                          : row.strategy_tag === 'target'
                          ? 'bg-blue-500'
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${row.admission_prob * 100}%` }}
                    />
                  </div>
                </div>

                {/* Predicted rank */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">预测位次</span>
                  <span className="text-sm font-semibold text-gray-900">{row.min_rank_pred.toLocaleString()}</span>
                </div>

                {/* Rank confidence interval */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">位次区间</span>
                  <span className="text-xs text-gray-500">
                    {row.rank_ci_lower.toLocaleString()} - {row.rank_ci_upper.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Major List (Expandable) */}
              <div className="pt-3 border-t border-gray-200">
                <button
                  onClick={() => toggleExpand(groupKey)}
                  className="w-full text-left flex justify-between items-center text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  <span>包含专业 ({row.major_count}个)</span>
                  <span className="text-xl">{isExpanded ? '−' : '+'}</span>
                </button>

                {isExpanded && (
                  <div className="mt-2 space-y-1">
                    {row.major_list.map((major, idx) => (
                      <div key={idx} className="text-xs text-gray-600 pl-2 py-1 bg-white bg-opacity-50 rounded">
                        {idx + 1}. {major}
                      </div>
                    ))}
                    {row.major_count > row.major_list.length && (
                      <div className="text-xs text-gray-500 italic pl-2">
                        ...还有 {row.major_count - row.major_list.length} 个专业
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Additional info */}
              <div className="pt-3 border-t border-gray-200 mt-3 space-y-1">
                {/* Volatility */}
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">波动性</span>
                  <span className="text-xs text-gray-700">{volatilityLabels[row.volatility]}</span>
                </div>

                {/* Adjustment risk */}
                {row.adjustment_risk > 0.1 && (
                  <div className="flex items-center gap-1 text-xs">
                    <span className="text-yellow-600">⚠</span>
                    <span className="text-gray-700">调剂风险: {(row.adjustment_risk * 100).toFixed(0)}%</span>
                  </div>
                )}

                {/* Blacklist warning */}
                {row.is_blacklist_risk && (
                  <div className="flex items-center gap-1 text-xs text-red-600 font-medium">
                    <span>🚫</span>
                    <span>可能调剂到: {row.worst_case_major || '不喜欢的专业'}</span>
                  </div>
                )}

                {/* News summary */}
                {row.news_summary && (
                  <div className="mt-2 text-xs text-gray-600 italic">
                    💡 {row.news_summary}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {filteredAndSortedRows.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow-md">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="mt-2 text-gray-600">当前筛选条件下没有专业组</p>
        </div>
      )}
    </div>
  );
};

// 修复P2-4: 使用React.memo包装组件，仅在props变化时重新渲染
export const GameMatrixView = React.memo(GameMatrixViewComponent);
