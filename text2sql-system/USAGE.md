# 使用指南

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

#### Web 界面（推荐）

```bash
python app.py
```

然后在浏览器中访问：`http://localhost:5000`

#### 命令行测试

```bash
python test_examples.py
```

## 使用示例

### 基础查询

- **问题**：查询所有用户信息
- **SQL**：`SELECT * FROM users;`

- **问题**：查找价格高于5000的商品
- **SQL**：`SELECT * FROM products WHERE price > 5000;`

### 聚合查询

- **问题**：统计每个用户的订单总数
- **SQL**：`SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id;`

### 复杂查询（多表 JOIN）

- **问题**：查询所有订单的详细信息，包括用户名和商品名
- **SQL**：
```sql
SELECT o.order_id, u.username, p.name as product_name, 
       o.quantity, o.total_amount, o.order_date 
FROM orders o 
JOIN users u ON o.user_id = u.user_id 
JOIN products p ON o.product_id = p.product_id;
```

## 注意事项

1. **模型加载**：首次运行需要下载模型（约 6GB），需要网络连接
2. **内存要求**：建议至少 8GB RAM，推荐 16GB
3. **推理速度**：CPU 模式较慢，建议使用 GPU 加速（如可用）
4. **SQL 安全**：系统会自动过滤危险的 SQL 操作，只支持 SELECT 查询

## 常见问题

### Q: 模型加载失败？
A: 检查网络连接，确保能够访问 Hugging Face。如果模型太大，可以考虑使用量化版本。

### Q: 内存不足？
A: 尝试使用较小的模型或启用模型量化（INT8）。

### Q: SQL 生成不准确？
A: 尝试更清晰地描述问题，或者提供更多上下文信息。

### Q: 如何切换模型？
A: 修改 `text_to_sql.py` 中的 `model_name` 参数，例如：
```python
converter = TextToSQL(model_name="THUDM/chatglm3-6b")
```






