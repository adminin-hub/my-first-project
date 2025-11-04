"""
数据库操作模块
负责数据库的初始化、连接和查询执行
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class Database:
    """数据库操作类"""
    
    def __init__(self, db_path: str = "database/ecommerce.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        执行 SQL 查询并返回结果
        
        Args:
            sql: SQL 查询语句
            
        Returns:
            Dict 包含查询结果和元信息
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                
                # 获取列名
                columns = [description[0] for description in cursor.description] if cursor.description else []
                
                # 获取所有行
                rows = cursor.fetchall()
                
                # 转换为字典列表
                results = [dict(row) for row in rows]
                
                return {
                    'success': True,
                    'columns': columns,
                    'data': results,
                    'row_count': len(results)
                }
        except sqlite3.Error as e:
            return {
                'success': False,
                'error': str(e),
                'columns': [],
                'data': [],
                'row_count': 0
            }
    
    def validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        验证 SQL 语句的语法和安全性
        
        Args:
            sql: SQL 查询语句
            
        Returns:
            (是否有效, 错误信息)
        """
        # 安全过滤：只允许 SELECT 查询
        sql_upper = sql.strip().upper()
        
        # 检查是否包含危险的SQL操作
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f'不允许执行 {keyword} 操作，仅支持 SELECT 查询'
        
        # 移除末尾的分号（EXPLAIN QUERY PLAN 不需要）
        sql_clean = sql.rstrip(';').strip()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 使用 EXPLAIN 验证语法，不实际执行
                cursor.execute(f"EXPLAIN QUERY PLAN {sql_clean}")
                return True, None
        except sqlite3.Error as e:
            return False, str(e)
    
    def get_schema_info(self) -> str:
        """
        获取数据库的 schema 信息，用于构建 prompt
        
        Returns:
            schema 信息的字符串描述
        """
        schema_info = []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                schema_info.append(f"\n## 表名: {table_name}")
                
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema_info.append("列信息:")
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, pk = col
                    schema_info.append(f"  - {col_name} ({col_type})")
                    if pk:
                        schema_info[-1] += " [主键]"
                    if not_null:
                        schema_info[-1] += " [非空]"
                    if default_val:
                        schema_info[-1] += f" [默认值: {default_val}]"
                
                # 获取外键信息
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = cursor.fetchall()
                
                if foreign_keys:
                    schema_info.append("外键关系:")
                    for fk in foreign_keys:
                        schema_info.append(f"  - {fk[3]} -> {fk[2]}.{fk[4]}")
        
        return "\n".join(schema_info)
    
    def init_database(self):
        """
        初始化数据库：创建表和插入示例数据
        """
        # 读取 schema.sql
        schema_file = "database/schema.sql"
        sample_data_file = "database/sample_data.sql"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 执行 schema 脚本
            if os.path.exists(schema_file):
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    # 分割多个 SQL 语句并执行
                    for statement in schema_sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            cursor.execute(statement)
            
            # 检查是否已有数据
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            # 如果没有数据，插入示例数据
            if user_count == 0 and os.path.exists(sample_data_file):
                with open(sample_data_file, 'r', encoding='utf-8') as f:
                    sample_sql = f.read()
                    for statement in sample_sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            try:
                                cursor.execute(statement)
                            except sqlite3.Error as e:
                                print(f"插入数据时出错: {e}")
                                continue


def init_database():
    """初始化数据库的便捷函数"""
    db = Database()
    db.init_database()
    print("数据库初始化完成！")


if __name__ == "__main__":
    init_database()

