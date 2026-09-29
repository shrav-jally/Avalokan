## Tech Stack

| Category | Component / Feature | Details, Versions, & File References |
| :--- | :--- | :--- |
| **Frontend** | **Language** | JavaScript with JSX |
| | **Framework** | React 19.2 |
| | **Build tool/dev server** | Vite 7.2+ |
| | **Routing** | React Router DOM 7.13 |
| | **HTTP client** | Axios 1.13 |
| | **Charts and visualization**| Recharts, D3, D3 Cloud, D3 Scale Chromatic |
| | **Animations** | Framer Motion |
| | **Icons** | Lucide React |
| | **Tooltips** | Tippy.js and @tippyjs/react |
| | **Styling** | CSS, Tailwind CSS 4.2, PostCSS, Autoprefixer |
| | **Linting** | ESLint 9 with React Hooks and React Refresh plugins |
| | **Module system** | ES modules |
| | **Frontend API origin** | Hardcoded backend URL at `http://localhost:5000` |
| | **Configuration** | Configured in `package.json:1-42` |
| **Backend** | **Language** | Python |
| | **Web framework** | Flask 3+ |
| | **CORS** | Flask-CORS |
| | **Authentication** | Flask sessions, Local email/password authentication, Google OAuth via Authlib, Werkzeug password hashing |
| | **Configuration** | python-dotenv |
| | **API style** | REST-style JSON endpoints |
| | **Server** | Flask development server |
| | **Entry point** | `app.py:1-70` |
| | **Dependencies** | Listed in `requirements.txt:1-15` |
| **Database** | **Database** | MongoDB |
| | **Python driver** | PyMongo |
| | **Default database** | `avalokan_db` |
| | **Default connection** | `mongodb://localhost:27017/avalokan_db` |
| | **Configurable through** | `MONGO_URI` (MongoDB Atlas can be used by setting `MONGO_URI` to an Atlas connection string) |
| | **Collections** | `policies`, `drafts`, `comments`, `draft_analysis`, `users` |
| | **Implementation** | Database configuration is implemented in `database.py:1-101` |
| **AI and NLP** | **PyTorch** | Model execution and CPU/GPU detection |
| | **Hugging Face Transformers**| NLP pipelines |
| | **TensorFlow Keras** | Compatibility via `tf-keras` |
| | **spaCy** | Keyword extraction and linguistic analysis |
| | **pandas** | Data processing |
| | **Models used** | **Sentiment:** `distilbert-base-uncased-finetuned-sst-2-english`<br>**Toxicity:** `unitary/toxic-bert`<br>**Summarization:** `t5-small`<br>**Hierarchical summarization:** `sshleifer/distilbart-cnn-12-6`<br>**Optional spaCy model:** `en_core_web_sm` |
| | **Implementation & Storage**| AI logic is implemented in `ai_engine.py:1-120`. Models are downloaded and cached locally under `.model_cache`. |
| **Reporting & Data Export**| **PDF reports** | ReportLab |
| | **Excel reports** | pandas and OpenPyXL |
| | **Charts/data preparation** | pandas and Matplotlib |
| | **Test/demo data** | Faker |
| | **Relevant files** | `report_generator.py`, `excel_generator.py` |
| | **Dependency Note** | `openpyxl` is used by the Excel generator but is not explicitly listed in `requirements.txt`, so it should be added for reliable fresh-environment setup. |
| **Configuration & Infrastructure**| **Environment variables** | Documented in `.env.example`:<br>`FLASK_SECRET_KEY`<br>`FLASK_HOST`<br>`FLASK_PORT`<br>`FLASK_DEBUG`<br>`FRONTEND_URL`<br>`CORS_ORIGINS`<br>`MONGO_URI`<br>`GOOGLE_CLIENT_ID`<br>`GOOGLE_CLIENT_SECRET`<br>`ADMIN_ALLOWLIST` |
| **Runtime Requirements**| **System Dependencies** | Node.js and npm, Python |
| | **Database Requirement** | MongoDB local server or MongoDB Atlas |
| | **Network Requirement** | Internet access on first AI model execution |
| | **Hardware & Credentials**| Optional GPU for faster AI inference, Google OAuth credentials for Google login |
| **Not Currently Present**| **Missing Capabilities** | TypeScript, Docker configuration, Docker Compose, Automated CI/CD configuration, Backend test suite, Frontend test framework, Production WSGI server such as Gunicorn or Waitress, Explicit Python or Node version files |
| **Summary** | **In short** | Avalokan is a React/Vite single-page application backed by a Flask REST API, MongoDB, Hugging Face/PyTorch NLP services, Google OAuth, and PDF/Excel reporting tools. |
