# SnapClass AI 🎓

AI-powered attendance management SaaS for schools, coaching institutes, and colleges.

## Quick Start

```bash
cd snapclass
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
streamlit run app.py
```

Open: http://localhost:8501

## Demo Credentials

| Portal  | Email                | Password   |
|---------|----------------------|------------|
| Student | student@snapclass.ai | student123 |
| Teacher | teacher@snapclass.ai | teacher123 |
| Admin   | *(password only)*    | admin123   |

## Supabase Setup (Optional)

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fill in your Supabase URL and key
# Run src/database/schema.sql in Supabase SQL Editor
```

App runs fully in demo mode without Supabase.

## AI Face Recognition (Optional)

```bash
pip install deepface tf-keras opencv-python-headless
```

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to share.streamlit.io → New App → select repo
3. Add secrets in Advanced Settings
4. Deploy
