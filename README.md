# Research Radar 🔭

A free, self-hosted daily digest of NLP & LLM papers from arXiv and Semantic Scholar.
Every day, a GitHub Action fetches new papers, uses **Gemini Flash** (free tier) to auto-tag
and summarise each one, then commits the results. Vercel rebuilds and redeploys automatically.

## Architecture

```
GitHub Actions (daily cron @ 07:00 UTC)
    │
    ├── fetch_papers.py
    │       ├── arXiv API      (free, no key)
    │       └── Semantic Scholar API (free, no key)
    │
    ├── Gemini Flash API  →  tags + 2-3 sentence summary per paper
    │
    └── Commits public/papers.json to repo
            │
            └── Vercel detects push → rebuilds React site → live in ~30s
```

## Setup (one-time, ~15 minutes)

### 1. Fork / clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/Rudra-Paper-Reading
cd Rudra-Paper-Reading
npm install
```

### 2. Get a free Gemini API key

1. Go to https://aistudio.google.com/app/apikey
2. Click **Create API key**
3. Copy it

### 3. Add the key to GitHub Secrets

In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**

- Name:  `GEMINI_API_KEY`
- Value: `your-key-here`

### 4. Deploy to Vercel (free)

1. Go to https://vercel.com → **New Project** → import your GitHub repo
2. Framework preset: **Vite**
3. Click **Deploy** — done. Vercel will auto-redeploy on every push.

### 5. Trigger the first paper fetch manually

In your GitHub repo → **Actions → Daily Paper Fetch → Run workflow**

This populates `public/papers.json`. After that it runs automatically every day at 07:00 UTC (12:30 IST).

## Local development

```bash
npm run dev        # starts Vite dev server at http://localhost:5173
```

To test the fetcher locally:

```bash
export GEMINI_API_KEY=your-key
python scripts/fetch_papers.py
```

## Customising

| What | Where |
|------|-------|
| Paper sources / categories | `scripts/fetch_papers.py` → `ARXIV_CATS` |
| Number of papers per run | `scripts/fetch_papers.py` → `MAX_PAPERS` |
| Tags list | `scripts/fetch_papers.py` → `VALID_TAGS` (keep in sync with `src/App.jsx → ALL_TAGS`) |
| Fetch schedule | `.github/workflows/daily-fetch.yml` → `cron` |
| UI colours / fonts | `src/App.jsx` |

## Free tier limits

| Service | Free allowance | Usage here |
|---------|---------------|-----------|
| arXiv API | Unlimited | ~30 calls/day |
| Semantic Scholar | Unlimited (no key) | ~10 calls/day |
| Gemini Flash | 1 500 req/day, 1M tokens/day | ~40 calls/day |
| GitHub Actions | 2 000 min/month | ~3 min/day |
| Vercel | 100 GB bandwidth, unlimited deploys | ~1 deploy/day |

All comfortably within free limits.

## Adding more sources

- **ACL Anthology**: add `fetch_acl_anthology()` using their RSS feed at `https://aclanthology.org/anthology+abstracts.bib.gz`
- **Semantic Scholar by venue**: filter by `venue=ACL` or `venue=EMNLP` in the S2 query
- **Twitter/X**: requires a paid API key; consider using `nitter` as a free alternative
