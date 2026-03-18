import sys
import os

# 添加后端目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db
from app.models.quote import Quote, QuoteHistory

# 获取数据库会话
db = next(get_db())

# 统计当前报价数量
current_count = db.query(Quote).count()
print(f"当前报价数量: {current_count}")

# 显示前10条报价
print("前10条报价:")
for quote in db.query(Quote).limit(10).all():
    print(f"ID: {quote.id}, 件号: {quote.part_number}, 供应商: {quote.supplier_name}, 价格: {quote.usd_price}")

# 询问是否删除所有报价
confirm = input("是否删除所有报价数据？(y/n): ")

if confirm.lower() == 'y':
    # 删除所有报价历史
    db.query(QuoteHistory).delete()
    # 删除所有报价
    db.query(Quote).delete()
    # 提交更改
    db.commit()
    print("所有报价数据已删除！")
else:
    print("操作已取消。")

# 再次统计报价数量
new_count = db.query(Quote).count()
print(f"删除后报价数量: {new_count}")
