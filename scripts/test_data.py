#!/usr/bin/env python3
"""测试数据生成脚本"""

import requests
import json
import random

API_URL = 'http://localhost:8000'

# 测试数据配置
TEST_PART_NUMBERS = [
    "A12345",
    "B67890",
    "C24680",
    "D13579"
]

SUPPLIERS = [
    "航空配件有限公司",
    "全球航空材料",
    "蓝天航空部件",
    "精密航空科技",
    "飞翔航空器材"
]

LEAD_TIMES = [
    "2 weeks",
    "3 weeks",
    "4 weeks",
    "6 weeks",
    "8 weeks"
]

# 生成测试数据
def generate_test_data():
    """生成测试数据"""
    test_data = []
    
    for part_number in TEST_PART_NUMBERS:
        # 为每个件号生成多个供应商报价
        for i, supplier in enumerate(SUPPLIERS):
            # 随机价格（美金）
            usd_price = round(random.uniform(100, 1000), 2)
            
            # 随机货币符号
            currency = "$"  # 统一使用美金
            
            # 随机交货期
            lead_time = random.choice(LEAD_TIMES)
            
            # 随机 MOQ
            moq = random.randint(1, 10)
            
            test_data.append({
                "part_number": part_number,
                "supplier_name": supplier,
                "usd_price": usd_price,
                "currency_symbol": currency,
                "lead_time": lead_time,
                "moq": moq
            })
    
    return test_data

# 发送数据到后端
def send_test_data(test_data):
    """发送测试数据到后端"""
    print(f"开始发送 {len(test_data)} 条测试数据...")
    
    for i, data in enumerate(test_data, 1):
        try:
            response = requests.post(
                f"{API_URL}/api/quotes/",
                headers={"Content-Type": "application/json"},
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                print(f"✓ 成功创建报价 {i}/{len(test_data)}: {data['part_number']} - {data['supplier_name']}")
            else:
                print(f"✗ 失败 {i}/{len(test_data)}: {response.text}")
        except Exception as e:
            print(f"✗ 错误 {i}/{len(test_data)}: {e}")

# 获取报价列表
def get_quotes():
    """获取报价列表"""
    try:
        response = requests.get(f"{API_URL}/api/quotes/")
        if response.status_code == 200:
            quotes = response.json()
            print(f"\n获取到 {len(quotes)} 条报价记录")
            for quote in quotes[:5]:  # 显示前 5 条
                print(f"  {quote['id']}: {quote['part_number']} - {quote['supplier_name']} - ${quote['usd_price']} - ￥{quote['cny_price']}")
            if len(quotes) > 5:
                print(f"  ... 还有 {len(quotes) - 5} 条记录")
        else:
            print(f"获取失败: {response.text}")
    except Exception as e:
        print(f"错误: {e}")

# 测试比价功能
def test_comparison():
    """测试比价功能"""
    print("\n测试比价功能...")
    
    for part_number in TEST_PART_NUMBERS:
        try:
            response = requests.get(f"{API_URL}/api/quotes/comparison/{part_number}")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {part_number}: 共 {data['supplier_count']} 家供应商")
                if data['min_cny_price']:
                    print(f"  最低人民币单价: ￥{data['min_cny_price']:.2f}")
            else:
                print(f"✗ {part_number}: {response.text}")
        except Exception as e:
            print(f"✗ {part_number}: {e}")

# 主函数
def main():
    """主函数"""
    print("=====================================")
    print("航空零件采购比价系统 - 测试数据生成")
    print("=====================================")
    
    # 生成测试数据
    test_data = generate_test_data()
    print(f"生成了 {len(test_data)} 条测试数据")
    
    # 发送数据
    send_test_data(test_data)
    
    # 获取报价列表
    get_quotes()
    
    # 测试比价
    test_comparison()
    
    print("\n=====================================")
    print("测试完成！")
    print("请打开前端页面查看结果:")
    print("c:\\Users\\123\\Desktop\\AI-coding\\frontend\\static.html")
    print("=====================================")

if __name__ == "__main__":
    main()
