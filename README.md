# Pain Point Collector

Collect and analyze business pain points from legal public sources.

## Sources

- **Hacker News** - Free API, Ask HN posts and discussions
- **Indie Hackers** - Public interviews with founders
- **App Store** - Negative reviews (1-3 stars) on business apps
- **YouTube** - Comments on relevant videos (requires API key)

## Setup

### 1. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
ANTHROPIC_API_KEY=sk-ant-xxxxx
YOUTUBE_API_KEY=xxxxx  # Optional
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Add to `.env` file

## Usage

### Collect from All Sources

```bash
python -m src.main --sources all --limit 50
```

### Collect from Specific Sources

```bash
# Hacker News + App Store only
python -m src.main --sources hn appstore --limit 100

# Indie Hackers only
python -m src.main --sources ih --limit 30
```

### Run Dashboard

```bash
streamlit run src/dashboard/app.py
```

## Project Structure

```
pain-collector/
├── src/
│   ├── collectors/
│   │   ├── base.py            # Base collector class
│   │   ├── hackernews.py      # HN API collector
│   │   ├── indiehackers.py    # IH interview scraper
│   │   ├── appstore.py        # App Store reviews
│   │   └── youtube.py         # YouTube comments
│   ├── analyzer/
│   │   ├── classifier.py      # Claude classification
│   │   └── prompts.py         # Analysis prompts
│   ├── storage/
│   │   ├── database.py        # SQLite storage
│   │   └── models.py          # Data models
│   ├── dashboard/
│   │   └── app.py             # Streamlit dashboard
│   ├── config.py              # Configuration
│   └── main.py                # Entry point
├── data/
│   └── pains.db               # SQLite database
├── requirements.txt
├── .env.example
└── README.md
```

## Output

- **SQLite database:** `data/pains.db`
- **Dashboard:** http://localhost:8501

## Apps Analyzed (App Store)

- Toast POS, Square POS, 7shifts (Restaurants)
- QuickBooks, Wave Invoicing, Jobber (Small Business)
- HubSpot, Pipedrive (CRM/Sales)
- Calendly, Acuity Scheduling (Scheduling)

## Pain Analysis Fields

Each identified pain point includes:

- **Industry** - restaurant, dental, saas, ecommerce, etc.
- **Role** - owner, founder, manager, employee
- **Severity** (1-10) - How painful is this problem?
- **Frequency** - daily, weekly, monthly, rare
- **Impact Type** - time, money, stress, growth
- **Willingness to Pay** - none, low, medium, high
- **AI Solvable** - Can AI help solve this?
- **Solution Complexity** - simple, medium, complex
- **Product Idea** - Suggested solution concept
- **Key Quotes** - Exact quotes from source
