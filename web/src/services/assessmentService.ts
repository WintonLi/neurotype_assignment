import { apiClient } from "../api/client";

export type AssessmentStatus = "pending_review" | "issued";

export type DomainName =
  | "social_communication"
  | "sensory_processing"
  | "executive_function"
  | "emotional_regulation"
  | "motor_coordination";

export type SupportNeedBand = "minimal" | "mild" | "moderate" | "substantial";

export type AssessmentSortField = "assessed_at" | "clinician_id";
export type SortOrder = "asc" | "desc";

export interface AssessmentItem {
  code: string;
  raw: number | null;
  max: number;
  completed: boolean;
}

export interface DomainResult {
  domain: DomainName;
  percentage: number | null;
  band: SupportNeedBand | null;
  items: AssessmentItem[];
}

export interface AssessmentListItem {
  assessment_id: string;
  assessed_at: string;
  clinician_id: string;
  status: AssessmentStatus;
  flagged: boolean;
  domains: DomainResult[];
}

export interface AssessmentListResponse {
  items: AssessmentListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface ListAssessmentsParams {
  status?: AssessmentStatus;
  clinician_id?: string;
  flagged?: boolean;
  domain?: DomainName;
  band?: SupportNeedBand;
  page?: number;
  page_size?: number;
  sort_by?: AssessmentSortField;
  sort_order?: SortOrder;
}

export async function listAssessments(
  params: ListAssessmentsParams,
): Promise<AssessmentListResponse> {
  const response = await apiClient.get<AssessmentListResponse>("/assessments", { params });
  return response.data;
}
