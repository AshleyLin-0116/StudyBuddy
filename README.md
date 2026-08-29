# StudyBuddy 🌿

AI-powered study companion for students. Generates open-ended practice questions, tracks weak spots, adapts to your study habits, and creates personalized exam schedules — built with Python, Flask, and the Anthropic API.

---

## Features

- Open-ended questions that require real understanding (not guessable by luck)
- Hints on demand, and full step-by-step explanations when you're truly stuck
- Automatically identifies and tracks your weak spots per course
- Study buddy mode (encouraging) vs exam mode (strict, no hints)
- Personalized study schedule based on your exam date
- Upload professor practice exams → generates similar questions
- Synced across all your devices via Supabase

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| AI | Anthropic API (Claude Sonnet) |
| Database | Supabase (PostgreSQL) |
| Hosting | Vercel |

---

## Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/AshleyLin-0116/StudyBuddy.git
cd StudyBuddy
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```
Then open `.env` and fill in:
- `ANTHROPIC_API_KEY` — get it from [console.anthropic.com](https://console.anthropic.com)
- `SUPABASE_URL` — from your Supabase project settings
- `SUPABASE_KEY` — the `anon` public key from Supabase

### 5. Set up Supabase
- Create a free project at [supabase.com](https://supabase.com)
- Go to the SQL Editor and run the contents of `supabase_schema.sql`

### 6. Run the app
```bash
python app.py
```
Visit `http://localhost:5000`

---

## Deployment (Vercel)

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com) → Import your `StudyBuddy` repo
3. Add your environment variables in Vercel's project settings:
   - `ANTHROPIC_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
4. Deploy — Vercel auto-deploys every time you push to `main`

---

## Cost

| Service | Cost |
|---|---|
| Vercel hosting | Free |
| Supabase database | Free |
| Anthropic API | ~$3–8 per semester |
| Custom domain (optional) | ~$10–12/year |

---

## Project Structure

```
StudyBuddy/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── vercel.json            # Vercel deployment config
├── supabase_schema.sql    # Database table definitions
├── .env.example           # Environment variable template
├── .gitignore
├── README.md
└── static/
    └── index.html         # Frontend app
```

---

Built by Ashley Lin — UW–Madison, Data Science
