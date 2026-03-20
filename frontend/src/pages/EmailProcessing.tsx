import { Card, Steps, Button, Space, Tabs, Table, Typography, Alert, message, Upload } from 'antd'
import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { importEmail, getQuotes } from '../services/api'
import type { UploadProps } from 'antd'
import { InboxOutlined, DownloadOutlined } from '@ant-design/icons'
import type { Quote } from '../types'

const { Title } = Typography
const { Step } = Steps
const { TabPane } = Tabs

// 模拟文件上传组件
const FileUploader = ({ onFilesUploaded }: { onFilesUploaded: (files: File[]) => void }) => {
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    accept: '.eml,.msg,.txt,.html,.pdf',
    beforeUpload: (file) => {
      return false
    },
    onChange: (info) => {
      const files = info.fileList.map(item => item.originFileObj as File)
      onFilesUploaded(files)
    },
  }

  return (
    <Card title="邮件文件上传">
      <Alert
        message="使用说明"
        description="将供应商报价邮件拖拽到下方区域，或点击上传。支持 .eml, .msg, .txt, .html, .pdf 格式。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      <Upload.Dragger {...uploadProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持单个或多个文件批量上传
        </p>
      </Upload.Dragger>
    </Card>
  )
}

// 报价列表组件
const QuoteListSection = ({ quotes, onSelectPartNumber }: { quotes: Quote[], onSelectPartNumber: (partNumber: string) => void }) => {
  const columns = [
    {
      title: '件号',
      dataIndex: 'part_number',
      key: 'part_number',
      render: (partNumber: string) => (
        <a onClick={() => onSelectPartNumber(partNumber)}>{partNumber}</a>
      ),
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
  ]

  return (
    <Card title="报价列表">
      <Table
        columns={columns}
        dataSource={quotes}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        locale={{ emptyText: '暂无报价数据' }}
      />
    </Card>
  )
}

// 比价单组件
const ComparisonSection = ({ quotes }: { quotes: Quote[] }) => {
  // 按件号分组
  const partNumberGroups: Record<string, Quote[]> = {}
  quotes.forEach(quote => {
    if (!partNumberGroups[quote.part_number]) {
      partNumberGroups[quote.part_number] = []
    }
    partNumberGroups[quote.part_number].push(quote)
  })

  // 为每个件号找到最低价格
  const comparisonData = Object.entries(partNumberGroups).map(([partNumber, partQuotes]) => {
    const minCnyPriceQuote = partQuotes.reduce((min, quote) => {
      if (!min || (quote.cny_price && quote.cny_price < min.cny_price!)) {
        return quote
      }
      return min
    }, partQuotes[0])

    return {
      part_number: partNumber,
      supplier_name: minCnyPriceQuote.supplier_name,
      usd_price: minCnyPriceQuote.usd_price,
      cny_price: minCnyPriceQuote.cny_price,
      lead_time: minCnyPriceQuote.lead_time,
    }
  })

  // 导出到CSV
  const handleExportExcel = () => {
    // 转换为CSV格式
    const headers = ['件号', '最优供应商', '美金单价', '人民币单价', '交货期']
    const csvContent = [
      headers.join(','),
      ...comparisonData.map(item => [
        item.part_number,
        item.supplier_name || '',
        item.usd_price ? `$${item.usd_price.toFixed(2)}` : '-',
        item.cny_price ? `￥${item.cny_price.toFixed(2)}` : '-',
        item.lead_time || ''
      ].join(','))
    ].join('\n')

    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', '采购比价单.csv')
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    message.success('CSV导出成功')
  }

  const columns = [
    {
      title: '件号',
      dataIndex: 'part_number',
      key: 'part_number',
    },
    {
      title: '最优供应商',
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
  ]

  return (
    <Card 
      title={
        <Space>
          <span>比价单</span>
          <Button 
            type="primary" 
            icon={<DownloadOutlined />}
            onClick={handleExportExcel}
          >
            导出Excel
          </Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={comparisonData}
        rowKey="part_number"
        pagination={{ pageSize: 10 }}
        locale={{ emptyText: '暂无比价数据' }}
      />
    </Card>
  )
}

export default function EmailProcessing() {
  const [currentStep, setCurrentStep] = useState(0)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [selectedPartNumber, setSelectedPartNumber] = useState<string>('')

  // 获取报价列表
  const { data: quotes = [], refetch } = useQuery({
    queryKey: ['quotes'],
    queryFn: () => getQuotes(),
  })

  // 邮件导入 mutation
  const importMutation = useMutation({
    mutationFn: (file: File) => importEmail(file),
    onSuccess: (data) => {
      if (data.success) {
        message.success(data.message)
        refetch() // 重新获取报价列表
        setCurrentStep(1) // 自动进入下一步
      } else {
        message.error(data.message)
      }
    },
  })

  // 处理文件上传
  const handleFilesUploaded = (files: File[]) => {
    setUploadedFiles(files)
    // 处理每个上传的文件
    files.forEach(file => {
      importMutation.mutate(file)
    })
  }

  // 处理步骤切换
  const handleStepChange = (step: number) => {
    setCurrentStep(step)
  }

  // 处理件号选择
  const handleSelectPartNumber = (partNumber: string) => {
    setSelectedPartNumber(partNumber)
    setCurrentStep(2) // 自动进入比价单步骤
  }

  const steps = [
    {
      title: '邮件导入',
      content: <FileUploader onFilesUploaded={handleFilesUploaded} />,
    },
    {
      title: '报价列表',
      content: <QuoteListSection quotes={quotes} onSelectPartNumber={handleSelectPartNumber} />,
    },
    {
      title: '比价单',
      content: <ComparisonSection quotes={quotes} />,
    },
  ]

  return (
    <div>
      <Title level={2}>邮件处理</Title>
      <Steps current={currentStep} onChange={handleStepChange} style={{ marginBottom: 24 }}>
        {steps.map((step, index) => (
          <Step key={index} title={step.title} />
        ))}
      </Steps>
      <div>{steps[currentStep].content}</div>
      <div style={{ marginTop: 24, display: 'flex', justifyContent: 'space-between' }}>
        <Button 
          disabled={currentStep === 0}
          onClick={() => setCurrentStep(currentStep - 1)}
        >
          上一步
        </Button>
        <Button 
          type="primary"
          disabled={currentStep === steps.length - 1}
          onClick={() => setCurrentStep(currentStep + 1)}
        >
          下一步
        </Button>
      </div>
    </div>
  )
}
