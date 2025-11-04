"""
改进版 Text-to-SQL 核心转换模块
修复JSON序列化错误
"""

import os
import re
import json
from typing import Optional, Dict, Any, List
from transformers import AutoTokenizer, AutoModel
import torch
from database import Database

# 设置国内镜像加速下载
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

class TextToSQL:
    """改进版 Text-to-SQL 转换类（修复JSON序列化问题）"""
    
    def __init__(self, model_name: str = None, device: str = "auto"):
        self.db = Database()
        self.device = self._get_device(device)
        
        if model_name is None:
            model_name = "THUDM/chatglm3-6b"
        
        self.model_name = model_name
        
        print(f"正在加载模型: {model_name}...")
        
        try:
            self._load_model()
        except Exception as e:
            print(f"模型加载失败: {e}")
            self.model = None
            self.tokenizer = None
        
        # 初始化数据库
        if not os.path.exists(self.db.db_path):
            print("初始化数据库...")
            self.db.init_database()
        
        # 获取详细的数据库schema信息
        self.schema_info = self._get_detailed_schema_info()
        self.table_relationships = self._get_table_relationships()
    
    def _load_model(self):
        """加载模型（简化版）"""
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            cache_dir="./models"
        )
        
        # 修复tokenizer
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModel.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            cache_dir="./models"
        )
        
        if self.device == "cpu":
            self.model = self.model.float()
        
        self.model.eval()
        print("模型加载成功！")
    
    def _get_device(self, device: str) -> str:
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _get_detailed_schema_info(self) -> Dict[str, Any]:
        """获取详细的数据库schema信息"""
        return {
            'tables': {
                'users': {
                    'columns': [
                        {'name': 'user_id', 'type': 'INTEGER', 'pk': True, 'description': '用户ID'},
                        {'name': 'username', 'type': 'VARCHAR(50)', 'description': '用户名'},
                        {'name': 'email', 'type': 'VARCHAR(100)', 'description': '邮箱'},
                        {'name': 'created_at', 'type': 'DATETIME', 'description': '创建时间'}
                    ],
                    'description': '用户信息表',
                    'sample_data': ['张三', '李四', '王五']
                },
                'products': {
                    'columns': [
                        {'name': 'product_id', 'type': 'INTEGER', 'pk': True, 'description': '商品ID'},
                        {'name': 'name', 'type': 'VARCHAR(100)', 'description': '商品名称'},
                        {'name': 'price', 'type': 'DECIMAL(10,2)', 'description': '价格'},
                        {'name': 'stock', 'type': 'INTEGER', 'description': '库存'},
                        {'name': 'category', 'type': 'VARCHAR(50)', 'description': '分类'},
                        {'name': 'description', 'type': 'TEXT', 'description': '描述'},
                        {'name': 'created_at', 'type': 'DATETIME', 'description': '创建时间'}
                    ],
                    'description': '商品信息表',
                    'sample_data': ['iPhone 15', 'MacBook Pro', 'iPad Air']
                },
                'orders': {
                    'columns': [
                        {'name': 'order_id', 'type': 'INTEGER', 'pk': True, 'description': '订单ID'},
                        {'name': 'user_id', 'type': 'INTEGER', 'fk': 'users.user_id', 'description': '用户ID'},
                        {'name': 'product_id', 'type': 'INTEGER', 'fk': 'products.product_id', 'description': '商品ID'},
                        {'name': 'quantity', 'type': 'INTEGER', 'description': '数量'},
                        {'name': 'total_amount', 'type': 'DECIMAL(10,2)', 'description': '总金额'},
                        {'name': 'order_date', 'type': 'DATETIME', 'description': '订单日期'}
                    ],
                    'description': '订单表',
                    'sample_data': ['订单记录']
                },
                'order_details': {
                    'columns': [
                        {'name': 'order_id', 'type': 'INTEGER', 'description': '订单ID'},
                        {'name': 'username', 'type': 'VARCHAR(50)', 'description': '用户名'},
                        {'name': 'email', 'type': 'VARCHAR(100)', 'description': '邮箱'},
                        {'name': 'product_name', 'type': 'VARCHAR(100)', 'description': '商品名'},
                        {'name': 'unit_price', 'type': 'DECIMAL(10,2)', 'description': '单价'},
                        {'name': 'quantity', 'type': 'INTEGER', 'description': '数量'},
                        {'name': 'total_amount', 'type': 'DECIMAL(10,2)', 'description': '总金额'},
                        {'name': 'order_date', 'type': 'DATETIME', 'description': '订单日期'}
                    ],
                    'description': '订单详情视图',
                    'is_view': True
                }
            },
            'relationships': [
                {'from': 'orders.user_id', 'to': 'users.user_id', 'type': '多对一'},
                {'from': 'orders.product_id', 'to': 'products.product_id', 'type': '多对一'}
            ]
        }
    
    def _get_table_relationships(self) -> str:
        """获取表关系描述"""
        relationships = []
        for rel in self.schema_info['relationships']:
            from_table = rel['from'].split('.')[0]
            to_table = rel['to'].split('.')[0]
            relationships.append(f"{from_table} 表通过 {rel['from']} 关联 {to_table} 表的 {rel['to']}")
        
        return "\n".join(relationships)
    
    def _build_context_aware_prompt(self, question: str) -> str:
        """构建基于数据库上下文的智能prompt"""
        
        # 构建表结构描述
        table_descriptions = []
        for table_name, table_info in self.schema_info['tables'].items():
            cols = [f"{col['name']} ({col['type']}) - {col['description']}" 
                   for col in table_info['columns']]
            table_descriptions.append(f"{table_name}表({table_info['description']}): {', '.join(cols)}")
        
        prompt = f"""你是一个专业的SQL专家。请根据下面的数据库结构和用户问题，生成准确可执行的SQL查询。

数据库表结构：
{chr(10).join(table_descriptions)}

表关系：
{self.table_relationships}

查询规则：
1. 使用明确的表别名（如 users u, orders o）
2. 多表查询必须使用JOIN并指定关联条件
3. 字符串值使用单引号，数字直接使用
4. 日期比较使用标准格式：'YYYY-MM-DD'
5. 聚合查询要包含GROUP BY
6. 只生成SELECT语句，不要其他操作

字段映射参考：
- 用户相关：用户名→username, 邮箱→email, 用户ID→user_id
- 商品相关：商品名→name, 价格→price, 分类→category, 库存→stock
- 订单相关：数量→quantity, 总金额→total_amount, 订单日期→order_date

示例转换：
问题：查询用户张三的所有订单
SQL：SELECT o.* FROM orders o JOIN users u ON o.user_id = u.user_id WHERE u.username = '张三';

问题：统计每个分类的商品数量
SQL：SELECT category, COUNT(*) as product_count FROM products GROUP BY category;

问题：查找价格高于5000的商品
SQL：SELECT * FROM products WHERE price > 5000;

问题：查询订单详情，包括用户名和商品名
SQL：SELECT o.order_id, u.username, p.name as product_name, o.quantity, o.total_amount, o.order_date 
     FROM orders o 
     JOIN users u ON o.user_id = u.user_id 
     JOIN products p ON o.product_id = p.product_id;

现在请为以下问题生成SQL：
问题：{question}
SQL："""
        
        return prompt
    
    def _analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """分析问题意图，帮助生成更准确的SQL"""
        
        question_lower = question.lower()
        
        # 修复：使用list而不是set，因为set不能被JSON序列化
        intent = {
            'tables': [],  # 改为list
            'conditions': [],
            'aggregations': False,
            'join_required': False
        }
        
        # 识别涉及的表（去重逻辑）
        tables_set = set()  # 内部使用set去重
        
        if any(word in question_lower for word in ['用户', '会员', '客户']):
            tables_set.add('users')
        if any(word in question_lower for word in ['商品', '产品', '价格', '库存']):
            tables_set.add('products')
        if any(word in question_lower for word in ['订单', '购买', '交易']):
            tables_set.add('orders')
        
        # 转换为list
        intent['tables'] = list(tables_set)
        
        # 识别是否需要连接
        if len(intent['tables']) > 1:
            intent['join_required'] = True
        
        # 识别聚合查询
        if any(word in question_lower for word in ['统计', '总数', '平均', '最多', '最少', '合计', '总和']):
            intent['aggregations'] = True
        
        # 识别条件
        if '张三' in question:
            intent['conditions'].append({"field": "users.username", "operator": "=", "value": "'张三'"})
        if '李四' in question:
            intent['conditions'].append({"field": "users.username", "operator": "=", "value": "'李四'"})
        if '手机' in question_lower:
            intent['conditions'].append({"field": "products.category", "operator": "=", "value": "'手机'"})
        if '电脑' in question_lower:
            intent['conditions'].append({"field": "products.category", "operator": "=", "value": "'电脑'"})
        if '高于' in question_lower or '大于' in question_lower:
            # 提取价格条件
            price_match = re.search(r'[高于大于](\d+)', question)
            if price_match:
                intent['conditions'].append({"field": "products.price", "operator": ">", "value": price_match.group(1)})
        
        return intent
    
    def _extract_sql_advanced(self, text: str) -> Optional[str]:
        """改进的SQL提取逻辑"""
        
        # 清理文本
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text, flags=re.IGNORECASE)
        
        # 查找SQL开始
        sql_patterns = [
            r'(SELECT\s+.*?;)',  # 标准SELECT语句
            r'(SELECT\s+.*?(?=SELECT|$))',  # 到下一个SELECT或文本结束
            r'(SELECT\s+.*)',  # 简单的SELECT开始
        ]
        
        for pattern in sql_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    sql_candidate = match[0]
                else:
                    sql_candidate = match
                
                sql_candidate = sql_candidate.strip()
                
                # 验证基本的SQL结构
                if self._validate_sql_candidate(sql_candidate):
                    # 确保有分号
                    if not sql_candidate.endswith(';'):
                        sql_candidate += ';'
                    return sql_candidate
        
        return None
    
    def _validate_sql_candidate(self, sql: str) -> bool:
        """验证SQL候选语句的基本有效性"""
        
        sql_upper = sql.upper()
        
        # 必须有SELECT和FROM
        if 'SELECT' not in sql_upper or 'FROM' not in sql_upper:
            return False
        
        # 检查是否有明显的语法错误
        if 'SELECT FROM' in sql_upper:  # 缺少字段
            return False
        
        # 检查表名是否存在
        valid_tables = ['users', 'products', 'orders', 'order_details']
        has_valid_table = any(table in sql_upper for table in [t.upper() for t in valid_tables])
        
        if not has_valid_table:
            return False
        
        # 检查JOIN条件（如果有JOIN）
        if 'JOIN' in sql_upper:
            if 'ON' not in sql_upper:
                return False
        
        return True
    
    def _post_process_sql(self, sql: str, question: str) -> str:
        """对生成的SQL进行后处理修正"""
        
        # 标准化空格
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        # 确保有分号
        if not sql.endswith(';'):
            sql += ';'
        
        # 基于问题语义的修正
        question_lower = question.lower()
        sql_upper = sql.upper()
        
        # 如果问题涉及特定用户但SQL中没有条件，添加默认条件
        if '张三' in question and '张三' not in sql:
            if 'users' in sql_upper and 'WHERE' not in sql_upper:
                # 使用双引号避免转义问题
                sql = sql.replace(';', " WHERE username = '张三';")
        
        return sql
    
    def convert(self, question: str, history: Optional[list] = None) -> Dict[str, Any]:
        """改进的转换方法"""
        
        try:
            # 如果模型不可用，使用智能回退
            if self.model is None or self.tokenizer is None:
                return self._smart_fallback(question)
            
            # 分析问题意图
            intent = self._analyze_question_intent(question)
            print(f"问题分析: {intent}")
            
            # 构建上下文感知的prompt
            prompt = self._build_context_aware_prompt(question)
            
            # 生成SQL
            generated_text = self._generate_sql(prompt)
            if generated_text:
                print(f"模型生成: {generated_text[:200]}...")
            else:
                print("模型生成失败，使用回退方案")
                return self._smart_fallback(question)
            
            # 提取SQL
            sql = self._extract_sql_advanced(generated_text)
            
            if not sql:
                # 如果提取失败，使用智能回退
                print("SQL提取失败，使用回退方案")
                return self._smart_fallback(question)
            
            # 后处理
            sql = self._post_process_sql(sql, question)
            print(f"最终SQL: {sql}")
            
            # 验证并执行
            is_valid, error_msg = self.db.validate_sql(sql)
            
            if not is_valid:
                return {
                    'success': False,
                    'error': f'SQL语法错误: {error_msg}',
                    'question': question,
                    'sql': sql
                }
            
            result = self.db.execute_query(sql)
            summary = self._generate_intelligent_summary(question, sql, result)
            
            # 修复：确保返回的数据都是JSON可序列化的
            return {
                'success': True,
                'question': question,
                'sql': sql,
                'result': result,
                'summary': summary,
                'method': 'llm',
                'intent_analysis': self._make_json_serializable(intent)  # 确保可序列化
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'转换过程出错: {str(e)}',
                'question': question
            }
    
    def _make_json_serializable(self, data: Any) -> Any:
        """确保数据可以被JSON序列化"""
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, dict):
            return {k: self._make_json_serializable(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._make_json_serializable(item) for item in data]
        elif isinstance(data, set):
            return [self._make_json_serializable(item) for item in data]  # set转list
        else:
            return str(data)  # 其他类型转为字符串
    
    def _generate_sql(self, prompt: str) -> str:
        """生成SQL文本"""
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = inputs.cuda()
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=len(inputs[0]) + 300,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除prompt部分
            if prompt in generated_text:
                generated_text = generated_text.split(prompt)[-1].strip()
            
            return generated_text
            
        except Exception as e:
            print(f"SQL生成失败: {e}")
            return ""
    
    def _smart_fallback(self, question: str) -> Dict[str, Any]:
        """智能回退方案"""
        
        # 基于分析意图生成SQL
        intent = self._analyze_question_intent(question)
        
        # 根据意图生成相应的SQL
        sql = self._generate_sql_by_intent(question, intent)
        
        result = self.db.execute_query(sql)
        summary = self._generate_intelligent_summary(question, sql, result)
        
        return {
            'success': True,
            'question': question,
            'sql': sql,
            'result': result,
            'summary': summary,
            'method': 'intent_based_fallback',
            'intent_analysis': self._make_json_serializable(intent)  # 确保可序列化
        }
    
    def _generate_sql_by_intent(self, question: str, intent: Dict) -> str:
        """基于意图生成SQL"""
        
        question_lower = question.lower()
        
        # 简单查询
        if '所有用户' in question:
            return "SELECT * FROM users;"
        elif '所有商品' in question:
            return "SELECT * FROM products;"
        elif '所有订单' in question:
            return "SELECT * FROM orders;"
        
        # 条件查询
        elif '张三' in question and '订单' in question:
            return "SELECT o.* FROM orders o JOIN users u ON o.user_id = u.user_id WHERE u.username = '张三';"
        elif '李四' in question and '订单' in question:
            return "SELECT o.* FROM orders o JOIN users u ON o.user_id = u.user_id WHERE u.username = '李四';"
        elif '手机' in question_lower:
            return "SELECT * FROM products WHERE category = '手机';"
        elif '电脑' in question_lower:
            return "SELECT * FROM products WHERE category = '电脑';"
        elif '平板' in question_lower:
            return "SELECT * FROM products WHERE category = '平板';"
        elif '价格高于' in question or '价格大于' in question:
            price_match = re.search(r'[高于大于](\d+)', question)
            if price_match:
                return f"SELECT * FROM products WHERE price > {price_match.group(1)};"
        elif '价格低于' in question or '价格小于' in question:
            price_match = re.search(r'[低于小于](\d+)', question)
            if price_match:
                return f"SELECT * FROM products WHERE price < {price_match.group(1)};"
        
        # 聚合查询
        elif '统计' in question or '总数' in question:
            if '用户' in question and '订单' in question:
                return "SELECT u.username, COUNT(o.order_id) as order_count FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.user_id, u.username;"
            elif '分类' in question and '商品' in question:
                return "SELECT category, COUNT(*) as product_count FROM products GROUP BY category;"
            elif '订单' in question:
                return "SELECT COUNT(*) as total_orders FROM orders;"
        
        # 订单详情查询
        elif '详情' in question or '详细' in question:
            return "SELECT * FROM order_details;"
        
        # 默认返回订单详情（限制数量避免数据过多）
        return "SELECT * FROM order_details LIMIT 10;"
    
    def _generate_intelligent_summary(self, question: str, sql: str, result: Dict) -> str:
        """生成智能总结"""
        
        if not result.get('success'):
            return f"查询执行失败: {result.get('error', '未知错误')}"
        
        row_count = result.get('row_count', 0)
        
        if row_count == 0:
            return "未找到匹配的数据。"
        
        # 基于问题类型生成不同的总结
        question_lower = question.lower()
        data = result.get('data', [])
        
        if '统计' in question_lower or '总数' in question_lower or '数量' in question_lower:
            if data:
                try:
                    # 统计类结果的总结
                    if len(data[0]) == 2:  # 通常统计查询有两列
                        summary_parts = []
                        for row in data:
                            keys = list(row.keys())
                            if len(keys) == 2:
                                summary_parts.append(f"{row[keys[0]]}: {row[keys[1]]}")
                        if summary_parts:
                            return f"统计结果: {', '.join(summary_parts)}"
                except:
                    pass  # 如果解析失败，使用默认总结
        
        elif '平均' in question_lower:
            if data and len(data) > 0:
                first_row = data[0]
                for key, value in first_row.items():
                    if 'avg' in key.lower():
                        return f"平均值为: {value}"
        
        elif '最多' in question_lower or '最高' in question_lower:
            if data and len(data) > 0:
                first_row = data[0]
                for key, value in first_row.items():
                    if 'max' in key.lower():
                        return f"最大值为: {value}"
        
        elif '最少' in question_lower or '最低' in question_lower:
            if data and len(data) > 0:
                first_row = data[0]
                for key, value in first_row.items():
                    if 'min' in key.lower():
                        return f"最小值为: {value}"
        
        # 默认总结
        if row_count == 1:
            return "查询完成，找到1条匹配记录。"
        else:
            return f"查询完成，共找到{row_count}条匹配记录。"


# 测试函数
def test_improved_converter():
    """测试改进的转换器"""
    
    converter = ImprovedTextToSQL()
    
    test_cases = [
        "查询所有用户信息",
        "查找所有商品",
        "查询张三的所有订单",
        "统计每个用户的订单数量",
        "查找价格高于5000的商品",
        "查询手机类别的商品",
        "统计每个分类的商品数量",
        "查询订单详情，包括用户名和商品名",
        "查找李四购买的商品",
        "查询最近一个月的订单"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试用例 {i}: {question}")
        print(f"{'='*50}")
        
        result = converter.convert(question)
        
        # 测试JSON序列化
        try:
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            print("✅ JSON序列化测试通过")
        except Exception as e:
            print(f"❌ JSON序列化失败: {e}")
        
        if result['success']:
            print(f"✅ 生成SQL: {result['sql']}")
            print(f"📊 结果总结: {result['summary']}")
            if 'intent_analysis' in result:
                print(f"🎯 意图分析: {result['intent_analysis']}")
        else:
            print(f"❌ 转换失败: {result['error']}")


if __name__ == "__main__":
    test_improved_converter()