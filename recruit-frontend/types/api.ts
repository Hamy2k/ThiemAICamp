/**
 * Types matching Phase 1 API contract.
 * Do NOT modify to match backend — if backend drifts, flag with API_MISMATCH.
 */

// ─── Error envelope ───

export interface ApiErrorDetail {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
  request_id: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export class ApiError extends Error {
  readonly code: string;
  readonly field: string | undefined;
  readonly details: Record<string, unknown> | undefined;
  readonly requestId: string;
  readonly status: number;

  constructor(payload: ApiErrorDetail, status: number) {
    super(payload.message);
    this.code = payload.code;
    this.field = payload.field;
    this.details = payload.details;
    this.requestId = payload.request_id;
    this.status = status;
  }
}

// ─── Public landing (GET /v1/j/:tracking_id) ───

export interface PublicJobLanding {
  tracking_id: string;
  title: string;
  salary_text: string | null;
  location_short: string;
  start_date: string | null;
  copy_vietnamese: string;
  apply_cta: string;
}

// ─── Lead create (POST /v1/leads) ───

export interface LeadCreatePayload {
  tracking_id: string | null;
  full_name: string;
  phone: string;
  area_raw: string | null;
  consent: { version: string; accepted: boolean };
}

export interface NormalizedLeadInfo {
  phone_e164: string;
  area_normalized: string | null;
  distance_km: number | null;
}

export interface LeadCreateResponse {
  lead_id: string;
  session_id: string;
  normalized: NormalizedLeadInfo;
  first_ai_message: string;
}

// ─── Screening (POST /v1/screening/message) ───

export interface ShiftAvailability {
  day?: boolean;
  night?: boolean;
  rotating?: boolean;
  preferred?: "day" | "night" | "rotating" | "any";
}

export interface ExperienceInfo {
  has_experience?: boolean;
  years?: number | null;
  related_keywords?: string[];
  willing_to_learn?: boolean;
}

export interface ExtractedDelta {
  start_date?: string | null;
  shift_availability?: ShiftAvailability;
  experience?: ExperienceInfo;
  questions_from_candidate?: string[];
  normalized_location?: { district: string; city: string };
  hours_per_day?: number | null;
  prefers_proximity?: boolean;
}

export interface ScreeningTurnPayload {
  session_id: string;
  message: string;
}

export interface ScreeningTurnResponse {
  turn_index: number;
  reply: string;
  extracted_delta: ExtractedDelta;
  turns_remaining: number;
  done: boolean;
}

export interface ScreeningCompletePayload {
  session_id: string;
}

export interface ScoreBreakdown {
  location: number;
  availability: number;
  experience: number;
  response_quality: number;
}

export interface ScreeningCompleteResponse {
  match_id: string;
  score_total: number;
  score_breakdown: ScoreBreakdown;
  tier: "hot" | "warm" | "cold";
  explanation_vi: string;
  thank_you_message: string;
  fallback_used?: boolean;
}

// ─── HR (POST /v1/hr/jobs) ───

export interface JobCreatePayload {
  title: string;
  salary_text?: string;
  location_raw: string;
  requirements_raw?: string;
  shift?: "day" | "night" | "rotating" | "flexible";
  start_date?: string;
  target_hires?: number;
}

export interface AIWarning {
  code: "SALARY_BELOW_MARKET" | "VAGUE_LOCATION" | "UNREALISTIC_REQUIREMENT";
  message: string;
}

export interface JobResponse {
  id: string;
  status: "draft" | "active" | "paused" | "closed";
  title: string;
  salary_min_vnd: number | null;
  salary_max_vnd: number | null;
  salary_text: string | null;
  location_district: string;
  location_city: string;
  location_lat: number;
  location_lng: number;
  start_date: string | null;
  shift: string | null;
  requirements_parsed: Record<string, unknown> | null;
  ai_warnings: AIWarning[] | null;
  created_at: string;
}

export interface ContentVariant {
  id: string;
  variant_index: number;
  hook_style: "urgency" | "salary_first" | "proximity" | "friendly" | "detailed";
  copy_vietnamese: string;
  final_copy: string | null;
}

export interface ShareKitItem {
  source_id: string;
  source_display_name: string;
  source_channel: string;
  variant_id: string;
  tracking_id: string;
  copy_with_placeholder: string;
  poster_url: string | null;
}

export interface GenerateContentResponse {
  variants: ContentVariant[];
  warnings: AIWarning[];
  token_usage: Record<string, unknown>;
  share_kit: ShareKitItem[];
}

// ─── HR admin leads (list + detail) ───

export interface LeadListItem {
  lead_id: string;
  match_id: string | null;
  session_id: string | null;
  full_name: string;
  phone_masked: string;
  area: string | null;
  score_total: number | null;
  tier: "hot" | "warm" | "cold" | null;
  distance_km: number | null;
  job_id: string | null;
  job_title: string | null;
  source_display_name: string | null;
  created_at: string;
  session_status: "in_progress" | "completed" | "abandoned" | null;
}

export interface LeadListResponse {
  items: LeadListItem[];
  total: number;
}

export interface TranscriptMessage {
  turn_index: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface LeadAttribution {
  source_channel: string;
  source_display_name: string | null;
  tracking_id: string | null;
  variant_hook_style: string | null;
}

export interface LeadDetailResponse {
  lead_id: string;
  full_name: string;
  phone_masked: string;
  phone_full: string;
  area_normalized: string | null;
  area_raw: string | null;
  created_at: string;
  match_id: string | null;
  score_total: number | null;
  tier: "hot" | "warm" | "cold" | null;
  score_breakdown: ScoreBreakdown | null;
  distance_km: number | null;
  explanation_vi: string | null;
  job_id: string | null;
  job_title: string | null;
  attribution: LeadAttribution | null;
  session_id: string | null;
  session_status: "in_progress" | "completed" | "abandoned" | null;
  turn_count: number | null;
  extracted_data: Record<string, unknown> | null;
  transcript: TranscriptMessage[];
  consent_version: string | null;
  consent_granted_at: string | null;
}

export interface TrackingLinkResponse {
  tracking_id: string;
  share_url: string;
  job_id: string;
  variant_id: string;
  source_id: string;
}
