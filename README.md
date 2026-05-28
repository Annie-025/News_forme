# News For Me

本地个人财经新闻与市场信息工作台。项目使用 Streamlit 构建。新闻主路径只依赖本地缓存和示例数据；市场数据由 AKShare 优先提供，开源 tushare 作为备用补充。

## 安装

```bash
cd "/Users/chenxinyu/Documents/news for me/news_forme"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置

在项目根目录创建 `.env`。不要提交这个文件。

```bash
NEWSAPI_KEY=
SERPAPI_API_KEY=
NEWSDATA_API_KEY=

REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=news_forme_local/0.1

X_BEARER_TOKEN=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_IG_USER_ID=
```

没有 API key 时，应用仍会读取 `data/cache/news_cache.json` 或 `data/sample_news.json`。

## 启动

```bash
source .venv/bin/activate
streamlit run app.py
```

访问：

```text
http://localhost:8501
```

本地 JSON API 可单独启动：

```bash
source .venv/bin/activate
python api_server.py --port 8510
```

接口地址：

```text
http://127.0.0.1:8510/api/market
http://127.0.0.1:8510/api/reports
http://127.0.0.1:8510/api/announcements
```

## 数据降级策略

- 新闻：`data/cache/news_cache.json` -> `data/sample_news.json`。新闻路径不调用 AKShare。
- 市场：新鲜 `data/cache/market_cache.json` -> AKShare -> 开源 tushare -> 旧缓存 -> 空状态。
- AI 解读：点击新闻卡片按钮后，本地规则分析按需生成。

缓存文件位于：

```text
data/cache/news_cache.json
data/cache/market_cache.json
```

这些文件是本地运行缓存，可随时删除。

## 使用说明

- 左侧栏是筛选中心，可按分类、关键词、影响/情绪和时间过滤新闻。
- 首页默认优先显示新闻流。
- 首页会显示市场指数和 A 股快照；点击顶部“更新指数”可刷新行情，AKShare 失败不会影响新闻浏览。
- 每条新闻上的“AI 解读”按钮会按需展开本地规则分析。

## 数据层结构

```text
data_sources/
  cache_store.py
  sample_provider.py
  news_service.py
  tushare_provider.py
  report_provider.py
  announcement_provider.py
  analysis_service.py
  akshare_provider.py      # 兼容旧导入
  market_service.py        # 兼容旧导入
src/market/
  market_cache.py
  market_providers.py
  market_service.py
```

AKShare 调用集中在 `src/market/market_providers.py`。开源 tushare 调用仍集中在 `data_sources/tushare_provider.py`，不需要 token。市场聚合在 `src/market/market_service.py`。研报与公告入口分别由 `report_provider.py` 和 `announcement_provider.py` 提供。

## 测试

```bash
./.venv/bin/pytest -q
./.venv/bin/python -m compileall app.py api_server.py data_sources src tests
```
