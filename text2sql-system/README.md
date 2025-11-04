# Text-to-SQL 系统

基于 ChatGLM 大语言模型的 Text-to-SQL 转换系统

## 📖 项目简介

本项目实现了一个基于 ChatGLM 的 Text-to-SQL 系统，能够将用户的自然语言问题转换为标准的 SQL 查询语句，并执行查询返回格式化结果。系统采用电商领域的示例数据库，包含用户、商品、订单等核心业务表。

**核心特性：**
- 🤖 基于 ChatGLM-6B 大语言模型
- 🔄 自然语言到 SQL 的智能转换
- 🛡️ SQL 安全验证与错误处理
- 🌐 友好的 Web 用户界面
- 📊 查询结果可视化展示

## 📁 项目结构

```
text2sql-system/
├── README.md                 # 项目说明文档
├── USAGE.md                  # 详细使用指南
├── requirements.txt          # Python 依赖包
├── app.py                    # Flask Web 应用主程序
├── text_to_sql.py           # Text-to-SQL 核心转换模块
├── database.py              # 数据库操作模块
├── test_examples.py         # 测试示例脚本
├── database/
│   ├── schema.sql           # 数据库表结构定义
│   ├── sample_data.sql      # 示例数据插入脚本
│   └── ecommerce.db         # SQLite 数据库文件（自动生成）
└── templates/
    └── index.html           # Web 界面模板
```

## ✨ 核心功能

### 1. Text-to-SQL 转换
- 使用 ChatGLM 模型理解自然语言问题
- 基于数据库 schema 生成准确的 SQL 查询
- 支持复杂查询（多表 JOIN、子查询、聚合函数等）

### 2. SQL 验证与执行
- 语法验证和错误检测
- 安全过滤（防止 SQL 注入）
- 格式化结果返回

### 3. Web 用户界面
- 简洁直观的操作界面
- 实时查询执行
- 结果可视化展示

### 4. 数据库 Schema 理解
- 自动读取表结构信息
- 理解表关系和字段含义
- Prompt 工程优化

## 🚀 快速开始

### 系统要求

- Python 3.8+
- 8GB+ RAM（推荐 16GB，用于加载模型）
- GPU 支持（可选，用于加速推理）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/adminin-hub/my-first-project.git
cd text2sql-system
```

2. **创建虚拟环境**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **初始化数据库**
```bash
# 数据库会在首次运行时自动创建
# 或手动执行：
python -c "from database import Database; db = Database(); db.init_database()"
```

5. **下载模型**
```bash
# ChatGLM 模型会自动从 Hugging Face 下载
# 首次运行需要网络连接，模型约 6GB
# 使用国内镜像加速：https://hf-mirror.com
```

## 💻 运行方法

### 方式一：Web 界面（推荐）

```bash
python app.py
```

然后在浏览器中访问：`http://localhost:5000`

### 方式二：命令行测试

```bash
python test_examples.py
```
## 📝 使用示例

### 基础查询

1. **简单查询**
   - 输入：`查询所有商品信息`
   - SQL：`SELECT * FROM products;`

2. **条件查询**
   - 输入：`查找价格高于1000的商品`
   - SQL：`SELECT * FROM products WHERE price > 1000;`

3. **聚合查询**
   - 输入：`统计每个用户的订单总数`
   - SQL：`SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id;`

### 复杂查询

1. **多表 JOIN**
   - 输入：`查询所有订单的详细信息，包括用户名和商品名`
   - SQL：包含 JOIN 多表的复杂查询

2. **子查询**
   - 输入：`找出订单金额最高的订单详情`
   - SQL：包含子查询的 SQL 语句

更多示例请参考 `test_examples.py` 文件。

## 🗄️ 数据库 Schema

系统使用电商数据库，包含以下表：

- **users**: 用户表
  - `user_id` (主键), `username`, `email`, `created_at`

- **products**: 商品表
  - `product_id` (主键), `name`, `price`, `stock`, `category`, `description`, `created_at`

- **orders**: 订单表
  - `order_id` (主键), `user_id` (外键), `product_id` (外键), `quantity`, `total_amount`, `order_date`

- **order_details**: 订单详情视图
  - 包含订单、用户和商品的完整信息

详细表结构见 `database/schema.sql`

## 🔧 技术实现

### 1. 模型选择
- 使用 ChatGLM-6B 作为基础模型
- 通过 Transformers 库加载和推理
- 支持本地部署，保护数据隐私
- 使用 Hugging Face 镜像加速下载

### 2. Prompt 工程
- 构建包含数据库 schema 信息的 prompt
- 提供清晰的示例和指令
- 优化 prompt 以提高 SQL 生成准确率
- 支持上下文感知的提示构建

### 3. SQL 验证机制
- 语法验证（使用 SQLite 解析器）
- 表名和列名验证
- 防止 SQL 注入攻击
- 智能错误提示

### 4. 错误处理
- 捕获模型生成错误
- SQL 执行异常处理
- 用户友好的错误提示
- 智能回退机制

## ✅ 功能特点

### 基础功能
- [x] Text-to-SQL 转换
- [x] SQL 执行和结果返回
- [x] Web 用户界面
- [x] 数据库 Schema 理解

### 进阶功能
- [x] SQL 语法验证
- [x] 错误处理和提示
- [x] 查询结果格式化展示
- [x] API 接口支持

### 高级功能
- [x] 支持复杂查询（JOIN、子查询、聚合）
- [x] 自然语言结果总结
- [x] 智能回退机制
- [x] 性能优化

## 🐛 遇到的挑战和解决方案

### 1. 模型推理速度
**挑战**：ChatGLM 模型较大，推理速度较慢

**解决方案**：
- 实现模型单例模式，避免重复加载
- 考虑使用 GPU 加速（如可用）

### 2. SQL 生成准确性
**挑战**：模型有时生成不正确的 SQL 语句

**解决方案**：
- 优化 prompt，提供更清晰的 schema 信息
- 实现 SQL 验证机制，检测常见错误
- 添加 few-shot 示例提高准确率
- 实现智能回退机制

### 3. 复杂查询支持
**挑战**：多表 JOIN 和复杂子查询生成困难

**解决方案**：
- 在 prompt 中详细说明表关系
- 提供复杂查询的示例
- 实现后处理和验证逻辑

## 🌟 项目亮点

1. **完整的系统架构**：从数据库到前端的完整实现
2. **实用性强**：针对真实业务场景（电商）设计
3. **可扩展性**：易于适配不同数据库和模型
4. **用户体验**：简洁直观的 Web 界面
5. **代码质量**：模块化设计，注释完整
6. **安全可靠**：SQL 注入防护，错误处理完善

## 📈 未来改进方向

- [ ] 支持更多数据库类型（PostgreSQL、MySQL）
- [ ] 实现模型微调，提高特定领域准确率
- [ ] 添加查询历史记录功能
- [ ] 实现结果可视化图表展示
- [ ] 支持多轮对话上下文理解
- [ ] 添加用户认证和权限管理
- [ ] 实现查询性能优化建议

## 📄 许可证

MIT License

## 👤 作者

YUNlong JU





