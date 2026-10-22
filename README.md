# 🤖 AI-Based PowerGPT
### Streamlit Chatbot · Browser Agent · Assignment Solver · Web Search

---

## ✨ Feature Overview

| Tab | Feature | Description |
|---|---|---|
| 💬 Chat | Text Chat | Streaming Gemini responses with conversation memory |
| 💬 Chat | 🎤 Voice Input | Record audio → auto-transcribe → send |
| 💬 Chat | 🖼️ Image Analysis | Upload PNG/JPG, ask questions about the image |
| 💬 Chat | 📄 Document Q&A | Upload PDF/DOCX/TXT and query the content |
| 🌐 Browser Agent | URL Visitor | Opens any URL in headless Chrome, takes a screenshot |
| 🌐 Browser Agent | Screenshot Analysis | Gemini Vision reads the screenshot and answers |
| 🌐 Browser Agent | Page Text Extraction | Fallback text scraping when Playwright unavailable |
| 🔍 Web Search | AI Search | DuckDuckGo search + Gemini synthesis with citations |
| 🔍 Web Search | Deep Search | Fetches full content of top result for richer answers |
| 🔍 Web Search | Follow-up Q&A | Ask follow-up questions on search results |
| 📚 Assignment Solver | Step-by-step Answers | Full academic answers with explanation |
| 📚 Assignment Solver | Web-augmented Solving | Searches for current info before answering |
| 📚 Assignment Solver | Deep Analysis Mode | Extra depth, multiple examples, edge cases |
| 📚 Assignment Solver | Export & Copy | Download answer as `.txt` or send to Chat tab |

---

## 🏗️ Project Structure

```
PowerGPT/
├── app.py                    # Main Streamlit application (all features)
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── secrets.toml          # API key — DO NOT commit to git
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the project
```bash
git clone https://github.com/your-username/powergpt.git
cd powergpt
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright (for Browser Agent)
```bash
pip install playwright
playwright install chromium
```

> **FFmpeg** is also required for voice input:
> - **macOS:** `brew install ffmpeg`
> - **Ubuntu:** `sudo apt install ffmpeg`
> - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org) and add to PATH

---

## 📦 requirements.txt

```
streamlit>=1.31.0
google-generativeai>=0.5.0
SpeechRecognition>=3.10.0
pydub>=0.25.1
PyPDF2>=3.0.0
python-docx>=1.1.0
Pillow>=10.0.0
playwright>=1.40.0
duckduckgo-search>=5.0.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
```

---

## 🔑 API Key Setup

Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-api-key-here"
```

Get a free key at: **https://aistudio.google.com/app/apikey**

---

## 🚀 Run the App

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**

---

## 🖥️ Usage Guide

### 💬 Chat Tab
Standard AI chat with multi-turn memory.
- **Voice:** Click "🎤 Voice Input", record, click "Send" button
- **Image:** Expand "📎 Attach", upload image, type your question
- **Document:** Upload PDF/DOCX/TXT, ask anything about its content

---

### 🌐 Browser Agent Tab

PowerGPT controls a headless Chrome browser to visit any webpage.

**How it works:**
1. Enter a URL (e.g. `https://en.wikipedia.org/wiki/Python`)
2. Enter a question (e.g. *"What are the main features of Python?"*)
3. Click **🚀 Visit & Analyse**
4. Playwright launches Chrome, navigates to the page, takes a screenshot
5. Gemini Vision reads the screenshot and answers your question

**Use cases:**
- Summarize any webpage
- Extract data from a webpage (tables, headings, links)
- Solve problems that need current online information
- Research multiple websites in sequence

**Quick Visit buttons** provide one-click access to Wikipedia, Hacker News, Python Docs, and arXiv.

> If Playwright is not installed, a text-only fallback automatically activates.

---

### 🔍 Web Search Tab

1. Type any search query
2. Choose number of results (3–10)
3. Optionally enable **Deep Search** (fetches full text of top result)
4. Click **🔍 Search & Synthesize**
5. Gemini reads all results and gives a cited, synthesized answer
6. Ask follow-up questions without searching again

---

### 📚 Assignment Solver Tab

The most powerful feature — designed for students.

1. **Paste your assignment question** in the text area
2. Select a **subject hint** (optional — improves accuracy)
3. Enable **🔍 Search web** to get current information (recommended)
4. Enable **🔬 Deep analysis** for complex multi-part questions
5. Click **🚀 Solve Assignment**
6. Get a full, structured answer with:
   - Step-by-step explanation
   - Relevant formulas / code / definitions
   - Summary section
7. **Download** the answer as a `.txt` file or **Send to Chat** for follow-ups

**Supported question types:**
- Mathematics (algebra, calculus, statistics)
- Computer Science (algorithms, data structures, code)
- Physics / Chemistry (derivations, problems)
- History / Economics / Biology (essays, explanations)
- Any subject with "Auto-detect" mode

---

## 🛠️ Technology Stack

| Tech | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web framework |
| [Google Gemini 2.5 Flash](https://ai.google.dev) | LLM + Vision AI |
| [Playwright](https://playwright.dev/python) | Headless Chrome browser control |
| [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search) | Web search (no API key) |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup) | HTML parsing |
| [SpeechRecognition](https://pypi.org/project/SpeechRecognition) | Voice-to-text |
| [pydub](https://github.com/jiaaro/pydub) | Audio conversion |
| [PyPDF2](https://pypi.org/project/PyPDF2) | PDF extraction |
| [python-docx](https://python-docx.readthedocs.io) | DOCX extraction |
| [Pillow](https://pillow.readthedocs.io) | Image processing |

---

## ⚠️ Troubleshooting

| Problem | Fix |
|---|---|
| `playwright install chromium` fails | Run as admin / check internet |
| Voice not transcribing | Check FFmpeg: `ffmpeg -version` |
| Browser screenshots blank | Some JS-heavy sites need `wait_until="networkidle"` |
| Gemini API errors | Check key at aistudio.google.com |
| PDF not readable | Use text-based (not scanned) PDFs |

---

## 🔮 Future Scope

- [ ] Voice output (text-to-speech)
- [ ] User login & persistent history (SQLite/Firebase)
- [ ] Multi-tab browser sessions
- [ ] Plagiarism check on assignment answers
- [ ] Cloud deployment (Streamlit Community Cloud)
- [ ] Export chat as PDF

---

## 📋 System Requirements

| Component | Minimum |
|---|---|
| Python | 3.9+ |
| RAM | 4 GB (8 GB recommended for browser) |
| Internet | Required |
| OS | Windows / macOS / Linux |
| FFmpeg | For voice input |
| Chromium | For browser agent (`playwright install chromium`) |

---

*Developed with ❤️ using Streamlit, Google Gemini & Playwright*
