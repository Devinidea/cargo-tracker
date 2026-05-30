# 📦 Cargo Tracker - 海运清单管理工具

再也不用忘记海运箱子里装了什么。

## 功能

- ✅ 创建海运记录，管理多次海运
- 📦 箱子管理（分箱打包，井井有条）
- 📷 截图 OCR 识别（淘宝/拼多多订单截图 AI 自动识别商品）
- ✔️ 到货验收（一键打勾确认每件商品都到了）
- 💰 价值统计（记录每件商品的价值）
- 📱 响应式设计（手机/电脑都能用）

## 部署（Synology NAS）

### 方式一：Docker Compose（推荐）

```bash
# 1. 创建数据目录
mkdir -p /volume1/docker/cargo-tracker/data

# 2. 复制并编辑环境配置
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY

# 3. 启动
docker-compose up -d

# 4. 访问
# http://你的NAS_IP:5180
```

### 方式二：手动 Docker

```bash
docker run -d \
  --name cargo-tracker \
  --restart unless-stopped \
  -p 5180:5180 \
  -v /volume1/docker/cargo-tracker/data:/data \
  -e MINIMAX_API_KEY=你的密钥 \
  ghcr.io/devinidea/cargo-tracker:latest
```

### 方式三：本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export MINIMAX_API_KEY=你的密钥

# 运行
python app.py
# 访问 http://localhost:5180
```

## 配置

| 环境变量 | 必须 | 说明 |
|---------|------|------|
| `MINIMAX_API_KEY` | 是 | MiniMax API Key，用于 OCR 识别 |

获取 MiniMax API Key: https://platform.minimax.chat/

## 截图预览

```
┌─────────────────────────────┐
│ 📦 海运清单                 │
├─────────────────────────────┤
│  ● 海运记录   + 新建海运     │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ 2025年5月家具海运        │ │
│ │ [运输中]  3箱·42件·¥12500│ │
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │ 2025年3月海运            │ │
│ │ [已到达]  5箱·89件·¥28000│ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

## 数据存储

所有数据存储在 SQLite 数据库中：
- 路径：`/data/cargo_tracker.db`
- 建议定期备份此文件

## 技术栈

- 后端：Python Flask + SQLite
- 前端：原生 HTML/CSS/JS（零依赖）
- OCR：MiniMax Vision API
- 部署：Docker
