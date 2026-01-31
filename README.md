# Pain Point Scraper & Analyzer

Collect, cluster, and analyze business pain points from public sources to find validated problems for building SaaS products.

## Features

- **Multi-source collection** - Hacker News, Reddit, YouTube, App Store, Stack Exchange, Indie Hackers
- **AI-powered classification** - GPT-4o-mini analyzes and categorizes pain points
- **Semantic clustering** - HDBSCAN groups similar pains using embeddings
- **Deep analysis** - GPT-4o provides GO/MAYBE/NO_GO verdicts on opportunities
- **Progress & cost tracking** - Real-time progress and LLM cost monitoring
- **Interactive dashboard** - Streamlit UI with filtering and visualizations

## Sources

| Source | Description | API Key Required |
|--------|-------------|------------------|
| Hacker News | Ask HN posts and discussions | No |
| Reddit | Via Pullpush.io API (free) | No |
| Stack Exchange | Software Recommendations, WebApps | No |
| App Store | Negative reviews on business apps | No |
| YouTube | Comments on relevant videos | Yes |
| Indie Hackers | Public founder interviews | No |

## Setup

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
OPENAI_API_KEY=sk-xxxxx          # Required
YOUTUBE_API_KEY=xxxxx            # Optional (for YouTube source)
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. (Optional) Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Add to `.env` file

## Usage

### Collect Pain Points

```bash
# All sources
python3 -m src.main --sources all --limit 50

# Specific sources
python3 -m src.main --sources reddit hn stackexchange --limit 100

# Single source
python3 -m src.main --sources appstore --limit 30
```

Available sources: `all`, `hn`, `ih`, `appstore`, `youtube`, `reddit`, `stackexchange` (or `se`)

### Cluster Similar Pains

```bash
# Default settings (min 3 pains per cluster)
python3 -m src.cluster

# Custom minimum cluster size
python3 -m src.cluster --min-size 5
```

### Deep Analysis of Top Clusters

```bash
# Analyze top 10 clusters
python3 -m src.analyze --top 10 --min-size 5

# Analyze specific cluster
python3 -m src.analyze --cluster-id 12
```

### Run Dashboard

```bash
streamlit run src/dashboard/app.py
```

Dashboard features:
- **Pains tab** - Browse and filter collected pain points
- **Clusters tab** - View clustered opportunities with deep analysis
- **Statistics tab** - Track collection runs, LLM costs, and progress

## Project Structure

```
pain-scraper/
├── src/
│   ├── collectors/
│   │   ├── base.py              # Base collector class
│   │   ├── hackernews.py        # HN API collector
│   │   ├── reddit_pullpush.py   # Reddit via Pullpush
│   │   ├── stackexchange.py     # Stack Exchange API
│   │   ├── appstore.py          # App Store reviews
│   │   ├── youtube.py           # YouTube comments
│   │   └── indiehackers.py      # IH interview scraper
│   ├── analyzer/
│   │   ├── classifier.py        # GPT pain classification
│   │   ├── clustering.py        # HDBSCAN clustering
│   │   ├── deep_analysis.py     # Deep opportunity analysis
│   │   └── prompts.py           # LLM prompts
│   ├── storage/
│   │   ├── database.py          # SQLite storage
│   │   └── models.py            # Data models
│   ├── tracking/
│   │   ├── progress.py          # Progress tracking
│   │   └── costs.py             # LLM cost tracking
│   ├── dashboard/
│   │   └── app.py               # Streamlit dashboard
│   ├── config.py                # Configuration
│   ├── main.py                  # Collection entry point
│   ├── cluster.py               # Clustering entry point
│   └── analyze.py               # Deep analysis entry point
├── data/
│   └── pains.db                 # SQLite database
├── requirements.txt
├── .env.example
└── README.md
```

## Database Schema

### Main Tables

- **pains** - Collected and classified pain points
- **clusters** - Grouped similar pains with opportunity scores
- **pain_clusters** - Pain-to-cluster mapping
- **deep_analyses** - Detailed analysis of clusters

### Tracking Tables

- **collection_runs** - Run history with stats
- **llm_costs** - Token usage and costs per request
- **daily_stats** - Aggregated daily statistics

## Pain Classification Fields

| Field | Description |
|-------|-------------|
| industry | restaurant, dental, saas, ecommerce, etc. |
| role | owner, founder, manager, employee |
| severity | 1-10 scale of pain intensity |
| frequency | daily, weekly, monthly, rare |
| impact_type | time, money, stress, growth |
| willingness_to_pay | none, low, medium, high |
| solvable_with_ai | Whether AI can help solve it |
| solution_complexity | simple, medium, complex |
| potential_product | Suggested solution concept |
| key_quotes | Exact quotes from source |

## Deep Analysis Fields

| Field | Description |
|-------|-------------|
| competitors | Existing solutions with weaknesses |
| target_role | Ideal customer persona |
| target_company_size | Company size fit |
| market_size | small, medium, large |
| mvp_description | Minimum viable product concept |
| core_features | Must-have v1 features |
| best_channel | Customer acquisition channel |
| price_range | Acceptable pricing |
| risks | Key risks to consider |
| verdict | go, maybe, no_go |
| attractiveness_score | 1-10 opportunity rating |

## LLM Cost Tracking

The system tracks all OpenAI API costs:

| Model | Use Case | Cost (per 1M tokens) |
|-------|----------|---------------------|
| gpt-4o-mini | Classification | $0.15 input / $0.60 output |
| gpt-4o | Deep analysis | $2.50 input / $10.00 output |
| text-embedding-3-small | Clustering | $0.02 input |

View costs in the dashboard Statistics tab or query the database:

```sql
SELECT operation, model, SUM(cost_usd)
FROM llm_costs
GROUP BY operation, model;
```

## Limitations

- Review sites (G2, Capterra, TrustRadius) are protected by anti-bot systems
- Reddit official API requires authentication; using Pullpush.io as alternative
- YouTube requires API key and has quota limits
- Some sources may have rate limiting

## Example Output

```
============================================================
DEEP CLUSTER ANALYSIS
============================================================

Analyzing top 5 clusters (min size: 3)...

📊 Summary:
   ✅ GO: 2
   🤔 MAYBE: 3
   ❌ NO GO: 0

============================================================
TOP OPPORTUNITIES (GO verdict):
============================================================

✅ Cluster #12: Coffee Shop Operational Challenges
   Attractiveness: 8/10
   Verdict: GO

   💡 Strong value proposition for small coffee shop owners

   📊 Target: Owner of a Small Coffee Shop
   🏢 Company Size: 10-30 employees
   📈 Market Size: medium

   🛠️ MVP: Platform for analytics, employee management, and costs
   💰 Price Range: $99-199/mo
```
