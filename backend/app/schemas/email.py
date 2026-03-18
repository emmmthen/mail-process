from pydantic import BaseModel
from typing import Optional, List


class EmailImportRequest(BaseModel):
    """邮件导入请求"""
    email_file_path: str
    process_type: str = "auto"  # auto, html, text, pdf, image


class EmailImportResponse(BaseModel):
    """邮件导入响应"""
    success: bool
    quotes_extracted: int
    message: str
    quotes: Optional[List[dict]] = None


class BatchEmailImportRequest(BaseModel):
    """批量邮件导入请求"""
    email_folder_path: str
