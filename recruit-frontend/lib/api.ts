import {
  ApiError,
  type ApiErrorResponse,
  type GenerateContentResponse,
  type JobCreatePayload,
  type JobResponse,
  type LeadCreatePayload,
  type LeadCreateResponse,
  type LeadDetailResponse,
  type LeadListResponse,
  type PublicJobLanding,
  type ScreeningCompletePayload,
  type ScreeningCompleteResponse,
  type ScreeningTurnPayload,
  type ScreeningTurnResponse,
} from "@/types/api";

/**
 * Typed fetch wrapper for the Phase 2 FastAPI backend.
 *
 * Usage:
 *   const job = await api.getPublicJob(trackingId);
 *   const lead = await api.createLead({...});
 *
 * Every error becomes ApiError with Vietnamese `.message` ready for UI.
 */

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type Method = "GET" | "POST" | "PATCH" | "DELETE";

interface RequestOptions {
  method?: Method;
  body?: unknown;
  headers?: Record<string, string>;
  cache?: RequestCache;
  next?: { revalidate?: number; tags?: string[] };
  signal?: AbortSignal;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const url = `${BASE}${path}`;
  const init: RequestInit = {
    method: opts.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(opts.headers ?? {}),
    },
    cache: opts.cache,
    // Next.js `next` field is a Next-specific extension; cast at use site
    ...(opts.next ? ({ next: opts.next } as RequestInit) : {}),
  };
  if (opts.body !== undefined) init.body = JSON.stringify(opts.body);
  if (opts.signal) init.signal = opts.signal;

  let res: Response;
  try {
    res = await fetch(url, init);
  } catch {
    throw new ApiError(
      {
        code: "NETWORK_ERROR",
        message: "Mất kết nối mạng. Anh/chị kiểm tra 3G/4G giúp em ạ.",
        request_id: "req_network",
      },
      0
    );
  }

  if (!res.ok) {
    let payload: ApiErrorResponse | null = null;
    try {
      payload = (await res.json()) as ApiErrorResponse;
    } catch {
      // non-JSON error
    }
    if (payload?.error) {
      throw new ApiError(payload.error, res.status);
    }
    throw new ApiError(
      {
        code: "INTERNAL_ERROR",
        message: "Đã có lỗi xảy ra. Vui lòng thử lại.",
        request_id: "req_unknown",
      },
      res.status
    );
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  // Candidate flow
  async getPublicJob(trackingId: string): Promise<PublicJobLanding> {
    return request<PublicJobLanding>(`/v1/j/${encodeURIComponent(trackingId)}`, {
      cache: "no-store",
    });
  },

  async createLead(payload: LeadCreatePayload): Promise<LeadCreateResponse> {
    return request<LeadCreateResponse>(`/v1/leads`, { method: "POST", body: payload });
  },

  async sendScreeningTurn(payload: ScreeningTurnPayload): Promise<ScreeningTurnResponse> {
    return request<ScreeningTurnResponse>(`/v1/screening/message`, {
      method: "POST",
      body: payload,
    });
  },

  async completeScreening(
    payload: ScreeningCompletePayload
  ): Promise<ScreeningCompleteResponse> {
    return request<ScreeningCompleteResponse>(`/v1/screening/complete`, {
      method: "POST",
      body: payload,
    });
  },

  // HR flow — requires bearer auth; caller supplies in headers
  async createJob(
    payload: JobCreatePayload,
    token: string
  ): Promise<JobResponse> {
    return request<JobResponse>(`/v1/hr/jobs`, {
      method: "POST",
      body: payload,
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  async generateContent(
    jobId: string,
    token: string
  ): Promise<GenerateContentResponse> {
    return request<GenerateContentResponse>(
      `/v1/hr/jobs/${encodeURIComponent(jobId)}/generate-content`,
      {
        method: "POST",
        body: {},
        headers: { Authorization: `Bearer ${token}` },
      }
    );
  },

  async listLeads(
    token: string,
    opts: { tier?: string; job_id?: string; limit?: number } = {}
  ): Promise<LeadListResponse> {
    const qs = new URLSearchParams();
    if (opts.tier) qs.set("tier", opts.tier);
    if (opts.job_id) qs.set("job_id", opts.job_id);
    qs.set("limit", String(opts.limit ?? 50));
    return request<LeadListResponse>(`/v1/hr/leads?${qs.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
  },

  async getLead(leadId: string, token: string): Promise<LeadDetailResponse> {
    return request<LeadDetailResponse>(
      `/v1/hr/leads/${encodeURIComponent(leadId)}`,
      {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      }
    );
  },
};

export { ApiError };
