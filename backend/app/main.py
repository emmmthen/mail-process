from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import quotes, emails, settings as settings_api
from app.core.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="航空零件采购比价系统",
    description="自动识别邮件报价数据，生成比价单",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，包括 file:// 协议
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(quotes.router, prefix="/api/quotes", tags=["报价管理"])
app.include_router(emails.router, prefix="/api/emails", tags=["邮件处理"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["系统设置"])


@app.get("/")
async def root():
    return {"message": "航空零件采购比价系统 API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
