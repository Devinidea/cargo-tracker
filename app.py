"""
Cargo Tracker - Flask 后端 API
海运清单管理工具
"""

import os
import re
import base64
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from db_schema import (
    init_db,
    cleanup_orphans,
    # 海运
    create_shipment, get_shipments, get_shipment, update_shipment_status, delete_shipment,
    # 箱子
    create_box, get_boxes, get_box, update_box, delete_box,
    # 商品
    create_item, get_items, get_items_by_shipment, update_item, delete_item, toggle_item_checked,
    # 统计
    get_shipment_stats
)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# MiniMax API 配置
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")

# 确保数据库目录存在
DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

# 初始化数据库
init_db()

# 启动时清理孤儿数据（B1 修复后的一次性兜底）
_cleanup_result = cleanup_orphans()
if _cleanup_result["boxes"] or _cleanup_result["items"]:
    print(
        f"启动清理：删除 {_cleanup_result['boxes']} 个孤儿 boxes、"
        f"{_cleanup_result['items']} 个孤儿 items",
        flush=True,
    )


# ============ 静态文件 ============

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


# ============ 健康检查 ============

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


# ============ 海运记录 API ============

@app.route('/api/shipments', methods=['GET'])
def api_get_shipments():
    """获取所有海运记录"""
    status = request.args.get('status')
    shipments = get_shipments(status)
    # 附加统计信息
    for s in shipments:
        s['stats'] = get_shipment_stats(s['id'])
    return jsonify({"success": True, "data": shipments})


@app.route('/api/shipments/<int:shipment_id>', methods=['GET'])
def api_get_shipment(shipment_id):
    """获取单个海运详情"""
    shipment = get_shipment(shipment_id)
    if not shipment:
        return jsonify({"success": False, "error": "不存在"}), 404
    
    shipment['stats'] = get_shipment_stats(shipment_id)
    shipment['boxes'] = []
    for box in get_boxes(shipment_id):
        box['items'] = get_items(box['id'])
        shipment['boxes'].append(box)
    
    return jsonify({"success": True, "data": shipment})


@app.route('/api/shipments', methods=['POST'])
def api_create_shipment():
    """创建海运记录"""
    data = request.get_json()
    name = data.get('name', '').strip()
    notes = data.get('notes', '')
    
    if not name:
        return jsonify({"success": False, "error": "名称不能为空"}), 400
    
    shipment_id = create_shipment(name, notes)
    return jsonify({"success": True, "data": {"id": shipment_id}})


@app.route('/api/shipments/<int:shipment_id>/status', methods=['PUT'])
def api_update_shipment_status(shipment_id):
    """更新海运状态"""
    data = request.get_json()
    status = data.get('status')
    if status not in ('shipping', 'arrived', 'cancelled'):
        return jsonify({"success": False, "error": "无效状态"}), 400
    
    success = update_shipment_status(shipment_id, status)
    return jsonify({"success": success})


@app.route('/api/shipments/<int:shipment_id>', methods=['DELETE'])
def api_delete_shipment(shipment_id):
    """删除海运记录"""
    success = delete_shipment(shipment_id)
    return jsonify({"success": success})


# ============ 箱子 API ============

@app.route('/api/shipments/<int:shipment_id>/boxes', methods=['POST'])
def api_create_box(shipment_id):
    """创建箱子"""
    data = request.get_json()
    name = data.get('name', '').strip()
    notes = data.get('notes', '')
    
    if not name:
        return jsonify({"success": False, "error": "名称不能为空"}), 400
    
    box_id = create_box(shipment_id, name, notes)
    return jsonify({"success": True, "data": {"id": box_id}})


@app.route('/api/boxes/<int:box_id>', methods=['PUT'])
def api_update_box(box_id):
    """更新箱子"""
    data = request.get_json()
    name = data.get('name')
    notes = data.get('notes')
    
    success = update_box(box_id, name=name, notes=notes)
    return jsonify({"success": success})


@app.route('/api/boxes/<int:box_id>', methods=['DELETE'])
def api_delete_box(box_id):
    """删除箱子"""
    success = delete_box(box_id)
    return jsonify({"success": success})


# ============ 商品 API ============

@app.route('/api/boxes/<int:box_id>/items', methods=['GET'])
def api_get_items(box_id):
    """获取箱内商品"""
    items = get_items(box_id)
    return jsonify({"success": True, "data": items})


@app.route('/api/boxes/<int:box_id>/items', methods=['POST'])
def api_create_item(box_id):
    """添加商品"""
    data = request.get_json()
    name = data.get('name', '').strip()
    quantity = data.get('quantity', 1)
    price = data.get('price')
    source = data.get('source', '')
    order_no = data.get('order_no', '')
    notes = data.get('notes', '')
    
    if not name:
        return jsonify({"success": False, "error": "名称不能为空"}), 400
    
    item_id = create_item(box_id, name, quantity, price, source, order_no, notes)
    return jsonify({"success": True, "data": {"id": item_id}})


@app.route('/api/items/<int:item_id>', methods=['PUT'])
def api_update_item(item_id):
    """更新商品"""
    data = request.get_json()
    
    name = data.get('name')
    quantity = data.get('quantity')
    price = data.get('price')
    notes = data.get('notes')
    checked = data.get('checked')
    
    if checked is not None:
        checked = 1 if checked else 0
    
    success = update_item(
        item_id,
        name=name,
        quantity=quantity,
        price=price,
        notes=notes,
        checked=checked,
    )
    return jsonify({"success": success})


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def api_delete_item(item_id):
    """删除商品"""
    success = delete_item(item_id)
    return jsonify({"success": success})


@app.route('/api/items/<int:item_id>/toggle', methods=['POST'])
def api_toggle_item(item_id):
    """切换验收状态"""
    result = toggle_item_checked(item_id)
    if result is None:
        return jsonify({"success": False, "error": "不存在"}), 404
    return jsonify({"success": True, "data": result})


# ============ AI OCR 识别 ============

@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    """
    接收订单截图，使用 MiniMax AI 识别商品列表
    支持 base64 或 URL 两种方式
    """
    data = request.get_json()
    
    # 支持 base64 图片或 URL
    image_data = data.get('image')
    image_url = data.get('url')
    
    if not image_data and not image_url:
        return jsonify({"success": False, "error": "需要提供 image 或 url"}), 400
    
    if not MINIMAX_API_KEY:
        return jsonify({"success": False, "error": "未配置 MiniMax API Key"}), 500
    
    # 构建提示词
    prompt = """请分析这张订单截图，提取所有商品信息并以 JSON 数组格式返回。

返回格式：
[
  {"name": "商品名称", "quantity": 数量, "price": 价格},
  ...
]

要求：
1. name 只保留商品名称，去除规格型号等
2. quantity 默认为 1
3. price 如果有价格就提取，没有填 null
4. 返回纯 JSON 数组，不要其他文字"""

    try:
        # base64 模式：直接解码到内存
        if image_data:
            # 去除可能的 data:image/xxx;base64, 前缀
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            return _call_minimax_vision(image_bytes, prompt)

        # URL 模式：下载到内存
        elif image_url:
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            return _call_minimax_vision(resp.content, prompt)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _call_minimax_vision(image_bytes: bytes, prompt: str):
    """调用 MiniMax 视觉模型进行 OCR。image_bytes 直接 base64 编码后发送。"""
    import json

    img_b64 = base64.b64encode(image_bytes).decode()

    payload = {
        "prompt": prompt,
        "image_url": f"data:image/jpeg;base64,{img_b64}"
    }

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(
        "https://api.minimax.chat/v1/coding_plan/vlm",
        headers=headers,
        json=payload,
        timeout=120
    )

    if resp.status_code != 200:
        return jsonify({
            "success": False,
            "error": f"API 调用失败: {resp.status_code} - {resp.text}"
        }), 500

    result = resp.json()

    # 检查 API 错误
    if result.get("base_resp", {}).get("status_code") != 0:
        return jsonify({
            "success": False,
            "error": f"API 错误: {result.get('base_resp', {}).get('status_msg', '未知错误')}"
        }), 500

    # 直接返回内容文本
    content = result.get("content", "")

    # 尝试提取 JSON
    json_match = re.search(r'\[.*\]', content, re.DOTALL)
    if json_match:
        try:
            items = json.loads(json_match.group())
            return jsonify({
                "success": True,
                "data": items,
                "raw": content
            })
        except json.JSONDecodeError:
            pass

    return jsonify({
        "success": True,
        "data": [],
        "raw": content,
        "note": "未能解析出商品列表，请手动录入"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5180, debug=True)
