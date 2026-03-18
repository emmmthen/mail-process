from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.email import EmailImportResponse, BatchEmailImportRequest
from app.services.email_processor import EmailProcessor
import tempfile
import os

router = APIRouter()


@router.post("/import", response_model=EmailImportResponse)
async def import_email(
    file: UploadFile = File(...),
    process_type: str = Form("auto"),
    db: Session = Depends(get_db)
):
    """导入并解析单封邮件"""
    processor = EmailProcessor(db)
    try:
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 处理邮件
            result = await processor.process_email(
                temp_file_path,
                process_type
            )
            return result
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    except Exception as e:
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
