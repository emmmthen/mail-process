import { Table, Card, Space, Button, Input, Tag } from 'antd'
import { SearchOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getQuotes, deleteQuote } from '../services/api'
import type { Quote } from '../types'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

export default function QuoteList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchPartNumber, setSearchPartNumber] = useState('')

  const { data: quotes, isLoading } = useQuery({
    queryKey: ['quotes', { part_number: searchPartNumber }],
    queryFn: () => getQuotes({ part_number: searchPartNumber }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteQuote(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
    },
  })

  const columns = [
    {
      title: '件号',
      dataIndex: 'part_number',
      key: 'part_number',
    },
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
      render: (price: number) => price ? `￥${price.toFixed(2)}` : '-',
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
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'valid' ? 'green' : status === 'invalid' ? 'red' : 'orange'
        const text = status === 'valid' ? '有效' : status === 'invalid' ? '无效' : '待确认'
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Quote) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/comparison/${record.part_number}`)}
          >
            比价
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteMutation.mutate(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card title="报价列表">
      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索件号"
          value={searchPartNumber}
          onChange={(e) => setSearchPartNumber(e.target.value)}
          style={{ width: 300 }}
          prefix={<SearchOutlined />}
          allowClear
        />
      </Space>
      <Table
        columns={columns}
        dataSource={quotes}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 20 }}
      />
    </Card>
  )
}
