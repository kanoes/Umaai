# Umaai

马娘数据库项目（数据抓取 + 数据生成 + 前端控制台）。

## 目录

- `dataFetcher/`
  - `fetch_uma_info.py`：抓取基础角色数据并更新 `uma/index.json`
  - `fetch_uma_chara.py`：补齐 `chara_img == "No"` 的角色立绘（优先胜负服）
- `dataGenerator/`
  - `build_body_metrics.py`：生成 `data/body_metrics.json`（含腰臀比、腰乳比等排行）
- `backend/`
  - `server.py`：本地 API 服务，前端按钮可直接触发 3 个模块任务
- `web/`
  - 前端页面（赛马娘主题控制台）
- `uma/`
  - 角色原始资料与立绘
- `data/`
  - 前端直接使用的数据产物（当前：`body_metrics.json`）

## 运行方式

1. 启动前后端一体服务：

```bash
python3 -m backend.server --host 127.0.0.1 --port 8787
```

2. 浏览器打开：

```text
http://127.0.0.1:8787
```

## 可单独运行的模块

```bash
python3 -m dataFetcher.fetch_uma_info
python3 -m dataFetcher.fetch_uma_chara
python3 -m dataGenerator.build_body_metrics
```

## API（供前端使用）

- `GET /api/health`
- `GET /api/data/index`
- `GET /api/data/body-metrics`
- `POST /api/actions/fetch_info`
- `POST /api/actions/fetch_chara`
- `POST /api/actions/build_body_metrics`
- `GET /api/jobs`
- `GET /api/jobs/{id}`
