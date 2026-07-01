export type UserRole = 'ADMIN' | 'DOCTOR' | 'LABORATORIAN' | 'PATIENT'
export type Gender = 'MALE' | 'FEMALE'
export type LabOrderStatus = 'ORDERED' | 'IN_PROGRESS' | 'RESULTS_READY' | 'CONCLUDED'
export type LabOrderPriority = 'ROUTINE' | 'URGENT' | 'EMERGENCY'
export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH'
export type ConclusionStatus = 'DRAFT' | 'SENT'
export type RecommendationPriority = 'HIGH' | 'MEDIUM' | 'LOW'

export interface User {
  id: string
  email: string
  role: UserRole
  first_name: string
  last_name: string
  middle_name: string | null
  full_name: string
  is_active: boolean
  created_at: string
}

export interface UserShort {
  id: string
  full_name: string
  role: UserRole
}

export interface PatientShort {
  id: string
  medical_record_number: string
  full_name: string
  date_of_birth: string
  age: number
  gender: Gender
}

export interface Patient {
  id: string
  medical_record_number: string
  first_name: string
  last_name: string
  middle_name: string | null
  full_name: string
  date_of_birth: string
  age: number
  gender: Gender
  phone: string | null
  address: string | null
  family_history_diabetes: boolean
  user_id: string | null
  created_by: string
  created_at: string
}

export interface LabResultsView {
  analysis_date: string | null
  analysis_time: string | null
  lab_notes: string | null
  results_submitted_at: string | null
  glucose: string | null
  hba1c: string | null
  insulin: string | null
  bmi: string | null
  waist_circumference: string | null
  systolic_bp: number | null
  diastolic_bp: number | null
  total_cholesterol: string | null
  hdl_cholesterol: string | null
  ldl_cholesterol: string | null
  triglycerides: string | null
}

export interface LabOrder {
  id: string
  status: LabOrderStatus
  priority: LabOrderPriority
  requested_panels: string[]
  order_notes: string | null
  ordered_at: string
  created_at: string
  patient: PatientShort
  ordering_doctor: UserShort
  laboratorian: UserShort | null
  results: LabResultsView | null
}

export interface RecommendationItem {
  category: string
  text: string
  priority: RecommendationPriority
}

export interface AIRecommendation {
  id: string
  summary: string
  recommendations: RecommendationItem[]
  warning_flags: string[]
  generated_at: string
}

export interface Prediction {
  id: string
  lab_order_id: string
  model_name: string
  model_version: string
  risk_score: string
  risk_level: RiskLevel
  homa_ir: string | null
  feature_importances: Record<string, number>
  predicted_at: string
}

export interface PredictionFullResponse {
  prediction: Prediction
  ai_recommendation: AIRecommendation
  disclaimer: string
}

export interface Conclusion {
  id: string
  lab_order_id: string
  preliminary_diagnosis: string | null
  conclusion_text: string
  recommendations: string | null
  agreed_with_ai: boolean
  risk_confirmed: RiskLevel | null
  follow_up_date: string | null
  status: ConclusionStatus
  sent_at: string | null
  created_at: string
  updated_at: string
  doctor: UserShort
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface SystemStats {
  total_users: number
  total_patients: number
  orders_by_status: Record<string, number>
}

export interface AuditLog {
  id: number
  user_id: string | null
  action: string
  entity_type: string | null
  entity_id: string | null
  details: Record<string, unknown> | null
  ip_address: string | null
  timestamp: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}
