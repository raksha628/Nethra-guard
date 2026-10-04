export const API_BASE_URL = 'http://127.0.0.1:8000';

async function fetchWithErr(url: string, options?: RequestInit) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const body = await res.json();
      if (body.detail) msg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch (e) {}
    throw new Error(`API Error ${res.status}: ${msg}`);
  }
  return res.json();
}

export const api = {
  getDemoWorkspace: () => fetchWithErr(`${API_BASE_URL}/api/demo/workspace`),
  createRun: (data: any) => fetchWithErr(`${API_BASE_URL}/api/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  getRuns: () => fetchWithErr(`${API_BASE_URL}/api/runs`),
  getRun: (runId: string) => fetchWithErr(`${API_BASE_URL}/api/runs/${runId}`),
  getFindings: (runId: string) => fetchWithErr(`${API_BASE_URL}/api/runs/${runId}/findings`),
  getEvidence: (runId: string) => fetchWithErr(`${API_BASE_URL}/api/runs/${runId}/evidence`),
  getComparison: (runId: string, baselineId: string) => fetchWithErr(`${API_BASE_URL}/api/runs/${runId}/compare?baseline_run_id=${baselineId}`),
  getLedger: () => fetchWithErr(`${API_BASE_URL}/api/ledger`),
  verifyLedger: () => fetchWithErr(`${API_BASE_URL}/api/ledger/verify`, { method: 'POST' })
};