from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.email import EmailImportResponse, BatchEmailImportRequest
from app.services.email_processor import EmailProcessor
import tempfile
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/import", response_model=EmailImportResponse)
async def import_email(
    file: UploadFile = File(...),
    process_type: str = Form("auto"),
    db: Session = Depends(get_db)
):
    """导入并解析单封邮件"""
    logger.info(f"开始处理邮件文件: {file.filename}")
    logger.info(f"处理类型: {process_type}")
    
    processor = EmailProcessor(db)
    try:
        # 保存上传的文件到临时目录
        logger.info("正在保存上传的文件到临时目录")
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            logger.info(f"文件大小: {len(content)} bytes")
            # 打印文件内容的前1000字符（如果文件较大）
            if len(content) > 1000:
                logger.info(f"文件内容预览: {content[:1000]}...")
            else:
                logger.info(f"文件内容: {content}")
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"临时文件保存路径: {temp_file_path}")
        
        try:
            # 处理邮件
            logger.info("开始处理邮件")
            result = await processor.process_email(
                temp_file_path,
                process_type
            )
            logger.info(f"邮件处理完成，提取到 {result.quotes_extracted} 条报价")
            logger.info(f"处理结果: {result.message}")
            return result
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                logger.info(f"清理临时文件: {temp_file_path}")
                os.unlink(temp_file_path)
    except Exception as e:
        logger.error(f"处理邮件时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/batch", response_model=EmailImportResponse)
async def import_batch_emails(
    request: BatchEmailImportRequest,
    db: Session = Depends(get_db)
):
    """批量导入邮件"""
    processor = EmailProcessor(db)
    try:
        result = await processor.process_batch_emails(request.email_folder_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection")
async def test_email_connection():
    """测试邮件服务器连接"""
    # TODO: 实现邮件服务器连接测试
    return {"status": "not_configured", "message": "请先配置邮件服务器信息"}
