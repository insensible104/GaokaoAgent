import React, { useMemo, useState } from "react";
import { buildDeliveryReviewRecord } from "../lib/deliveryReviewRecord";
import type { GameMatrix, RecommendationProfileSummary } from "./GameMatrixView";

interface DeliveryReviewRecordProps {
  gameMatrix: GameMatrix;
  userProfile?: RecommendationProfileSummary | null;
  reportReady?: boolean;
  externalPlanCompared?: boolean;
}

const statusLabels = {
  ready: "可交付",
  needs_review: "待复核",
  blocked: "阻断",
};

export const DeliveryReviewRecord: React.FC<DeliveryReviewRecordProps> = ({
  gameMatrix,
  userProfile,
  reportReady = false,
  externalPlanCompared = false,
}) => {
  const [copied, setCopied] = useState(false);
  const record = useMemo(
    () =>
      buildDeliveryReviewRecord({
        gameMatrix,
        userProfile,
        reportReady,
        externalPlanCompared,
      }),
    [externalPlanCompared, gameMatrix, reportReady, userProfile],
  );

  const copyRecord = async () => {
    try {
      await navigator.clipboard.writeText(record.copyText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">交付复核记录</h3>
          <p className="mt-1 text-sm text-gray-600">
            版本快照用于交接当前复核状态，保留阻断项、待复核项、下一步动作和证据边界。
          </p>
        </div>
        <button
          type="button"
          onClick={copyRecord}
          className="rounded-md bg-gray-900 px-3 py-2 text-sm font-semibold text-white hover:bg-gray-800"
        >
          {copied ? "已复制" : "复制记录"}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <RecordMetric label="版本快照" value={record.versionStamp} />
        <RecordMetric label="复核记录" value={statusLabels[record.status]} />
        <RecordMetric label="阻断项" value={record.metrics.blocked_items.toString()} />
        <RecordMetric label="待复核项" value={record.metrics.review_items.toString()} />
      </div>

      <div className="mt-4 rounded-md bg-gray-50 p-4">
        <div className="text-sm font-semibold text-gray-900">下一步动作</div>
        <p className="mt-1 text-sm leading-6 text-gray-700">{record.leadAction}</p>
      </div>

      <textarea
        readOnly
        value={record.copyText}
        className="mt-4 min-h-56 w-full resize-y rounded-md border border-gray-300 bg-white px-3 py-2 font-mono text-xs leading-5 text-gray-800"
        aria-label="交付复核记录文本"
      />

      <p className="mt-3 text-xs leading-5 text-gray-500">证据边界：{record.claimBoundary}</p>
    </section>
  );
};

interface RecordMetricProps {
  label: string;
  value: string;
}

const RecordMetric: React.FC<RecordMetricProps> = ({ label, value }) => (
  <div className="rounded-md bg-gray-50 px-3 py-3">
    <div className="text-xs font-semibold text-gray-500">{label}</div>
    <div className="mt-1 break-words text-sm font-bold text-gray-900">{value}</div>
  </div>
);
