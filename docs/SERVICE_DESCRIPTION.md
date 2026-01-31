# Pain Scraper — Описание сервиса

## Цель

Автоматический сбор и анализ бизнес-болей из публичных источников для поиска идей SaaS-продуктов с валидированным спросом.

---

## Текущая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        ИСТОЧНИКИ                            │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│ Hacker News │ App Store   │ YouTube     │ Indie Hackers    │
│ (API)       │ (RSS)       │ (API)       │ (Scraping)       │
└──────┬──────┴──────┬──────┴──────┬──────┴────────┬─────────┘
       │             │             │               │
       ▼             ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                      COLLECTORS                             │
│  • hackernews.py  • appstore.py  • youtube.py  • indiehackers.py │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ANALYZER (GPT-4o-mini)                 │
│  • Классификация: боль или нет?                            │
│  • Извлечение: industry, severity, WTP, product idea       │
│  • Структурированный JSON output                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      STORAGE (SQLite)                       │
│  • 156 записей                                              │
│  • Индексы по industry, severity, source                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DASHBOARD (Streamlit)                  │
│  • Фильтры по industry, source, severity                   │
│  • Карточки болей с деталями                               │
│  • Экспорт в CSV                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Источники данных

| Источник | Тип доступа | Что собираем | Текущий лимит |
|----------|-------------|--------------|---------------|
| Hacker News | API (бесплатно) | Ask HN посты, поиск по keywords | 100+ постов |
| App Store | RSS (бесплатно) | Негативные отзывы 1-3★ на бизнес-приложения | 30 отзывов |
| YouTube | API (ключ) | Комментарии под видео о бизнес-проблемах | 60+ комментов |
| Indie Hackers | Web scraping | Публичные интервью с фаундерами | ~20 интервью |

---

## Анализируемые метрики

Для каждой найденной боли извлекаем:

| Поле | Описание | Значения |
|------|----------|----------|
| `industry` | Индустрия | restaurant, cafe, dental, saas, ecommerce, freelance... |
| `role` | Роль автора | owner, founder, manager, employee, customer |
| `severity` | Острота проблемы | 1-10 |
| `frequency` | Как часто возникает | daily, weekly, monthly, rare |
| `impact_type` | Тип влияния | time, money, stress, growth |
| `willingness_to_pay` | Готовность платить | none, low, medium, high |
| `solvable_with_software` | Решается софтом? | true/false |
| `solvable_with_ai` | Решается AI? | true/false |
| `solution_complexity` | Сложность решения | simple, medium, complex |
| `potential_product` | Идея продукта | Текст |
| `key_quotes` | Ключевые цитаты | JSON array |
| `tags` | Теги | scheduling, billing, hiring... |

---

## Текущие результаты

**База:** 156 болей

**По источникам:**
- Hacker News: 65
- YouTube: 61
- App Store: 30

**Топ индустрий:**
- SaaS: 34 (avg severity 7.2)
- Cafe: 21 (avg severity 7.4)
- E-commerce: 21 (avg severity 7.4)
- Freelance: 17 (avg severity 7.2)
- Retail: 15 (avg severity 7.5)

---

## Ограничения текущей версии

### Технические
1. **Синхронный анализ** — GPT вызывается последовательно, медленно
2. **Нет дедупликации** — похожие боли не объединяются
3. **Нет валидации JSON** — иногда GPT возвращает невалидный JSON
4. **SQLite** — не масштабируется для больших объёмов

### По данным
1. **Ограниченные источники** — нет Twitter/X, Reddit, G2, Capterra
2. **Только английский** — не собираем русскоязычные источники
3. **Нет исторических данных** — только текущий snapshot
4. **Нет трендов** — не отслеживаем рост/падение болей

### По анализу
1. **Нет кластеризации** — похожие боли не группируются
2. **Нет скоринга возможностей** — все боли равны
3. **Нет конкурентного анализа** — не смотрим существующие решения
4. **Нет TAM/SAM оценки** — не оцениваем размер рынка

---

## Потенциальные улучшения

### Фаза 1: Стабилизация
- [ ] Retry logic для API вызовов
- [ ] Валидация JSON с fallback
- [ ] Логирование ошибок
- [ ] Rate limiting

### Фаза 2: Больше источников
- [ ] Reddit (через API или scraping)
- [ ] G2 Reviews
- [ ] Capterra Reviews
- [ ] Product Hunt (комментарии)
- [ ] Twitter/X (API дорогой)

### Фаза 3: Умный анализ
- [ ] Кластеризация похожих болей (embeddings)
- [ ] Opportunity Score = severity × WTP × frequency × market_size
- [ ] Автоматический поиск конкурентов
- [ ] Трекинг трендов по времени

### Фаза 4: Автоматизация
- [ ] Scheduled runs (cron / GitHub Actions)
- [ ] Алерты на новые высокоприоритетные боли
- [ ] Интеграция с Notion/Airtable
- [ ] API для внешних систем

### Фаза 5: Монетизация
- [ ] Подписка на отчёты по нишам
- [ ] API доступ
- [ ] Консалтинг на основе данных

---

## Технический стек

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.9+ |
| HTTP клиент | httpx (async) |
| Scraping | BeautifulSoup4 |
| LLM | OpenAI GPT-4o-mini |
| База данных | SQLite |
| Dashboard | Streamlit |
| Деплой | Локально (пока) |

---

## Файловая структура

```
pain-scraper/
├── src/
│   ├── collectors/
│   │   ├── base.py            # Базовый класс
│   │   ├── hackernews.py      # HN API
│   │   ├── indiehackers.py    # IH scraping
│   │   ├── appstore.py        # App Store RSS
│   │   └── youtube.py         # YouTube API
│   ├── analyzer/
│   │   ├── classifier.py      # GPT классификация
│   │   └── prompts.py         # Промпты
│   ├── storage/
│   │   ├── database.py        # SQLite операции
│   │   └── models.py          # Dataclasses
│   ├── dashboard/
│   │   └── app.py             # Streamlit UI
│   ├── config.py              # Настройки
│   └── main.py                # CLI entry point
├── data/
│   ├── pains.db               # SQLite база
│   └── pains_export.csv       # Экспорт
├── docs/
│   └── SERVICE_DESCRIPTION.md # Этот документ
├── requirements.txt
├── .env
└── README.md
```

---

## Команды

```bash
# Сбор из всех источников
python3 -m src.main --sources all --limit 50

# Сбор из конкретных источников
python3 -m src.main --sources hn appstore --limit 30

# Dashboard
python3 -m streamlit run src/dashboard/app.py

# Экспорт в CSV
python3 -c "import sqlite3; import pandas as pd; pd.read_sql_query('SELECT * FROM pains', sqlite3.connect('data/pains.db')).to_csv('data/export.csv', index=False)"
```

---

## Следующие шаги

1. **Определить приоритет улучшений** — что важнее: больше данных или лучший анализ?
2. **Выбрать целевую нишу** — на какие индустрии фокусируемся?
3. **Решить вопрос хостинга** — локально, VPS, или cloud?
4. **Определить формат отчётов** — CSV, Notion, email дайджест?

---

*Последнее обновление: 2026-01-31*
