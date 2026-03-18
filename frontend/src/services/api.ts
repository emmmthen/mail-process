import axios from 'axios'
import type { Quote, QuoteComparison, EmailImportRequest, EmailImportResponse, ExchangeRateSettings } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 报价相关 API
export const getQuotes = async (params?: { part_number?: string; status?: string }): Promise<Quote[]> => {
  const response = await api.get('/quotes/', { params })
  return response.data
}

export const getQuote = async (id: number): Promise<Quote> => {
  const response = await api.get(`/quotes/${id}`)
  return response.data
}

export const createQuote = async (data: Partial<Quote>): Promise<Quote> => {
  const response = await api.post('/quotes/', data)
  return response.data
}

export const updateQuote = async (id: number, data: Partial<Quote>): Promise<Quote> => {
  const response = await api.put(`/quotes/${id}`, data)
  return response.data
}

export const deleteQuote = async (id: number): Promise<void> => {
  await api.delete(`/quotes/${id}`)
}

export const getPriceComparison = async (partNumber: string): Promise<QuoteComparison> => {
  const response = await api.get(`/quotes/comparison/${partNumber}`)
  return response.data
}

// 邮件导入 API
export const importEmail = async (data: EmailImportRequest): Promise<EmailImportResponse> => {
  const response = await api.post('/emails/import', data)
  return response.data
}

export const importBatchEmails = async (folderPath: string): Promise<EmailImportResponse> => {
  const response = await api.post('/emails/import/batch', { email_folder_path: folderPath })
  return response.data
}

// 系统设置 API
export const getExchangeRateSettings = async (): Promise<ExchangeRateSettings> => {
  const response = await api.get('/settings/exchange-rate')
  return response.data
}

export const updateExchangeRateSettings = async (settings: ExchangeRateSettings): Promise<ExchangeRateSettings> => {
  const response = await api.put('/settings/exchange-rate', settings)
  return response.data
}

export const getAllSettings = async () => {
  const response = await api.get('/settings/')
  return response.data
}
