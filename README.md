# Pain Point Scraper

Automated tool for collecting and analyzing business pain points from Reddit. The goal is to find validated problems for building SaaS products.

## Features

- Scrapes Reddit posts from business-focused subreddits
- Filters posts by upvotes, comments, and age
- Classifies pain points using Claude AI
- Stores results in SQLite database
- Interactive Streamlit dashboard for exploring results

## Setup

### 1. Create Reddit App

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" as the application type
4. Set redirect URI to `http://localhost:8080`
5. Copy the client ID (under the app name) and client secret

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Collect Data

Run the scraper to collect and analyze posts:

```bash
python -m src.main --limit 50
```

### Launch Dashboard

View and explore collected pain points:

```bash
streamlit run src/dashboard/app.py
```

### Scrape Specific Subreddits

```bash
python -m src.main --subreddits restaurateur dentistry smallbusiness --limit 100
```

## Project Structure

```
pain-scraper/
├── src/
│   ├── scraper/
│   │   ├── reddit.py         # Reddit API client
│   │   └── keywords.py       # Keywords for search
│   ├── analyzer/
│   │   ├── classifier.py     # Claude classification
│   │   └── prompts.py        # Analysis prompts
│   ├── storage/
│   │   ├── database.py       # SQLite storage
│   │   └── models.py         # Data models
│   ├── dashboard/
│   │   └── app.py            # Streamlit dashboard
│   ├── config.py             # Configuration
│   └── main.py               # Entry point
├── data/
│   └── pains.db              # SQLite database
├── requirements.txt
├── .env.example
└── README.md
```

## Output

- SQLite database: `data/pains.db`
- Dashboard: http://localhost:8501

## Subreddits Covered

- **Small Business**: smallbusiness, Entrepreneur, startups
- **HoReCa**: restaurateur, Restaurant_Managers, coffeeshops, KitchenConfidential
- **Medical**: dentistry, Dentists, optometry, veterinary
- **Real Estate**: realtors, PropertyManagement
- **Services**: HVAC, Plumbing, electricians, AutoDetailing, lawncare
- **E-commerce**: ecommerce, FulfillmentByAmazon, shopify
- **Freelance/Agencies**: freelance, agency, web_design, marketing

## Pain Analysis

Each identified pain point includes:

- **Severity** (1-10): How painful is this problem?
- **Frequency**: How often does it occur?
- **Financial Impact**: Cost implications
- **Time Impact**: Time wasted
- **Willingness to Pay**: Would users pay for a solution?
- **AI Solvable**: Can AI help solve this?
- **Product Idea**: Suggested solution concept
