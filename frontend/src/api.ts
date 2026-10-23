export type Source = {
  id: number;
  title: string;
  url: string;
  language: string;
  collected_at: string;
  synthetic: boolean;
};
export type Health = {
  status: string;
  synthetic: boolean;
  inference_configured: boolean;
  retrieval: string;
};
export type Event = { kind: string; data: Record<string, unknown> };
const BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

export async function waitForBackend(
  signal: AbortSignal,
  notify: () => void,
  budget = 90000,
): Promise<Health> {
  const deadline = Date.now() + budget;
  while (Date.now() < deadline) {
    signal.throwIfAborted();
    try {
      const remaining = Math.max(1, Math.min(10000, deadline - Date.now()));
      const response = await fetch(`${BASE}/healthz`, {
        signal: AbortSignal.any([signal, AbortSignal.timeout(remaining)]),
      });
      if (response.ok) return (await response.json()) as Health;
    } catch {
      signal.throwIfAborted();
    }
    notify();
    const delay = Math.min(2500, Math.max(0, deadline - Date.now()));
    await new Promise<void>((resolve, reject) => {
      const cleanup = () => signal.removeEventListener("abort", abort);
      const timer = setTimeout(() => {
        cleanup();
        resolve();
      }, delay);
      const abort = () => {
        clearTimeout(timer);
        cleanup();
        reject(signal.reason);
      };
      signal.addEventListener("abort", abort, { once: true });
    });
  }
  throw new Error("wake_timeout");
}

export function parseEvent(frame: string): Event | null {
  const lines = frame.split("\n");
  const kind = lines
    .find((line) => line.startsWith("event:"))
    ?.slice(6)
    .trim();
  const raw = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n");
  if (!kind || !raw) return null;
  return { kind, data: JSON.parse(raw) as Record<string, unknown> };
}

export async function streamChat(
  body: unknown,
  signal: AbortSignal,
  receive: (event: Event) => void,
) {
  const response = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    if (response.status === 429) throw new Error("rate_limit");
    throw new Error("request_failed");
  }
  if (!response.body) throw new Error("no_stream");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "",
    finished = false;
  try {
    while (true) {
      const part = await reader.read();
      if (part.done) break;
      buffer += decoder
        .decode(part.value, { stream: true })
        .replace(/\r\n/g, "\n");
      let boundary: number;
      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        const parsed = parseEvent(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        if (!parsed) continue;
        if (parsed.kind === "error") throw new Error(String(parsed.data.code));
        if (parsed.kind === "done") finished = true;
        receive(parsed);
      }
    }
    if (!finished) throw new Error("interrupted");
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

export async function fetchSources(signal: AbortSignal): Promise<Source[]> {
  const response = await fetch(`${BASE}/api/sources`, { signal });
  if (!response.ok) throw new Error("sources_failed");
  return ((await response.json()) as { sources: Source[] }).sources;
}
