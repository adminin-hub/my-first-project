"""
测试示例脚本
用于测试 Text-to-SQL 系统的功能
"""

from text_to_sql import TextToSQL
from database import Database


def test_examples():
    """测试示例问题"""
    
    print("=" * 60)
    print("Text-to-SQL 系统测试")
    print("=" * 60)
    print()
    
    # 初始化转换器
    print("正在初始化 Text-to-SQL 转换器...")
    try:
        converter = TextToSQL()
    except Exception as e:
        print(f"初始化失败: {e}")
        print("提示：请确保已正确安装依赖并下载模型")
        return
    
    # 测试问题列表
    test_questions = [
        "查询所有用户信息",
        "查找价格高于5000的商品",
        "统计每个用户的订单总数",
        "查询所有订单的详细信息，包括用户名和商品名",
        "找出订单金额最高的订单详情",
        "查询库存低于50的商品",
        "统计每个商品类别的平均价格",
    ]
    
    print("\n开始测试...")
    print("-" * 60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n测试 {i}/{len(test_questions)}")
        print(f"问题: {question}")
        print("-" * 60)
        
        # 执行转换
        result = converter.convert(question)
        
        # 显示结果
        if result['success']:
            print(f"✅ 成功")
            print(f"生成的 SQL: {result['sql']}")
            if result.get('summary'):
                print(f"结果总结: {result['summary']}")
            
            if result.get('result') and result['result'].get('data'):
                data = result['result']['data']
                print(f"查询结果: 共 {result['result']['row_count']} 条记录")
                if len(data) > 0:
                    print("前 3 条记录:")
                    for row in data[:3]:
                        print(f"  {row}")
        else:
            print(f"❌ 失败")
            print(f"错误: {result.get('error', '未知错误')}")
        
        print()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)


def test_database():
    """测试数据库功能"""
    print("\n测试数据库功能...")
    db = Database()
    
    # 测试查询
    result = db.execute_query("SELECT COUNT(*) as user_count FROM users")
    print(f"用户总数: {result['data'][0]['user_count']}")
    
    result = db.execute_query("SELECT COUNT(*) as product_count FROM products")
    print(f"商品总数: {result['data'][0]['product_count']}")
    
    result = db.execute_query("SELECT COUNT(*) as order_count FROM orders")
    print(f"订单总数: {result['data'][0]['order_count']}")


if __name__ == "__main__":
    # 先测试数据库
    test_database()
    
    # 然后测试 Text-to-SQL（需要模型加载，可能需要较长时间）
    print("\n注意：Text-to-SQL 测试需要加载模型，可能需要几分钟时间...")
    response = input("是否继续测试 Text-to-SQL？(y/n): ")
    
    if response.lower() == 'y':
        test_examples()
    else:
        print("跳过 Text-to-SQL 测试")






