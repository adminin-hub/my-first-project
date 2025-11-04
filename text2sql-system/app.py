"""
Flask Web 应用主程序
提供 Text-to-SQL 的 Web 界面和 API 接口
"""

from flask import Flask, render_template, request, jsonify
import os
import sys
from text_to_sql import TextToSQL
from database import Database

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支持中文 JSON

# 全局变量存储转换器（避免重复加载模型）
converter = None


def get_converter():
    """获取 Text-to-SQL 转换器实例（单例模式）"""
    global converter
    if converter is None:
        try:
            converter = TextToSQL()
        except Exception as e:
            print(f"初始化转换器失败: {e}")
            print("提示：请确保已正确安装依赖并下载模型")
            return None
    return converter


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """
    API 接口：处理 Text-to-SQL 查询
    
    请求格式:
    {
        "question": "用户的问题",
        "history": []  // 可选，对话历史
    }
    
    响应格式:
    {
        "success": true/false,
        "question": "用户问题",
        "sql": "生成的SQL",
        "result": {...},
        "summary": "结果总结",
        "error": "错误信息"  // 如果失败
    }
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': '问题不能为空'
            }), 400
        
        # 获取转换器
        conv = get_converter()
        if conv is None:
            return jsonify({
                'success': False,
                'error': '系统初始化失败，请检查模型是否已加载'
            }), 500
        
        # 获取对话历史（可选）
        history = data.get('history', [])
        
        # 执行转换
        result = conv.convert(question, history)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/schema', methods=['GET'])
def get_schema():
    """
    API 接口：获取数据库 schema 信息
    """
    try:
        db = Database()
        schema_info = db.get_schema_info()
        
        return jsonify({
            'success': True,
            'schema': schema_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取 schema 失败: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    conv = get_converter()
    return jsonify({
        'status': 'healthy',
        'model_loaded': conv is not None
    })


if __name__ == '__main__':
    # 确保数据库目录存在
    os.makedirs('database', exist_ok=True)
    
    # 初始化数据库（如果不存在）
    db = Database()
    if not os.path.exists(db.db_path):
        print("初始化数据库...")
        db.init_database()
    
    print("=" * 50)
    print("Text-to-SQL 系统启动中...")
    print("=" * 50)
    print("\n访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务\n")
    
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5000, debug=True)

