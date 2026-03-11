# Umaai

赛马娘资料站与后台工具的单仓库项目。

现在仓库被拆成两层产品：

- 公开站：角色发现页、详情页、排行页、对比页
- 后台：`/admin` 下的数据抓取、生成与任务日志

## 目录结构

- `frontend/`
  - React + Vite + TypeScript 前端
  - 构建产物输出到 `static/`
- `backend/`
  - Python 本地服务
  - 提供公开站 API、后台任务 API、SPA 静态托管
- `dataFetcher/`
  - 原始数据抓取脚本
- `dataGenerator/`
  - 派生数据生成脚本
- `uma/`
  - 角色原始资料与立绘
- `data/`
  - 生成出的数据文件
- `tests/`
  - 当前最小单元测试

## 首次安装

### 前端

```bash
cd frontend
npm install
```

### 抓图环境变量

`fetch_uma_chara` 不再把 microCMS key 写死在仓库里。

```bash
cp .env.example .env
export UMA_MICROCMS_API_KEY=你的_key
```

## 运行方式

### 方式 1：构建后由 Python 服务统一托管

```bash
cd frontend
npm run build
cd ..
python3 -m backend.server --host 127.0.0.1 --port 8787
```

打开：

```text
http://127.0.0.1:8787
```

### 方式 2：前端开发模式

终端 1：

```bash
python3 -m backend.server --host 127.0.0.1 --port 8787
```

终端 2：

```bash
cd frontend
npm run dev
```

Vite 会把 `/api` 和 `/uma` 代理到本地 Python 服务。

## 页面路由

- `/`
- `/characters/:slug`
- `/rankings`
- `/compare`
- `/admin`

## 公开站 API

- `GET /api/health`
- `GET /api/site/overview`
- `GET /api/site/filter-meta`
- `GET /api/site/characters`
- `GET /api/site/characters/{slug}`
- `GET /api/site/rankings`
- `GET /api/site/relations`
- `GET /api/site/compare?slugs=a,b`

## 后台 API

- `GET /api/admin/overview`
- `GET /api/admin/quality`
- `GET /api/admin/jobs`
- `GET /api/admin/jobs/{id}`
- `POST /api/admin/jobs/{id}/retry`
- `POST /api/admin/actions/fetch_info`
- `POST /api/admin/actions/fetch_chara`
- `POST /api/admin/actions/build_body_metrics`
- `POST /api/admin/actions/build_site_bundle`

## 数据脚本

```bash
python3 -m dataFetcher.fetch_uma_info
python3 -m dataFetcher.fetch_uma_chara
python3 -m dataGenerator.build_body_metrics
python3 -m dataGenerator.build_site_bundle --output-dir data
```

## 持久化任务

- 后台任务现在会写入 `data/umaai_jobs.sqlite3`
- 服务重启后，历史任务和日志仍然保留
- 运行中断的任务会在下次启动时被标记为 `error`

## 测试

```bash
python3 -m unittest discover -s tests
```
