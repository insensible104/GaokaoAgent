import type {
  WebEvidenceAdapterResult,
  WebEvidenceSearchAdapterRequest,
} from "./webEvidenceSearchAdapter";
import type { WebEvidenceSearchProvider } from "./webEvidenceSearchProvider";
import type { WebEvidenceSourceTier } from "./webEvidencePlanner";

export interface RawWebSearchDocument {
  title: string;
  url: string;
  snippet: string;
}

export interface WebEvidenceSearchSnapshotProviderInput {
  id: string;
  documents: RawWebSearchDocument[];
}

interface ScoredDocument {
  document: RawWebSearchDocument;
  score: number;
  hostMatches: boolean;
}

const SOCIAL_HOST_HINTS = ["zhihu.com", "xiaohongshu.com", "weibo.com", "douyin.com", "bilibili.com"];
const OFFICIAL_HOST_HINTS = [".gov.cn", ".edu.cn", "eea."];

export function createWebEvidenceSearchSnapshotProvider({
  id,
  documents,
}: WebEvidenceSearchSnapshotProviderInput): WebEvidenceSearchProvider {
  return {
    id,
    search: async (request) => searchSnapshotDocuments({ request, documents }),
  };
}

function searchSnapshotDocuments({
  request,
  documents,
}: {
  request: WebEvidenceSearchAdapterRequest;
  documents: RawWebSearchDocument[];
}): WebEvidenceAdapterResult[] {
  return documents
    .map((document) => scoreDocument(request, document))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, request.maxResults)
    .map((item) => toAdapterResult(request, item));
}

function scoreDocument(
  request: WebEvidenceSearchAdapterRequest,
  document: RawWebSearchDocument,
): ScoredDocument {
  const text = `${document.title} ${document.snippet}`.toLowerCase();
  const tokens = queryTokens(request.query);
  const tokenMatches = tokens.filter((token) => text.includes(token)).length;
  const host = hostOf(document.url);
  const hostMatches = request.domains.some((domain) => hostMatchesDomain(host, domain));
  const socialMatch = request.sourceTier === "public_opinion" && isSocialHost(host);
  const score = tokenMatches + (hostMatches ? 8 : 0) + (socialMatch ? 4 : 0);
  return {
    document,
    score,
    hostMatches,
  };
}

function toAdapterResult(
  request: WebEvidenceSearchAdapterRequest,
  item: ScoredDocument,
): WebEvidenceAdapterResult {
  const sourceTier = inferSourceTier({
    requestedTier: request.sourceTier,
    host: hostOf(item.document.url),
    hostMatches: item.hostMatches,
  });
  return {
    title: item.document.title,
    url: item.document.url,
    snippet: item.document.snippet,
    sourceTier,
    excerpts: [item.document.snippet],
    claimedSupports: request.allowedClaims,
  };
}

function inferSourceTier({
  requestedTier,
  host,
  hostMatches,
}: {
  requestedTier: WebEvidenceSourceTier;
  host: string;
  hostMatches: boolean;
}): WebEvidenceSourceTier {
  if (requestedTier === "public_opinion") {
    return "public_opinion";
  }
  if (hostMatches) {
    return requestedTier;
  }
  if (isSocialHost(host)) {
    return "public_opinion";
  }
  if (isOfficialHost(host)) {
    return "official";
  }
  return "public_opinion";
}

function queryTokens(query: string): string[] {
  return Array.from(new Set(
    query
      .toLowerCase()
      .split(/[^a-z0-9\u4e00-\u9fa5]+/)
      .map((token) => token.trim())
      .filter((token) => token.length >= 3),
  ));
}

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.toLowerCase().replace(/^www\./, "");
  } catch {
    return "";
  }
}

function hostMatchesDomain(host: string, domain: string): boolean {
  const normalized = domain.toLowerCase().replace(/^www\./, "");
  return host === normalized || host.endsWith(`.${normalized}`);
}

function isSocialHost(host: string): boolean {
  return SOCIAL_HOST_HINTS.some((hint) => hostMatchesDomain(host, hint));
}

function isOfficialHost(host: string): boolean {
  return OFFICIAL_HOST_HINTS.some((hint) => host.includes(hint));
}
