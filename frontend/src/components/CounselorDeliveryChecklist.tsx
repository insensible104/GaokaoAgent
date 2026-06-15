import React, { useMemo } from "react";
import {
  buildCounselorDeliveryChecklist,
  type CounselorChecklistOwner,
  type CounselorChecklistStatus,
} from "../lib/counselorDeliveryChecklist";
import type { GameMatrix, RecommendationProfileSummary } from "./GameMatrixView";

interface CounselorDeliveryChecklistProps {
  gameMatrix: GameMatrix;
  userProfile?: RecommendationProfileSummary | null;
  reportReady?: boolean;
  externalPlanCompared?: boolean;
}

const statusLabels: Record<CounselorChecklistStatus, string> = {
  ready: "可交付",
  needs_review: "待复核",
  blocked: "阻断",
};

const statusStyles: Record<CounselorChecklistStatus, string> = {
  ready: "border-emerald-200 bg-emerald-50 text-emerald-900",
  needs_review: "border-amber-200 bg-amber-50 text-amber-900",
  blocked: "border-red-200 bg-red-50 text-red-900",
};

const ownerLabels: Record<CounselorChecklistOwner, string> = {
  counselor: "顾问",
  student_family: "家庭",
  data_update: "数据更新",
};

export const CounselorDeliveryChecklist: React.FC<CounselorDeliveryChecklistProps> = ({
  gameMatrix,
  userProfile,
  reportReady = false,
  externalPlanCompared = false,
}) => {
  const checklist = useMemo(
    () =>
      buildCounselorDeliveryChecklist({
        gameMatrix,
        userProfile,
        reportReady,
        externalPlanCompared,
      }),
    [externalPlanCompared, gameMatrix, reportReady, userProfile],
  );

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">顾问交付清单</h3>
          <p className="mt-1 text-sm text-gray-600">
            1 分钟交付判断：先看阻断项，再处理复核项，最后进入报告交付包。
          </p>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusStyles[checklist.status]}`}>
          {statusLabels[checklist.status]}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="min-w-0 rounded-md bg-gray-50 p-4">
          <div className="text-sm font-semibold text-gray-900">下一步动作</div>
          <p className="mt-2 text-sm leading-6 text-gray-700">{checklist.leadAction}</p>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center">
            <CountTile label="阻断项" value={checklist.blockedCount} tone="text-red-700" />
            <CountTile label="复核项" value={checklist.reviewCount} tone="text-amber-700" />
            <CountTile label="已就绪" value={checklist.readyCount} tone="text-emerald-700" />
          </div>
          <p className="mt-4 border-t border-gray-200 pt-3 text-xs leading-5 text-gray-500">
            交付口径：{checklist.claimBoundary}
          </p>
        </div>

        <div className="min-w-0 space-y-2">
          {checklist.items.map((item) => (
            <div key={item.id} className={`rounded-md border px-3 py-3 ${statusStyles[item.status]}`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-sm font-semibold">{item.label}</div>
                <div className="flex items-center gap-2 text-xs font-semibold">
                  <span>{ownerLabels[item.owner]}</span>
                  <span>{statusLabels[item.status]}</span>
                </div>
              </div>
              <p className="mt-1 text-xs leading-5">{item.evidence}</p>
              <p className="mt-2 text-xs font-semibold">动作：{item.action}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 rounded-md border border-indigo-100 bg-indigo-50 px-3 py-3 text-sm text-indigo-950">
        千问/老师方案不是竞争噪音，而是顾问复核输入；粘贴到下方外部方案审计器后，未匹配条目应进入人工复核记录。
      </div>
    </section>
  );
};

interface CountTileProps {
  label: string;
  value: number;
  tone: string;
}

const CountTile: React.FC<CountTileProps> = ({ label, value, tone }) => (
  <div className="rounded bg-white px-2 py-2">
    <div className="text-xs text-gray-500">{label}</div>
    <div className={`mt-1 text-xl font-bold ${tone}`}>{value}</div>
  </div>
);
