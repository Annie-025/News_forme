# News For Me

News For Me 是一个面向财经新闻学习与经济学解读的个人财经信息工作台。项目整合市场行情、新闻信息、研报入口和公告入口，并通过标签筛选与重要性排序帮助用户快速定位高价值财经信息。

## Features

- 财经新闻与市场信息聚合
- AKShare / Tushare 数据源支持
- 标签筛选与重要性排序
- 研报中心入口
- 年报与公告入口
- AI 按需解读新闻

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Environment Variables

Copy `.env.example` to `.env` and fill in only the API keys you want to use. The app can still run with sample or cached data when external keys are not configured.

```bash
cp .env.example .env
```

## Data Sources

- NewsAPI / SerpAPI / RSS for news fallback
- AKShare as the primary market data source
- Open-source Tushare as a backup market data source
- Eastmoney report center entry
- CNINFO announcement entry

## Notes

- Do not commit `.env`, API keys, tokens, virtual environments, or cache files.
- Market data may vary depending on network availability and upstream data-source stability.
- This project is for coursework, research, and learning. It is not investment advice.
