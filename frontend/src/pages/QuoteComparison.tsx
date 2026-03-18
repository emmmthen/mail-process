import { Card, Table, Typography, Space, Tag, Button, Empty, Input, Alert } from 'antd'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getQuotes } from '../services/api'
import { ArrowLeftOutlined, SearchOutlined } from '@ant-design/icons'
import { useState } from 'react'

const { Title } = Typography

export default function QuoteComparison() {
  const { partNumber } = useParams<{ partNumber: string }>()
  const navigate = useNavigate()
  const [searchPartNumber, setSearchPartNumber] = useState('')

  const { data: quotes, isLoading } = useQuery({
    queryKey: ['quotes', { part_number: partNumber }],
    queryFn: () => getQuotes({ part_number: partNumber }),
    enabled: !!partNumber,
  })

  // 找出最低价格
  const minPrice = quotes 
    ? Math.min(...quotes.filter(q => q.cny_price).map(q => q.cny_price))
    : null

  const columns = [
    {
      title: '供应商',
      dataIndex: 'supplier_name',
      key: 'supplier_name',
    },
    {
      title: '美金单价',
      dataIndex: 'usd_price',
      key: 'usd_price',
      render: (price: number) => price ? `$${price.toFixed(2)}` : '-',
    },
    {
      title: '人民币单价',
      dataIndex: 'cny_price',
      key: 'cny_price',
      render: (price: number, record: any) => {
        const isLowest = price === minPrice
        return (
          <span style={{ fontWeight: isLowest ? 'bold' : 'normal', color: isLowest ? '#ff4d4f' : 'inherit' }}>
            {price ? `￥${price.toFixed(2)}` : '-'}
            {isLowest && <Tag color="red" style={{ marginLeft: 8 }}>最低</Tag>}
          </span>
        )
      },
    },
    {
      title: '汇率',
      dataIndex: 'exchange_rate',
      key: 'exchange_rate',
      render: (rate: number) => rate?.toFixed(2) || '-',
    },
    {
      title: '附加费用',
      dataIndex: 'additional_fee',
      key: 'additional_fee',
      render: (fee: number) => fee ? `￥${fee.toFixed(2)}` : '-',
    },
    {
      title: '服务费率',
      dataIndex: 'service_fee_rate',
      key: 'service_fee_rate',
      render: (rate: number) => rate ? `${(rate * 100).toFixed(1)}%` : '-',
    },
    {
      title: '交货期',
      dataIndex: 'lead_time',
      key: 'lead_time',
    },
    {
      title: 'MOQ',
      dataIndex: 'moq',
      key: 'moq',
    },
  ]

  const handleSearch = () => {
    if (searchPartNumber) {
      navigate(`/comparison/${searchPartNumber}`)
    }
  }

  if (!partNumber) {
    return (
      <Card title="比价单">
        <Alert
          message="请输入件号进行比价"
          description="在下方输入框中输入零件编号，系统将为您展示该零件的所有报价并进行比价。"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
        <Space style={{ width: '100%' }} direction="vertical" size="large">
          <Space style={{ width: '100%', justifyContent: 'center' }}>
            <Input
              placeholder="输入件号"
              value={searchPartNumber}
              onChange={(e) => setSearchPartNumber(e.target.value)}
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
              onPressEnter={handleSearch}
            />
            <Button type="primary" onClick={handleSearch}>
              搜索
            </Button>
          </Space>
          <Empty
            description="输入件号后点击搜索"
            style={{ margin: '40px 0' }}
          />
        </Space>
      </Card>
    )
  }

  return (
    <Card
      title={
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
            返回
          </Button>
          <span>件号：{partNumber} - 比价单</span>
        </Space>
      }
    >
      {minPrice && (
        <div style={{ marginBottom: 16, padding: 12, background: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 4 }}>
          <strong>最低人民币单价：￥{minPrice.toFixed(2)}</strong>
        </div>
      )}
      <Table
        columns={columns}
        dataSource={quotes}
        loading={isLoading}
        rowKey="id"
        pagination={false}
        locale={{ emptyText: '暂无报价数据' }}
      />
    </Card>
  )
}
