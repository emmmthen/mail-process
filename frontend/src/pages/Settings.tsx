import { Card, Form, InputNumber, Button, Space, message, Row, Col } from 'antd'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getExchangeRateSettings, updateExchangeRateSettings } from '../services/api'
import { DollarOutlined } from '@ant-design/icons'

export default function Settings() {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data: settings } = useQuery({
    queryKey: ['exchangeRateSettings'],
    queryFn: getExchangeRateSettings,
  })

  const updateMutation = useMutation({
    mutationFn: updateExchangeRateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exchangeRateSettings'] })
      message.success('设置已保存')
    },
  })

  const handleSubmit = (values: any) => {
    updateMutation.mutate(values)
  }

  return (
    <Card title="系统设置">
      <Form
        form={form}
        layout="vertical"
        initialValues={settings}
        onFinish={handleSubmit}
        style={{ maxWidth: 600 }}
      >
        <Form.Item
          label="汇率换算公式配置"
          tooltip="人民币单价 = 美金单价 × 汇率 + 附加费用 + (美金单价 × 服务费率)"
        >
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="exchange_rate"
                label="美金转人民币汇率"
                rules={[{ required: true, message: '请输入汇率' }]}
              >
                <InputNumber 
                  prefix={<DollarOutlined />}
                  step={0.01} 
                  min={0} 
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="additional_fee"
                label="附加费用"
                rules={[{ required: true }]}
              >
                <InputNumber 
                  prefix="￥"
                  step={0.01} 
                  min={0} 
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="service_fee_rate"
                label="服务费率"
                rules={[{ required: true }]}
              >
                <InputNumber 
                  suffix="%"
                  step={0.001} 
                  min={0} 
                  max={1}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={updateMutation.isPending}>
              保存设置
            </Button>
            <Button 
              htmlType="button"
              onClick={() => form.resetFields()}
            >
              重置
            </Button>
          </Space>
        </Form.Item>

        <Card type="inner" title="公式说明" size="small">
          <p>
            <strong>当前公式：</strong>人民币单价 = 美金单价 × {form.getFieldValue('exchange_rate') || 7.2} + {form.getFieldValue('additional_fee') || 0} + (美金单价 × {(form.getFieldValue('service_fee_rate') || 0) * 100}%)
          </p>
          <p style={{ color: '#999', fontSize: 12 }}>
            业务人员可根据实际情况调整上述参数，系统会自动重新计算所有报价的人民币单价。
          </p>
        </Card>
      </Form>
    </Card>
  )
}
