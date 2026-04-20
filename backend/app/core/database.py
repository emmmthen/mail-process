from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 确保 SQLite 数据库目录存在，避免启动时因路径缺失失败
if settings.DATABASE_URL.startswith("sqlite:///./"):
    db_path = Path(settings.DATABASE_URL.removeprefix("sqlite:///./"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖注入函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
