import { Card, Upload, Button, Space, message, Alert } from 'antd'
import { InboxOutlined, UploadOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { importEmail } from '../services/api'
import type { UploadProps } from 'antd'

export default function EmailImport() {
  const importMutation = useMutation({
    mutationFn: (filePath: string) => importEmail({ email_file_path: filePath }),
    onSuccess: (data) => {
      if (data.success) {
        message.success(data.message)
      } else {
        message.error(data.message)
      }
    },
  })

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    accept: '.eml,.msg,.txt,.html,.pdf',
    beforeUpload: (file) => {
      // 这里需要实现文件上传到服务器的逻辑
      // 目前简化处理，假设文件已经在服务器上
      const filePath = `/uploads/${file.name}`
      importMutation.mutate(filePath)
      return false
    },
  }

  return (
    <Card title="邮件导入">
      <Alert
        message="使用说明"
        description="将供应商报价邮件拖拽到下方区域，或点击上传。支持 .eml, .msg, .txt, .html, .pdf 格式。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Upload.Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个或多个文件批量上传
          </p>
        </Upload.Dragger>

        <Button 
          type="primary" 
          icon={<UploadOutlined />}
          onClick={() => message.info('批量导入功能开发中...')}
        >
          批量导入文件夹
        </Button>
      </Space>
    </Card>
  )
}
