# Contributing to StudyFlow AI 📚⚡

Thank you for your interest in contributing to **StudyFlow AI**! Whether you are fixing a bug, adding new study modes, improving prompt efficiency, or polishing UI interactions, we welcome your contributions.

---

## 👥 Project Team & Maintainers

- **Raghav** ([@Raghav-6509](https://github.com/Raghav-6509)) – Main developer & architecture
- **CKhurana13** ([@CKhurana13](https://github.com/CKhurana13)) – Frontend UI development & design implementation

We warmly welcome new contributors to join in and help improve the project!

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Git**
- A **Google AI Studio API Key** ([Get one here](https://aistudio.google.com/apikey)) or use built-in offline mock mode (`MOCK_AI=true`)

### Development Setup

1. **Fork the repository** on GitHub.
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/studyflow-ai.git
   cd studyflow-ai
   ```
3. **Create and activate a virtual environment**:
   - **Windows (PowerShell / Command Prompt)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to add your `GEMINI_API_KEY`, or set `MOCK_AI=true` to develop locally without consuming API quota.
6. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
7. **Run the local dev server**:
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

---

## 🧪 Testing

Before submitting your changes, run the automated test suite:

```bash
python test_app.py
```

Ensure all tests pass and any new functionality is covered with test cases where appropriate.

---

## 📝 Contribution Guidelines

### Code Style
- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/) style conventions. Write readable code with clear variable and function names.
- **Frontend (HTML/CSS/JS)**:
  - Vanilla JS (ES6+) with 2-space indentation.
  - Semantic HTML5 structure.
  - Maintain the existing CSS design system tokens and glassmorphism styling in `static/css/style.css`.
- **API & Token Management**:
  - Keep prompt templates concise and token-efficient.
  - Respect and maintain the in-memory cache layer (`CacheManager`) to preserve API quota.

### Commit Messages
Use clear, conventional commit messages:

```text
feat: add flashcard generation mode
fix: handle empty input validation on client
docs: update installation steps for Linux
test: add test cases for cache expiration
perf: optimize prompt token usage for summaries
```

### Pull Request Process
1. **Branch out**: Never commit directly to `main`. Create descriptive branch names (e.g., `feature/export-pdf`, `fix/cache-ttl-bug`).
2. **Test thoroughly**: Run `python test_app.py` and manually verify UI workflows.
3. **Document**: Update `README.md` if you introduce new environment variables, dependencies, or flags.
4. **Open PR**: Push your branch and open a Pull Request with a clear summary of changes, motivation, and screenshots/GIFs for UI modifications.

---

## 🐛 Reporting Issues

If you find a bug or issue, please open an Issue with:
- **Environment**: OS and Python version.
- **Steps to reproduce**: Minimal steps to trigger the bug.
- **Expected vs. actual behavior**.
- **Relevant logs or console errors**.
- **Screenshots**: If visual or UI-related.

---

## 💡 Feature Requests & Ideas

Have an idea for StudyFlow AI? Feel free to submit an issue or start a discussion:
- Check existing issues to see if it's already requested.
- Explain the user problem and use case.
- Suggest how it fits into the current quota-efficient architecture.

---

## 🔧 High-Priority Development Areas

- **Interactive Study Tools**: Flashcard generator, interactive quiz cards, or active recall prompts.
- **Export Options**: Exporting study notes to Markdown (`.md`) or PDF.
- **Performance & Caching**: Persistent caching options (e.g., SQLite/Redis) or custom TTL settings.
- **Prompt Engineering**: Fine-tuning prompts for even more compact token footprints and sharper recall cues.
- **Test Coverage**: Expanding tests in `test_app.py` for edge cases and input validation.

---

## 🏗️ Project Structure

```text
ai-study-helper/
├── app.py              # Flask server, Gemini API integration & in-memory caching
├── test_app.py         # Automated test suite (health check, caching & mock flow)
├── requirements.txt    # Project Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Excludes venv, .env, and sensitive files
├── LICENSE             # MIT License
├── README.md           # Project overview & documentation
├── CONTRIBUTING.md      # Contribution guidelines
├── static/
│   ├── css/
│   │   └── style.css   # Modern dashboard styling & design system
│   └── js/
│       └── app.js      # Client-side state, history, and API communications
└── templates/
    └── index.html      # Main application interface
```

---

## 🎯 Code Review Process

All pull requests are reviewed with a focus on:
- **Functionality & Quality**: Does the feature work as described without breaking existing features?
- **Token & Resource Efficiency**: Does it avoid excessive LLM token usage?
- **Security**: Ensures no secrets (`GEMINI_API_KEY`) or sensitive data are committed or exposed.
- **UI & UX**: Maintains modern, responsive, and accessible styling.

---

## 📜 License

By contributing to StudyFlow AI, you agree that your contributions will be licensed under the [MIT License](file:///c:/Users/ragha/ai-study-helper/LICENSE).

---

## 🤝 Code of Conduct

- Be respectful, constructive, and welcoming.
- Encourage beginners and provide actionable feedback.
- Focus on what is best for the community and users.

---

Thank you for contributing to **StudyFlow AI**! 🚀
