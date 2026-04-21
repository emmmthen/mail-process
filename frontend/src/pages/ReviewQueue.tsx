import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Modal,
  Space,
  Spin,
  Select,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  approveReview,
  correctReview,
  getPendingReviews,
  getReviewDetail,
  rejectReview,
} from '../services/api'
import type { ReviewPendingItem } from '../types'

const { TextArea } = Input
const { Text } = Typography

type ReviewFormValue = {
  part_number?: string
  supplier_name?: string
  usd_price?: number
  lead_time?: string
  moq?: number
  remarks?: string
  review_action?: 'approve' | 'correct' | 'reject' | 'no_quote'
  reason?: string
  can_reuse_as_pattern?: boolean
}

export default function ReviewQueue() {
  const [form] = Form.useForm<ReviewFormValue>()
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)
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

  const columns: ColumnsType<ReviewPendingItem> = [
    {
      title: '件号',
      dataIndex: 'part_number',
      key: 'part_number',
      render: (value) => value || '-',
    },
    {
      title: '供应商',
      dataIndex: 'supplier_name',
      key: 'supplier_name',
      render: (value) => value || '-',
    },
    {
      title: '置信度',
      dataIndex: 'confidence_score',
      key: 'confidence_score',
      render: (value) => (value === undefined ? '-' : (value * 100).toFixed(0) + '%'),
    },
    {
      title: '状态',
      dataIndex: 'run_status',
      key: 'run_status',
      render: (value) => <Tag color={value === 'pending_review' ? 'orange' : 'green'}>{value}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type="link" onClick={() => setSelectedRunId(record.extraction_run_id)}>
          查看详情
        </Button>
      ),
    },
  ]

  const initialValues = useMemo<ReviewFormValue>(() => {
    const quote = detail?.extraction_run?.llm_output_json?.quotes?.[0] || {}
    return {
      part_number: quote.part_number,
      supplier_name: quote.supplier_name,
      usd_price: quote.usd_price,
      lead_time: quote.lead_time,
      moq: quote.moq,
      remarks: quote.remarks,
      review_action: quote.quote_status === 'no_quote' ? 'no_quote' : 'approve',
      can_reuse_as_pattern: false,
    }
  }, [detail])

  useEffect(() => {
    if (detail) {
      form.setFieldsValue(initialValues)
    }
  }, [detail, form, initialValues])

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="待审核队列">
        {pendingLoading ? (
          <Spin />
        ) : (
          <Table
            columns={columns}
            dataSource={pendingReviews}
            rowKey="extraction_run_id"
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: '暂无待审核记录' }}
          />
        )}
      </Card>

      <Modal
        title="抽取详情"
        open={selectedRunId !== null}
        onCancel={() => setSelectedRunId(null)}
        footer={null}
        width={1000}
        destroyOnClose
      >
        {detailLoading || !detail ? (
          <Spin />
        ) : (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message={`来源：${detail.email_message.subject || '未命名邮件'}`}
              description={`发件人：${detail.email_message.sender || '-'}，审核后可确认、修改或驳回抽取结果。`}
              type="info"
              showIcon
            />

            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="状态">{detail.extraction_run.run_status}</Descriptions.Item>
              <Descriptions.Item label="置信度">
                {detail.extraction_run.confidence_score === undefined
                  ? '-'
                  : `${(detail.extraction_run.confidence_score * 100).toFixed(0)}%`}
              </Descriptions.Item>
              <Descriptions.Item label="来源类型">{detail.email_message.source_type || '-'}</Descriptions.Item>
              <Descriptions.Item label="邮件ID">{detail.email_message.id}</Descriptions.Item>
            </Descriptions>

            <Card size="small" title="重建内容">
              <Text style={{ whiteSpace: 'pre-wrap' }}>
                {detail.email_artifact?.rebuilt_text || '暂无重建内容'}
              </Text>
            </Card>

            <Card size="small" title="抽取结果">
              <Text style={{ whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(detail.extraction_run.llm_output_json, null, 2)}
              </Text>
            </Card>

            <Form
              form={form}
              layout="vertical"
              initialValues={initialValues}
              onFinish={(values) => {
                const payload = {
                  reviewer: 'system-user',
                  review_reason: values.reason,
                  can_reuse_as_pattern: !!values.can_reuse_as_pattern,
                  final_values: {
                    part_number: values.part_number,
                    supplier_name: values.supplier_name,
                    usd_price: values.usd_price,
                    lead_time: values.lead_time,
                    moq: values.moq,
                    remarks: values.remarks,
                    quote_status: values.review_action === 'no_quote' ? 'no_quote' : 'quoted',
                    source_id: String(detail.extraction_run.id),
                    source_type: detail.email_message.source_type || 'email',
                  },
                }

                if (values.review_action === 'reject') {
                  rejectMutation.mutate({ id: detail.extraction_run.id, data: { reviewer: 'system-user', review_reason: values.reason || '人工驳回', can_reuse_as_pattern: !!values.can_reuse_as_pattern } })
                  return
                }

                if (values.review_action === 'no_quote') {
                  rejectMutation.mutate({
                    id: detail.extraction_run.id,
                    data: {
                      reviewer: 'system-user',
                      review_reason: values.reason || 'No Quote',
                      can_reuse_as_pattern: !!values.can_reuse_as_pattern,
                    },
                  })
                  return
                }

                if (values.review_action === 'correct') {
                  correctMutation.mutate({
                    id: detail.extraction_run.id,
                    data: {
                      reviewer: 'system-user',
                      review_reason: values.reason,
                      reviewed_fields: detail.extraction_run.llm_output_json,
                      final_values: payload.final_values,
                      can_reuse_as_pattern: !!values.can_reuse_as_pattern,
                    },
                  })
                  return
                }

                approveMutation.mutate({
                  id: detail.extraction_run.id,
                  data: {
                    reviewer: 'system-user',
                    review_reason: values.reason,
                    final_values: payload.final_values,
                    can_reuse_as_pattern: !!values.can_reuse_as_pattern,
                  },
                })
              }}
            >
              <Form.Item label="件号" name="part_number">
                <Input />
              </Form.Item>
              <Form.Item label="供应商" name="supplier_name">
                <Input />
              </Form.Item>
              <Space size="large" style={{ width: '100%' }} align="start">
                <Form.Item label="美金单价" name="usd_price" style={{ flex: 1 }}>
                  <InputNumber style={{ width: '100%' }} min={0} step={0.01} />
                </Form.Item>
                <Form.Item label="交货期" name="lead_time" style={{ flex: 1 }}>
                  <Input />
                </Form.Item>
                <Form.Item label="MOQ" name="moq" style={{ flex: 1 }}>
                  <InputNumber style={{ width: '100%' }} min={0} step={1} />
                </Form.Item>
              </Space>
              <Form.Item label="备注" name="remarks">
                <TextArea rows={3} />
              </Form.Item>
              <Form.Item label="审核动作" name="review_action" initialValue="approve">
                <Select
                  options={[
                    { value: 'approve', label: '通过' },
                    { value: 'correct', label: '修改后通过' },
                    { value: 'reject', label: '驳回' },
                    { value: 'no_quote', label: '暂无报价' },
                  ]}
                />
              </Form.Item>
              <Form.Item label="原因" name="reason">
                <TextArea rows={2} placeholder="可填写修改原因、驳回原因或复用说明" />
              </Form.Item>
              <Form.Item name="can_reuse_as_pattern" valuePropName="checked">
                <Checkbox>可复用为模板经验</Checkbox>
              </Form.Item>

              <Space>
                <Button type="primary" htmlType="submit" loading={approveMutation.isPending || correctMutation.isPending || rejectMutation.isPending}>
                  提交
                </Button>
                <Button onClick={() => form.resetFields()}>重置</Button>
              </Space>
            </Form>
          </Space>
        )}
      </Modal>
    </Space>
  )
}
