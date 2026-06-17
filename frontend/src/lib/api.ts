const trimTrailingSlash = (value: string) => value.replace(/\/+$/, "");

export function getApiBaseUrl() {
  const configured = import.meta.env.VITE_API_URL?.trim();
  if (configured) return trimTrailingSlash(configured);
  if (import.meta.env.DEV) return "http://localhost:8000";
  return "";
}

export function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}
