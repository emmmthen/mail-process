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
