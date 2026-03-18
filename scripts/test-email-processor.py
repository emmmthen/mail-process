import sys
import os

# 添加后端目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db
from app.services.email_processor import EmailProcessor

# 获取数据库会话
db = next(get_db())

# 创建邮件处理器
processor = EmailProcessor(db)

# 测试邮件文件路径
email_path = 'c:\\Users\\123\\Desktop\\AI-coding\\test-email.html'

try:
    # 测试邮件处理
    result = processor.process_email(email_path, 'auto')
    print(f"Success: {result.success}")
    print(f"Quotes extracted: {result.quotes_extracted}")
    print(f"Message: {result.message}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
