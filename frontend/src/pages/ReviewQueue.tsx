import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Descriptions,
  Divider,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  approveReview,
  correctReview,
  deleteReview,
  getPendingReviews,
  getReviewDetail,
  rejectReview,
} from '../services/api'
import type { ReviewPendingItem } from '../types'

const { TextArea } = Input
const { Text } = Typography

type QuoteRow = {
  key: string
  part_number?: string
  product_name?: string
  supplier_name?: string
  quantity?: number
  currency?: string
  unit_price?: number
  cny_price?: number
  lead_time?: string
  moq?: number
  remarks?: string
  source_location?: string
  confidence?: number
  selected?: boolean
  final?: boolean
}

type ReviewFormValue = {
  review_action?: 'approve' | 'correct' | 'reject' | 'no_quote'
  reason?: string
  can_reuse_as_pattern?: boolean
}

export default function ReviewQueue() {
  const [form] = Form.useForm<ReviewFormValue>()
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const queryClient = useQueryClient()

  const { data: pendingReviews = [], isLoading: pendingLoading } = useQuery({
    queryKey: ['pending-reviews'],
    queryFn: getPendingReviews,
  })

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['review-detail', selectedRunId],
    queryFn: () => getReviewDetail(selectedRunId!),
    enabled: selectedRunId !== null,
  })

  const quotes = useMemo<QuoteRow[]>(() => {
    const items = detail?.extraction_run?.llm_output_json?.quotes || []
    return items.map((quote: any, index: number) => ({
      key: String(index),
      part_number: quote.part_number,
      product_name: quote.product_name,
      supplier_name: quote.supplier_name,
      quantity: quote.quantity,
      currency: quote.currency || quote.currency_symbol,
      unit_price: quote.unit_price ?? quote.usd_price,
      cny_price: quote.cny_price,
      lead_time: quote.lead_time,
      moq: quote.moq,
      remarks: quote.remarks,
      source_location: quote.source_location,
      confidence: quote.confidence,
      selected: true,
      final: true,
    }))
  }, [detail])

  useEffect(() => {
    setSelectedRowKeys(quotes.map((row) => row.key))
    form.setFieldsValue({ review_action: detail?.extraction_run?.llm_output_json?.quote_status === 'no_quote' ? 'no_quote' : 'approve', can_reuse_as_pattern: false })
  }, [detail, form, quotes])

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteReview(id),
    onSuccess: () => {
      message.success('已删除')
      queryClient.invalidateQueries({ queryKey: ['pending-reviews'] })
      setSelectedRunId(null)
    },
  })

  const approveMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof approveReview>[1] }) =>
      approveReview(id, data),
    onSuccess: () => {
      message.success('已通过并提交')
      queryClient.invalidateQueries({ queryKey: ['pending-reviews'] })
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setSelectedRunId(null)
    },
  })

  const correctMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof correctReview>[1] }) =>
      correctReview(id, data),
    onSuccess: () => {
      message.success('已修改并提交')
      queryClient.invalidateQueries({ queryKey: ['pending-reviews'] })
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setSelectedRunId(null)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof rejectReview>[1] }) =>
      rejectReview(id, data),
    onSuccess: () => {
      message.success('已驳回')
      queryClient.invalidateQueries({ queryKey: ['pending-reviews'] })
      setSelectedRunId(null)
    },
  })

  const quoteColumns: ColumnsType<QuoteRow> = [
    { title: '选择', dataIndex: 'selected', render: (_, record) => <Checkbox checked={selectedRowKeys.includes(record.key)} onChange={(e) => {
      const next = e.target.checked ? [...selectedRowKeys, record.key] : selectedRowKeys.filter((key) => key !== record.key)
      setSelectedRowKeys(next)
    }} /> },
    { title: '件号', dataIndex: 'part_number', render: (value) => value || '-' },
    { title: '产品名', dataIndex: 'product_name', render: (value) => value || '-' },
    { title: '供应商', dataIndex: 'supplier_name', render: (value) => value || '-' },
    { title: '数量', dataIndex: 'quantity', render: (value) => value ?? '-' },
    { title: '币种', dataIndex: 'currency', render: (value) => value || '-' },
    { title: '单价', dataIndex: 'unit_price', render: (value) => value ?? '-' },
    { title: '人民币价', dataIndex: 'cny_price', render: (value) => value ?? '-' },
    { title: '交期', dataIndex: 'lead_time', render: (value) => value || '-' },
    { title: 'MOQ', dataIndex: 'moq', render: (value) => value ?? '-' },
    { title: '来源', dataIndex: 'source_location', render: (value) => value || '-' },
    { title: '置信度', dataIndex: 'confidence', render: (value) => (value === undefined ? '-' : `${(value * 100).toFixed(0)}%`) },
  ]

  const columns: ColumnsType<ReviewPendingItem> = [
    { title: '件号', dataIndex: 'part_number', render: (value) => value || '-' },
    { title: '供应商', dataIndex: 'supplier_name', render: (value) => value || '-' },
    { title: '置信度', dataIndex: 'confidence_score', render: (value) => (value === undefined ? '-' : `${(value * 100).toFixed(0)}%`) },
    { title: '状态', dataIndex: 'run_status', render: (value) => <Tag color={value === 'pending_review' ? 'orange' : value === 'approved' ? 'green' : 'red'}>{value}</Tag> },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" onClick={() => setSelectedRunId(record.extraction_run_id)}>查看详情</Button>
          <Popconfirm title="确定删除这条审核记录？" onConfirm={() => deleteMutation.mutate(record.extraction_run_id)}>
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const submitByAction = async (action: ReviewFormValue['review_action']) => {
    if (!selectedRunId || !detail) return
    const selectedQuotes = quotes.filter((row) => selectedRowKeys.includes(row.key))
    const finalValues = selectedQuotes.length > 0 ? selectedQuotes[0] : quotes[0]
    const payload = {
      reviewer: 'system-user',
      review_reason: form.getFieldValue('reason') || undefined,
      can_reuse_as_pattern: !!form.getFieldValue('can_reuse_as_pattern'),
      final_values: finalValues ? {
        ...finalValues,
        source_type: detail.email_message.source_type || 'email',
        source_id: String(detail.extraction_run.id),
      } : undefined,
    }
    if (action === 'reject') {
      rejectMutation.mutate({ id: selectedRunId, data: { reviewer: 'system-user', review_reason: form.getFieldValue('reason') || '人工驳回', can_reuse_as_pattern: !!form.getFieldValue('can_reuse_as_pattern') } })
      return
    }
    if (action === 'correct') {
      correctMutation.mutate({ id: selectedRunId, data: { ...payload, reviewed_fields: detail.extraction_run.llm_output_json } as any })
      return
    }
    approveMutation.mutate({ id: selectedRunId, data: payload as any })
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="待审核队列">
        {pendingLoading ? <Spin /> : <Table columns={columns} dataSource={pendingReviews} rowKey="extraction_run_id" pagination={{ pageSize: 10 }} locale={{ emptyText: '暂无待审核记录' }} />}
      </Card>

      <Modal title="抽取详情" open={selectedRunId !== null} onCancel={() => setSelectedRunId(null)} footer={null} width={1400} destroyOnClose>
        {detailLoading || !detail ? <Spin /> : (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert message={`来源：${detail.email_message.subject || '未命名邮件'}`} description={`发件人：${detail.email_message.sender || '-'}，审核后可确认、修改或驳回抽取结果。`} type="info" showIcon />
            <Descriptions bordered size="small" column={3}>
              <Descriptions.Item label="状态">{detail.extraction_run.run_status}</Descriptions.Item>
              <Descriptions.Item label="置信度">{detail.extraction_run.confidence_score === undefined ? '-' : `${(detail.extraction_run.confidence_score * 100).toFixed(0)}%`}</Descriptions.Item>
              <Descriptions.Item label="来源类型">{detail.email_message.source_type || '-'}</Descriptions.Item>
              <Descriptions.Item label="邮件ID">{detail.email_message.id}</Descriptions.Item>
              <Descriptions.Item label="处理模式">{detail.extraction_run.extract_mode}</Descriptions.Item>
              <Descriptions.Item label="抽取状态">{detail.extraction_run.llm_output_json?.quote_status || '-'}</Descriptions.Item>
            </Descriptions>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 16 }}>
              <Card title="原邮件预览" style={{ minHeight: 560, overflow: 'auto' }}>
                <pre style={{ whiteSpace: 'pre-wrap' }}>{detail.email_artifact?.cleaned_text || detail.email_artifact?.rebuilt_text || '暂无原邮件内容'}</pre>
              </Card>
              <Card title="抽取结果" style={{ minHeight: 560, overflow: 'auto' }}>
                <Table columns={quoteColumns} dataSource={quotes} pagination={false} rowKey="key" size="small" />
                <Divider />
                <Space wrap>
                  <Button type="primary" onClick={() => submitByAction('approve')}>通过并提交</Button>
                  <Button onClick={() => submitByAction('correct')}>修改并提交</Button>
                  <Button danger onClick={() => submitByAction('reject')}>未通过</Button>
                  <Button onClick={() => submitByAction('approve')}>回到未审核</Button>
                </Space>
              </Card>
            </div>
          </Space>
        )}
      </Modal>
    </Space>
  )
}
