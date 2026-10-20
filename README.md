# StudyFlow AI 📚

A lightweight, student-focused study companion that generates structured revision notes, summaries, and revision checklists using Google Gemini with built-in token optimization and quota-saving caching.

---

## Key Highlights

- **Built-in Quota Saver**: Employs in-memory TTL caching so repeat topics consume **0 tokens and 0 API requests**.
- **High-Yield Notes**: Compact, structured revision bullet points tailored by academic level (High School, Undergraduate, Advanced) and goal.
- **Executive Summaries & Checklists**: Generates quick digestible summaries and step-by-step master checklists for quick recall.
- **Export & Copy**: Easily download notes as text files or copy them with one click.
- **Offline Dev / Mock Mode (`MOCK_AI=true`)**: Test UI changes, styling, and workflows without burning any Gemini API credits.
- **Responsive UI**: Modern glassmorphic dashboard built with vanilla CSS and responsive design.

---

## Repository Structure

```text
ai-study-helper/
├── app.py              # Flask server, Gemini API integration & in-memory caching
├── test_app.py         # Automated test suite (health check, caching & mock flow)
├── requirements.txt    # Project Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Excludes venv, .env, and sensitive files
├── LICENSE             # MIT License
├── README.md           # Project documentation
├── static/
│   ├── css/
│   │   └── style.css   # Modern dashboard styling & design system
│   └── js/
│       └── app.js      # Client-side state, history, and API communications
└── templates/
    └── index.html      # Main application interface
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- A Google AI Studio API key ([Get one for free here](https://aistudio.google.com/apikey))

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/ai-study-helper.git
cd ai-study-helper
```

### 3. Create & Activate Virtual Environment
On Windows (PowerShell / Command Prompt):
```bash
python -m venv venv
.\venv\Scripts\activate
```

On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(On Windows: `copy .env.example .env`)*

Open `.env` and fill in your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
MOCK_AI=false
```

---

## Running the Application

```bash
python app.py
```
Open your browser and navigate to:
```text
http://localhost:5000
```

---

## Running Automated Tests

Run the built-in test suite to verify routes and caching without using any API tokens:
```bash
python test_app.py -v
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web dashboard |
| `GET` | `/api/health` | Health & model status, cache counter |
| `POST` | `/api/generate-notes` | High-yield revision notes |
| `POST` | `/api/generate-summary` | 2-3 sentence revision summary |
| `POST` | `/api/generate-study-pack` | Combined summary, notes & checklist |

---

## Contributors

- **Raghav** ([@Raghav-6509](https://github.com/Raghav-6509)) – Main developer & architecture
- **CKhurana13** ([@CKhurana13](https://github.com/CKhurana13)) – Frontend UI development & design implementation

---

## Contributing

Contributions, bug reports, and feature suggestions are always welcome! Please check out our [Contributing Guidelines](CONTRIBUTING.md) to get started.

---

## License

This project is licensed under the [MIT License](LICENSE).
