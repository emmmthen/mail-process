# 航空零件采购比价系统 - 快速启动指南

## 项目结构

```
AI-coding/
├── backend/          # 后端（Python + FastAPI）
│   ├── app/
│   │   ├── api/     # API 路由
│   │   ├── core/    # 核心配置
│   │   ├── models/  # 数据库模型
│   │   ├── schemas/ # Pydantic Schema
│   │   └── services/# 业务逻辑
│   ├── pyproject.toml  # 项目配置（使用 UV 管理）
│   ├── uv.lock          # 依赖锁定文件
│   └── .env
├── frontend/         # 前端（React + TypeScript）
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json     # 项目配置（使用 PNPM 管理）
├── scripts/          # 脚本目录
│   ├── start_backend.sh # 启动后端服务
│   ├── start_frontend.sh # 启动前端服务
│   └── test_*.py        # 测试脚本
└── requirements.md   # 需求文档
```

## 快速启动

### 1. 启动后端

**使用 UV 管理依赖**

```bash
# 进入后端目录
cd backend

# 安装依赖（使用 UV）
uv sync

# 启动后端服务
../scripts/start_backend.sh
```

或者直接从项目根目录启动：

```bash
# 从根目录启动后端
./scripts/start_backend.sh
```

后端服务将在 http://localhost:8000 启动
API 文档：http://localhost:8000/docs

### 2. 启动前端

**使用 PNPM 管理依赖**

```bash
# 进入前端目录
cd frontend

# 安装依赖（使用 PNPM）
pnpm install

# 启动开发服务器
pnpm run dev
```

或者直接从项目根目录启动：

```bash
# 从根目录启动前端
./scripts/start_frontend.sh
```

前端服务将在 http://localhost:3000 启动

## 功能说明

### 1. 报价管理
- 查看报价列表
- 搜索件号
- 删除报价记录

### 2. 比价单
- 按件号查看多家供应商报价
- 自动高亮最低人民币单价
- 显示汇率换算参数

### 3. 邮件导入
- 上传邮件文件（.eml, .msg, .txt, .html, .pdf）
- 自动识别和提取报价数据
- 支持批量导入

### 4. 系统设置
- 配置汇率换算公式
- 调整汇率、附加费用、服务费率
- 公式：人民币单价 = 美金单价 × 汇率 + 附加费用 + (美金单价 × 服务费率)

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite (可扩展 PostgreSQL)
- **ORM**: SQLAlchemy
- **数据处理**: Pandas
- **邮件解析**: BeautifulSoup4, pdfplumber
- **OCR**: pytesseract（待实现）
- **包管理**: UV

### 前端
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design
- **状态管理**: React Query
- **路由**: React Router v6
- **HTTP 客户端**: Axios
- **包管理**: PNPM

## 下一步开发

1. **完善邮件解析**
   - 实现 PDF 附件解析
   - 实现 OCR 图片识别
   - 优化非结构化文本提取

2. **添加用户系统**
   - 用户认证
   - 权限管理
   - 多用户支持

3. **增强功能**
   - Excel 导出
   - 历史价格趋势
   - 邮件自动抓取（IMAP）

## 常见问题

### 数据库在哪里？
默认在 `backend/data/quotes.db`，使用 SQLite 存储。

### 如何切换到 PostgreSQL？
1. 安装 PostgreSQL
2. 修改 `.env` 中的 `DATABASE_URL`
3. 运行数据迁移

### 邮件服务器如何配置？
在 `.env` 中配置以下参数：
```
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_auth_code
EMAIL_IMAP_SERVER=imap.example.com
EMAIL_IMAP_PORT=993
```

## 开发团队

如有问题，请联系开发团队。
