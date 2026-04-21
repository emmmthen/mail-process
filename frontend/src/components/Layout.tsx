import { Menu } from 'antd'
import { Link, useLocation, Outlet } from 'react-router-dom'
import {
  DashboardOutlined,
  ImportOutlined,
  SettingOutlined,
  BarChartOutlined,
  SnippetsOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'

const menuItems: MenuProps['items'] = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: <Link to="/">报价列表</Link>,
  },
  {
    key: '/comparison',
    icon: <BarChartOutlined />,
    label: <Link to="/comparison">比价单</Link>,
  },
  {
    key: '/email-processing',
    icon: <ImportOutlined />,
    label: <Link to="/email-processing">邮件处理</Link>,
  },
  {
    key: '/reviews',
    icon: <SnippetsOutlined />,
    label: <Link to="/reviews">审核队列</Link>,
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: <Link to="/settings">系统设置</Link>,
  },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <div style={{ width: 200, background: '#001529' }}>
        <div style={{ 
          height: 32, 
          margin: 16, 
          background: 'rgba(255, 255, 255, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold'
        }}>
          采购比价系统
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
        />
      </div>
      <div style={{ flex: 1, padding: 24 }}>
        <Outlet />
      </div>
    </div>
  )
}
