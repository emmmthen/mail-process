export interface Quote {
  id: number
  part_number: string
  supplier_name?: string
  usd_price?: number
  cny_price?: number
  currency_symbol?: string
  exchange_rate?: number
  additional_fee?: number
  service_fee_rate?: number
  lead_time?: string
  moq?: number
  source_type?: string
  source_id?: string
  status: string
  created_at: string
  updated_at: string
}

export interface QuoteComparison {
  part_number: string
  quotes: Quote[]
  min_cny_price?: number
  min_usd_price?: number
  supplier_count: number
}

export interface EmailImportRequest {
  email_file_path: string
  process_type?: string
}

export interface EmailImportResponse {
  success: boolean
  quotes_extracted: number
  message: string
  quotes?: any[]
}

export interface ExchangeRateSettings {
  exchange_rate: number
  additional_fee: number
  service_fee_rate: number
  formula_description?: string
}

export interface SystemSettings {
  id: number
  setting_key: string
  setting_value: string
  setting_type?: string
  description?: string
  created_at: string
  updated_at: string
}

export interface EmailMessage {
  id: number
  subject?: string
  sender?: string
  received_at?: string
  source_file_path?: string
  source_file_hash?: string
  source_type?: string
  message_id?: string
  raw_status: string
  created_at: string
  updated_at: string
}

export interface EmailArtifact {
  id: number
  email_message_id: number
  cleaned_text?: string
  rebuilt_text?: string
  rebuilt_blocks_json?: any
  extractable_status: string
  created_at: string
  updated_at: string
}

export interface ExtractionRun {
  id: number
  email_message_id: number
  email_artifact_id?: number
  extract_mode: string
  llm_input_snapshot?: string
  llm_output_json?: any
  validation_result_json?: any
  confidence_score?: number
  run_status: string
  committed_quote_id?: number
  created_at: string
  updated_at: string
}

export interface ReviewAction {
  id: number
  extraction_run_id: number
  review_status: string
  review_reason?: string
  reviewed_fields_json?: any
  final_values_json?: any
  can_reuse_as_pattern: boolean
  reviewer?: string
  reviewed_at: string
}

export interface ReviewPendingItem {
  extraction_run_id: number
  email_message_id: number
  subject?: string
  sender?: string
  confidence_score?: number
  run_status: string
  created_at: string
  quote_status?: string
  supplier_name?: string
  part_number?: string
}

export interface ReviewDetail {
  email_message: EmailMessage
  email_artifact?: EmailArtifact | null
  extraction_run: ExtractionRun
  review_actions: ReviewAction[]
}

export interface ReviewApproveRequest {
  reviewer?: string
  review_reason?: string
  final_values?: Record<string, any>
  can_reuse_as_pattern?: boolean
}

export interface ReviewCorrectRequest {
  reviewer?: string
  review_reason?: string
  reviewed_fields?: Record<string, any>
  final_values: Record<string, any>
  can_reuse_as_pattern?: boolean
}

export interface ReviewRejectRequest {
  reviewer?: string
  review_reason: string
  reviewed_fields?: Record<string, any>
  can_reuse_as_pattern?: boolean
}
