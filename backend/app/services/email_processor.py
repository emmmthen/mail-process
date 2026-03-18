from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.services.quote_service import QuoteService
from app.schemas.email import EmailImportResponse
from app.schemas.quote import QuoteCreate
import re
import os


class EmailProcessor:
    """邮件数据提取处理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.quote_service = QuoteService(db)
    
    async def process_email(self, email_path: str, process_type: str = "auto") -> EmailImportResponse:
        """处理单封邮件"""
        try:
            # 检测邮件类型并提取数据
            quotes_data = await self._extract_quotes_from_email(email_path, process_type)
            
            # 创建报价记录
            created_quotes = []
            for quote_data in quotes_data:
                # 确保 quote_data 包含必要的字段
                if not quote_data.get('usd_price'):
                    continue  # 跳过没有价格的报价
                
                # 从备注中提取交货期和 MOQ
                remarks = quote_data.get('remarks', '')
                lead_time = quote_data.get('lead_time')
                moq = quote_data.get('moq')
                
                if not lead_time or not moq:
                    lead_time, moq = self._extract_lead_time_and_moq_from_remarks(remarks)
                
                # 转换为 QuoteCreate 对象
                quote_create = QuoteCreate(
                    part_number=quote_data.get('part_number'),
                    supplier_name=quote_data.get('supplier_name'),
                    usd_price=quote_data.get('usd_price'),
                    currency_symbol=quote_data.get('currency_symbol'),
                    lead_time=lead_time,
                    moq=moq,
                    remarks=remarks,
                    exchange_rate=7.2,  # 默认汇率
                    additional_fee=0.0,  # 默认附加费用
                    service_fee_rate=0.0,  # 默认服务费率
                    source_type=quote_data.get('source_type', 'email'),
                    source_id=quote_data.get('source_id')
                )
                
                quote = await self.quote_service.create_quote(quote_create)
                created_quotes.append(quote)
            
            # 安全地序列化报价对象
            quotes_serialized = []
            for quote in created_quotes:
                quote_dict = {
                    "id": quote.id,
                    "part_number": quote.part_number,
                    "supplier_name": quote.supplier_name,
                    "usd_price": quote.usd_price,
                    "cny_price": quote.cny_price,
                    "currency_symbol": quote.currency_symbol,
                    "lead_time": quote.lead_time,
                    "moq": quote.moq,
                    "source_type": quote.source_type,
                    "source_id": quote.source_id,
                    "status": quote.status,
                    "created_at": quote.created_at.isoformat() if quote.created_at else None,
                    "updated_at": quote.updated_at.isoformat() if quote.updated_at else None
                }
                quotes_serialized.append(quote_dict)
            
            return EmailImportResponse(
                success=True,
                quotes_extracted=len(created_quotes),
                message=f"成功提取 {len(created_quotes)} 条报价数据",
                quotes=quotes_serialized
            )
        except Exception as e:
            return EmailImportResponse(
                success=False,
                quotes_extracted=0,
                message=f"处理失败：{str(e)}"
            )
    
    async def process_batch_emails(self, folder_path: str) -> EmailImportResponse:
        """批量处理邮件"""
        total_quotes = 0
        success_count = 0
        
        for filename in os.listdir(folder_path):
            if filename.endswith(('.eml', '.msg', '.txt', '.html')):
                file_path = os.path.join(folder_path, filename)
                result = await self.process_email(file_path)
                if result.success:
                    success_count += 1
                    total_quotes += result.quotes_extracted
        
        return EmailImportResponse(
            success=True,
            quotes_extracted=total_quotes,
            message=f"成功处理 {success_count} 封邮件，提取 {total_quotes} 条报价"
        )
    
    async def _extract_quotes_from_email(self, email_path: str, process_type: str) -> List[dict]:
        """从邮件中提取报价数据"""
        # 读取邮件内容
        content = self._read_email_content(email_path)
        
        # 检测是否为"暂无报价"
        if self._is_no_quote(content):
            return []
        
        # 根据类型选择提取器
        if process_type == "auto":
            process_type = self._detect_email_type(content)
        
        if process_type == "html":
            return await self._extract_from_html(content)
        elif process_type == "text":
            return await self._extract_from_text(content)
        elif process_type == "pdf":
            return await self._extract_from_pdf(email_path)
        elif process_type == "image":
            return await self._extract_from_image(email_path)
        else:
            return await self._extract_from_text(content)
    
    def _read_email_content(self, email_path: str) -> str:
        """读取邮件内容"""
        import email
        import quopri
        
        # 检查文件扩展名
        ext = os.path.splitext(email_path)[1].lower()
        
        if ext == '.eml':
            # 处理 .eml 文件
            with open(email_path, 'rb') as f:
                msg = email.message_from_bytes(f.read())
            
            # 提取邮件正文
            content = []
            
            def process_part(part):
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # 跳过附件
                if 'attachment' in content_disposition:
                    return
                
                # 处理文本内容
                if content_type == 'text/plain':
                    charset = part.get_content_charset('utf-8')
                    try:
                        content.append(part.get_payload(decode=True).decode(charset))
                    except:
                        content.append(part.get_payload())
                elif content_type == 'text/html':
                    charset = part.get_content_charset('utf-8')
                    try:
                        content.append(part.get_payload(decode=True).decode(charset))
                    except:
                        content.append(part.get_payload())
                elif part.is_multipart():
                    for subpart in part.get_payload():
                        process_part(subpart)
            
            if msg.is_multipart():
                for part in msg.get_payload():
                    process_part(part)
            else:
                process_part(msg)
            
            return '\n'.join(content)
        else:
            # 处理其他格式文件
            with open(email_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    def _is_no_quote(self, content: str) -> bool:
        """检查是否为"暂无报价"邮件"""
        no_quote_patterns = [
            r"暂无报价",
            r"No\s*Quote",
            r"Not\s*[Aa]vailable",
            r"无法报价"
        ]
        
        for pattern in no_quote_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _detect_email_type(self, content: str) -> str:
        """检测邮件类型"""
        if "<table" in content.lower():
            return "html"
        elif len(content.strip()) < 100:
            return "text"
        else:
            # 检查是否包含常见的报价关键词
            quote_keywords = ['报价', 'quote', 'price', '单价', 'cost', '金额']
            for keyword in quote_keywords:
                if keyword.lower() in content.lower():
                    return "text"
            return "html"
    
    async def _extract_from_html(self, content: str) -> List[dict]:
        """从 HTML 表格提取数据"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, 'html.parser')
        quotes = []
        
        # 查找表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            # 跳过表头行
            header_row = True
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # 跳过表头行
                    if header_row:
                        header_row = False
                        continue
                    # 尝试提取件号和价格
                    quote_data = self._parse_table_row(cells)
                    if quote_data and quote_data.get('part_number'):
                        quotes.append(quote_data)
        
        return quotes
    
    async def _extract_from_text(self, content: str) -> List[dict]:
        """从非结构化文本提取数据"""
        quotes = []
        
        # 正则表达式提取件号（假设格式如：PN123, P/N: ABC-456 等）
        part_number_patterns = [
            r"P(?:art)?\s*N(?:umber)?[:\s]*([A-Z0-9\-]+)",
            r"PN[:\s]*([A-Z0-9\-]+)",
            r"件号 [:\s]*([A-Z0-9\-]+)",
            r"Part\s*No[:\s]*([A-Z0-9\-]+)",
            r"Part\s*Number[:\s]*([A-Z0-9\-]+)",
            r"Item\s*No[:\s]*([A-Z0-9\-]+)",
            r"Item\s*Number[:\s]*([A-Z0-9\-]+)",
            r"Product\s*Code[:\s]*([A-Z0-9\-]+)",
            r"Product\s*No[:\s]*([A-Z0-9\-]+)",
            r"Model\s*No[:\s]*([A-Z0-9\-]+)",
            r"Model\s*Number[:\s]*([A-Z0-9\-]+)",
            r"Part[:\s]*([A-Z0-9\-]+)",
            r"P/N[:\s]*([A-Z0-9\-]+)",
            r"\b([A-Z0-9\-]{3,})\b",  # 通用件号格式
        ]
        
        # 正则表达式提取价格
        price_patterns = [
            r"[\$￥]\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:USD|CNY|人民币|美元)",
            r"价格 [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"单价 [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"金额 [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"报价 [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"cost [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"price [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"quote [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"unit price [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"\$([0-9,]+(?:\.[0-9]+)?)",
            r"￥([0-9,]+(?:\.[0-9]+)?)",
            r"USD\s*([0-9,]+(?:\.[0-9]+)?)",
            r"CNY\s*([0-9,]+(?:\.[0-9]+)?)",
            r"人民币\s*([0-9,]+(?:\.[0-9]+)?)",
            r"美元\s*([0-9,]+(?:\.[0-9]+)?)",
        ]
        
        # 提取件号
        part_numbers = []
        for pattern in part_number_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            part_numbers.extend(matches)
        
        # 去重并过滤无效件号
        part_numbers = list(set(part_numbers))
        valid_part_numbers = []
        # 常见的货币代码，避免将其识别为件号
        currency_codes = ['USD', 'CNY', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'HKD', 'SGD']
        for pn in part_numbers:
            # 过滤掉纯数字的件号（可能是价格）和货币代码
            if not pn.isdigit() and len(pn) >= 3 and pn.upper() not in currency_codes:
                valid_part_numbers.append(pn)
        part_numbers = valid_part_numbers
        
        # 提取价格
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    prices.append(match[0])
                else:
                    prices.append(match)
        
        # 去重并清理价格
        prices = list(set(prices))
        valid_prices = []
        for price in prices:
            # 移除逗号并转换为数字
            price_str = price.replace(',', '')
            try:
                float(price_str)
                valid_prices.append(price_str)
            except:
                pass
        prices = valid_prices
        
        # 匹配件号和价格
        for i, pn in enumerate(part_numbers):
            quote = {
                "part_number": pn.strip(),
                "source_type": "text"
            }
            
            if i < len(prices):
                price_str = prices[i]
                # 移除价格中的逗号
                price_str = price_str.replace(',', '')
                currency_symbol = self._detect_currency(content)
                quote["currency_symbol"] = currency_symbol
                
                if currency_symbol in ["$", "USD"]:
                    quote["usd_price"] = float(price_str)
                else:
                    quote["usd_price"] = float(price_str) / 7.2  # 假设是人民币，反推美金
            
            quotes.append(quote)
        
        return quotes
    
    async def _extract_from_pdf(self, file_path: str) -> List[dict]:
        """从 PDF 提取数据"""
        import pdfplumber
        
        quotes = []
        text_content = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # 尝试提取表格
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if row:
                                quote_data = self._parse_table_row([type('obj', (object,), {'text': str(c)})() for c in row if c])
                                if quote_data and quote_data.get('part_number'):
                                    quotes.append(quote_data)
                    
                    # 提取文本
                    text = page.extract_text()
                    if text:
                        text_content += text
            
            # 如果没有表格，尝试从文本提取
            if not quotes and text_content:
                quotes = await self._extract_from_text(text_content)
        except Exception as e:
            print(f"PDF 处理错误：{e}")
        
        return quotes
    
    async def _extract_from_image(self, image_path: str) -> List[dict]:
        """从图片提取数据（OCR）"""
        # TODO: 实现 OCR 功能
        # 需要安装 pytesseract 和 Tesseract-OCR
        return []
    
    def _parse_table_row(self, cells) -> Optional[dict]:
        """解析表格行"""
        quote = {}
        cell_texts = [cell.text.strip() if hasattr(cell, 'text') else str(cell).strip() for cell in cells]
        
        # 常见的货币代码，避免将其识别为件号
        currency_codes = ['USD', 'CNY', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'HKD', 'SGD']
        
        # 尝试识别件号列和价格列
        part_number = None
        price = None
        currency_symbol = None
        
        for i, text in enumerate(cell_texts):
            # 尝试识别件号（排除货币代码）
            if re.match(r'^[A-Z0-9\-]{3,}$', text, re.IGNORECASE) and text.upper() not in currency_codes:
                part_number = text
                quote["part_number"] = part_number
            
            # 尝试识别价格
            # 直接检查是否包含货币符号
            if '$' in text or '￥' in text:
                # 提取价格数字（匹配完整的数字）
                price_match = re.search(r'[\$￥]\s*(\d+(?:,\d{3})*(?:\.\d+)?)', text)
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    price = float(price_str)
                    
                    # 检测货币类型
                    if '$' in text:
                        currency_symbol = '$'
                        quote["usd_price"] = price
                    else:
                        currency_symbol = '￥'
                        quote["usd_price"] = price / 7.2  # 人民币转换为美金
                    
                    quote["currency_symbol"] = currency_symbol
        
        return quote if "part_number" in quote else None
    
    def _is_price_column(self, text: str, cell_texts: list) -> bool:
        """判断是否为价格列"""
        # 检查文本中是否包含价格相关关键词
        price_keywords = ['price', '单价', '金额', '报价', 'cost', 'USD', 'CNY', '人民币', '美元', '$', '￥']
        
        # 检查当前单元格
        for keyword in price_keywords:
            if keyword.lower() in text.lower():
                return True
        
        # 检查其他单元格（作为表头）
        for cell_text in cell_texts:
            for keyword in price_keywords:
                if keyword.lower() in cell_text.lower():
                    return True
        
        return False
    
    def _detect_currency(self, text: str) -> str:
        """检测货币符号"""
        if "$" in text or "USD" in text or "US$" in text:
            return "$"
        elif "￥" in text or "CNY" in text or "人民币" in text:
            return "￥"
        else:
            return "￥"  # 默认为人民币
    
    def _extract_lead_time_and_moq_from_remarks(self, remarks: str) -> tuple:
        """从备注中提取交货期和 MOQ"""
        lead_time = None
        moq = None
        
        # 提取交货期
        lead_time_patterns = [
            r"交货期[:\s]*([^,]+)",
            r"Lead\s*Time[:\s]*([^,]+)",
            r"交付时间[:\s]*([^,]+)",
            r"Delivery[:\s]*([^,]+)",
            r"交期[:\s]*([^,]+)",
            r"时间[:\s]*([^,]+)",
        ]
        
        for pattern in lead_time_patterns:
            match = re.search(pattern, remarks, re.IGNORECASE)
            if match:
                lead_time = match.group(1).strip()
                break
        
        # 提取 MOQ
        moq_patterns = [
            r"MOQ[:\s]*([0-9]+)",
            r"最小起订量[:\s]*([0-9]+)",
            r"起订量[:\s]*([0-9]+)",
            r"Minimum[:\s]*Order[:\s]*([0-9]+)",
            r"最小[:\s]*([0-9]+)",
            r"MOQ[:\s]*([0-9]+)",
        ]
        
        for pattern in moq_patterns:
            match = re.search(pattern, remarks, re.IGNORECASE)
            if match:
                moq = int(match.group(1).strip())
                break
        
        return lead_time, moq
