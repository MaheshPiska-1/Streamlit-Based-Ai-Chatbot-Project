"""
╔══════════════════════════════════════════════════════╗
║           AI-Based PowerGPT  –  Enhanced             ║
║  Features: Chat · Voice · Images · Docs              ║
║            Browser Agent · Web Search · Assignment   ║
╚══════════════════════════════════════════════════════╝
"""

import streamlit as st
import google.generativeai as genai
import os, io, time, re, base64, tempfile, textwrap

# ── Optional deps (graceful degradation if missing) ──
try:
    import speech_recognition as sr
    from pydub import AudioSegment
    VOICE_OK = True
except ImportError:
    VOICE_OK = False

try:
    import PyPDF2
    PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    import docx as _docx
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

try:
    from duckduckgo_search import DDGS
    DDG_OK = True
except ImportError:
    DDG_OK = False

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

import urllib.request, urllib.parse

# ══════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI PowerGPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
:root {
    --brand:    #6c63ff;
    --brand-dk: #4b44cc;
    --surface:  #f7f8fc;
    --card:     #ffffff;
    --border:   #e2e5ef;
    --text:     #1a1a2e;
    --muted:    #6b7280;
}
.stApp { background: var(--surface); }
h1, h2, h3 { color: var(--text); }

.stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: var(--card);
    padding: 6px 8px; border-radius: 12px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; padding: 6px 14px;
    font-weight: 600; font-size: 13px; color: var(--muted);
}
.stTabs [aria-selected="true"] {
    background: var(--brand) !important; color: #fff !important;
}
.stChatMessage { background: var(--card); border-radius: 12px; }

.card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;
}
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; letter-spacing: .4px;
}
.badge-ok   { background:#d1fae5; color:#065f46; }
.badge-warn { background:#fef3c7; color:#92400e; }

.ss-frame {
    border: 2px solid var(--brand); border-radius: 10px; overflow: hidden;
    box-shadow: 0 4px 20px rgba(108,99,255,.15);
}
.profile-img {
    border-radius: 50%; display: block; margin: 0 auto;
    width: 90px; border: 3px solid var(--brand);
}
.answer-block {
    background: linear-gradient(135deg, #f0f4ff, #faf5ff);
    border-left: 4px solid var(--brand);
    border-radius: 0 12px 12px 0; padding: 16px 20px; margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# API SETUP
# ══════════════════════════════════════════════════════
try:
    _api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    _api_key = "YOUR API KEY"   # replace or set in .streamlit/secrets.toml

os.environ["GEMINI_API_KEY"] = _api_key
genai.configure(api_key=_api_key)

# ══════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════
def _init_chat():
    return genai.GenerativeModel("gemini-2.5-flash").start_chat(history=[])

for _k, _v in {
    "chat_session": None, "messages": [], "voice_prompt": None,
    "last_audio_id": None, "browser_log": [], "browser_ss": None,
    "search_results": [], "assign_history": [],
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.chat_session is None:
    try:
        st.session_state.chat_session = _init_chat()
    except Exception as e:
        st.error(f"Gemini init error: {e}")

# ══════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════

def transcribe_audio(audio_file):
    if not VOICE_OK:
        st.warning("Install `SpeechRecognition` and `pydub`.")
        return None
    recognizer = sr.Recognizer()
    raw = audio_file.read()
    try:
        seg = AudioSegment.from_file(io.BytesIO(raw))
    except Exception as e:
        st.warning(f"Audio decode error: {e}")
        return None
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        seg.export(f.name, format="wav"); path = f.name
    try:
        with sr.AudioFile(path) as src:
            data = recognizer.record(src)
        return recognizer.recognize_google(data)
    except sr.UnknownValueError:
        st.warning("Could not understand audio — speak clearly.")
        return None
    except sr.RequestError as e:
        st.error(f"Speech API error: {e}"); return None
    finally:
        os.unlink(path)


def extract_file_text(f) -> str:
    name = f.name.lower(); mime = f.type or ""
    if "pdf" in mime or name.endswith(".pdf"):
        if not PDF_OK: return "Install PyPDF2."
        reader = PyPDF2.PdfReader(io.BytesIO(f.read()))
        pages = [f"[Page {i+1}]\n{pg.extract_text().strip()}"
                 for i, pg in enumerate(reader.pages) if pg.extract_text()]
        return "\n\n".join(pages) or "No readable text."
    elif "plain" in mime or name.endswith(".txt"):
        return f.read().decode("utf-8", errors="ignore")
    elif "word" in mime or name.endswith(".docx"):
        if not DOCX_OK: return "Install python-docx."
        doc = _docx.Document(io.BytesIO(f.read()))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return "Unsupported file type."


def gemini_ask(prompt: str, *, system: str = None, image=None) -> str:
    try:
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction=system or "You are a helpful AI assistant.",
        )
        parts = ([image] if image is not None else []) + [prompt]
        return model.generate_content(parts).text
    except Exception as e:
        return f"Gemini error: {e}"


def _html_to_text(html: str) -> str:
    if BS4_OK:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script","style","nav","footer","header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:12_000]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))[:12_000]


def browser_screenshot_and_text(url: str):
    if PLAYWRIGHT_OK:
        try:
            with sync_playwright() as p:
                br = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage"],
                )
                pg = br.new_page(viewport={"width":1280,"height":800})
                pg.goto(url, wait_until="domcontentloaded", timeout=30_000)
                time.sleep(1.5)
                ss = pg.screenshot(full_page=False, type="png")
                html = pg.content()
                br.close()
            return ss, _html_to_text(html)
        except Exception as e:
            return None, f"[Playwright error: {e}]"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
        return None, _html_to_text(html)
    except Exception as e:
        return None, f"[Fetch error: {e}]"


def web_search(query: str, n: int = 5) -> list:
    if DDG_OK:
        try:
            with DDGS() as ddgs:
                return [{"title":r.get("title",""),"url":r.get("href",""),
                         "snippet":r.get("body","")}
                        for r in ddgs.text(query, max_results=n)]
        except Exception:
            pass
    try:
        q = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
        if BS4_OK:
            soup = BeautifulSoup(html, "lxml")
            out = []
            for res in soup.select(".result")[:n]:
                t = res.select_one(".result__title a")
                s = res.select_one(".result__snippet")
                if t:
                    out.append({"title":t.get_text(strip=True),
                                "url":t.get("href",""),
                                "snippet":(s.get_text(strip=True) if s else "")})
            return out
    except Exception as e:
        return [{"title":"Search failed","url":"","snippet":str(e)}]
    return []


def search_and_synthesize(query: str):
    results = web_search(query)
    if not results: return [], "No results found."
    ctx = "\n\n".join(f"[{i+1}] {r['title']}\nURL: {r['url']}\n{r['snippet']}"
                      for i,r in enumerate(results))
    answer = gemini_ask(
        f"Answer: '{query}'\n\nSearch results:\n{ctx}",
        system=("You are a research assistant. Synthesize the search results "
                "into a clear answer. Cite sources as [1], [2] etc."),
    )
    return results, answer


ASSIGNMENT_SYSTEM = """
You are an expert academic AI tutor. When given an assignment question:
1. Identify the subject and topic
2. Break the question into sub-parts if needed
3. Provide a thorough, step-by-step answer
4. Include relevant formulas, definitions, or code snippets if needed
5. Add a brief summary at the end
6. Use clear markdown: headers, bullets, code blocks where appropriate
Be thorough, accurate, and educational — explain WHY, not just WHAT.
"""

def solve_assignment(question: str, web_ctx: str = "", extra_system: str = "") -> str:
    prompt = (f"Web context:\n{web_ctx}\n\nQuestion:\n{question}"
              if web_ctx else question)
    return gemini_ask(prompt, system=ASSIGNMENT_SYSTEM + extra_system)


def analyze_screenshot(ss_bytes: bytes, question: str) -> str:
    if not PIL_OK: return "Install Pillow."
    img = Image.open(io.BytesIO(ss_bytes))
    return gemini_ask(
        question or "Describe this webpage screenshot in detail.",
        system="You analyse webpage screenshots and answer questions about them.",
        image=img,
    )

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div style='text-align:center;padding:10px 0 4px'>
        <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' class='profile-img'>
    </div>""", unsafe_allow_html=True)
    profile_name = st.text_input("Name", "Guest User")
    profile_role = st.selectbox("Role", ["Student","Developer","Data Scientist","Manager"])
    st.divider()

    st.markdown("**🔌 Feature Status**")
    for label, ok in [("💬 Chat",True),("🎤 Voice",VOICE_OK),
                      ("🌐 Browser",PLAYWRIGHT_OK),("🔍 Web Search",True),
                      ("📄 PDF/DOCX",PDF_OK and DOCX_OK)]:
        cls  = "badge-ok" if ok else "badge-warn"
        txt  = "Ready"    if ok else "Install pkg"
        st.markdown(f'<span>{label}</span> <span class="badge {cls}">{txt}</span>',
                    unsafe_allow_html=True)
    st.divider()

    if st.button("🗑️ Clear All"):
        for k in ["messages","browser_log","browser_ss","search_results",
                  "assign_history","voice_prompt"]:
            st.session_state[k] = [] if isinstance(st.session_state[k], list) else None
        st.session_state.chat_session = _init_chat()
        st.rerun()

    st.markdown("### 📦 Install")
    st.code(("pip install streamlit google-generativeai\n"
             "pip install SpeechRecognition pydub\n"
             "pip install playwright\n"
             "playwright install chromium\n"
             "pip install duckduckgo-search beautifulsoup4 lxml\n"
             "pip install PyPDF2 python-docx Pillow"), language="bash")

# ══════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════
st.markdown("""
<div style='display:flex;align-items:center;gap:12px;margin-bottom:4px'>
  <span style='font-size:2.4rem'>🤖</span>
  <div>
    <h1 style='margin:0;font-size:1.9rem'>AI-Based PowerGPT</h1>
    <p style='margin:0;color:#6b7280;font-size:14px'>
      Chat &nbsp;·&nbsp; Voice &nbsp;·&nbsp; Browser Agent &nbsp;·&nbsp;
      Web Search &nbsp;·&nbsp; Assignment Solver
    </p>
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════
tab_chat, tab_browser, tab_search, tab_assign = st.tabs([
    "💬 Chat", "🌐 Browser Agent", "🔍 Web Search", "📚 Assignment Solver"
])

# ════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════
with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("image_display"): st.image(msg["image_display"], width=280)
            if msg.get("file_name"):     st.caption(f"📎 {msg['file_name']}")
            st.markdown(msg["content"])

    with st.expander("🎤 Voice Input"):
        audio_in = st.audio_input("Record your question")
        if audio_in is not None:
            aid = id(audio_in)
            if aid != st.session_state.last_audio_id:
                st.session_state.last_audio_id = aid
                with st.spinner("Transcribing…"):
                    txt = transcribe_audio(audio_in)
                if txt:
                    st.success(f"📝 *{txt}*")
                    st.session_state.voice_prompt = txt

    with st.expander("📎 Attach File or Image"):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("🖼️ Image")
            up_img = st.file_uploader("img", type=["png","jpg","jpeg","webp"],
                                      key="cu_img", label_visibility="collapsed")
            if up_img: st.image(up_img, use_container_width=True)
        with c2:
            st.caption("📄 Document (PDF/DOCX/TXT)")
            up_doc = st.file_uploader("doc", type=["pdf","docx","txt"],
                                      key="cu_doc", label_visibility="collapsed")
            if up_doc: st.success(f"Ready: **{up_doc.name}**")

    prompt = st.chat_input("Ask PowerGPT anything…")
    if st.session_state.voice_prompt and not prompt:
        if st.button(f'📨 Send: *"{st.session_state.voice_prompt}"*'):
            prompt = st.session_state.voice_prompt
            st.session_state.voice_prompt = None

    if prompt:
        pil_image = img_bytes = file_text = file_name = None
        if up_img:
            img_bytes = up_img.getvalue()
            if PIL_OK: pil_image = Image.open(io.BytesIO(img_bytes))
        if up_doc:
            file_name = up_doc.name
            with st.spinner(f"Reading {up_doc.name}…"):
                file_text = extract_file_text(up_doc)

        entry = {"role":"user","content":prompt}
        if img_bytes:  entry["image_display"] = img_bytes
        if file_name:  entry["file_name"]      = file_name
        st.session_state.messages.append(entry)

        with st.chat_message("user"):
            if img_bytes:  st.image(img_bytes, width=280)
            if file_name:  st.caption(f"📎 {file_name}")
            st.markdown(prompt)

        with st.chat_message("assistant"):
            ph = st.empty(); reply = ""
            try:
                content = (f"Document:\n---\n{file_text}\n---\n\nQuestion: {prompt}"
                           if file_text else prompt)
                if pil_image:
                    resp = st.session_state.chat_session.send_message([pil_image, content])
                    reply = resp.text; ph.markdown(reply)
                else:
                    resp = st.session_state.chat_session.send_message(content, stream=True)
                    for chunk in resp:
                        if chunk.text:
                            reply += chunk.text; ph.markdown(reply + "▌")
                    ph.markdown(reply)
            except Exception as e:
                reply = f"❌ {e}"; ph.markdown(reply)

        st.session_state.messages.append({"role":"assistant","content":reply})
        st.session_state.voice_prompt = None

# ════════════════════════════════════════════════
# TAB 2 — BROWSER AGENT
# ════════════════════════════════════════════════
with tab_browser:
    st.markdown("### 🌐 Browser Agent")
    st.markdown(
        "Enter a URL — PowerGPT opens it with headless Chrome, takes a **screenshot**, "
        "reads the full page text, and answers your question using Gemini Vision."
    )
    if not PLAYWRIGHT_OK:
        st.warning("**Playwright not installed.** Run `pip install playwright && playwright install chromium`. "
                   "Text-only fallback is active.")

    bc1, bc2 = st.columns([2,3])
    with bc1:
        browser_url = st.text_input("🔗 URL", placeholder="https://en.wikipedia.org/wiki/Python_(programming_language)", key="b_url")
    with bc2:
        browser_q = st.text_input("❓ Question about the page",
                                  placeholder="Summarise / Extract headings / What is this about?", key="b_q")

    bb1, bb2, _ = st.columns([1,1,4])
    with bb1: visit_btn = st.button("🚀 Visit & Analyse", type="primary", key="b_visit")
    with bb2:
        if st.session_state.browser_ss and st.button("🔄 Re-ask", key="b_reask"):
            if browser_q:
                with st.spinner("Analysing…"):
                    ans = analyze_screenshot(st.session_state.browser_ss, browser_q)
                st.session_state.browser_log.append(
                    {"url":"(cached)","question":browser_q,"answer":ans})

    if visit_btn and browser_url:
        if not browser_url.startswith("http"): browser_url = "https://" + browser_url
        with st.spinner(f"🌐 Opening {browser_url}…"):
            ss_bytes, page_text = browser_screenshot_and_text(browser_url)
        st.session_state.browser_ss = ss_bytes

        q = browser_q or "Summarise this webpage including main topics and key information."
        with st.spinner("🤖 Gemini is reading the page…"):
            if ss_bytes and PIL_OK:
                answer = analyze_screenshot(ss_bytes, q)
            else:
                answer = gemini_ask(
                    f"Page: {browser_url}\n\n{page_text}\n\nQuestion: {q}",
                    system="You analyse web pages. Answer based on the content provided.",
                )
        st.session_state.browser_log.append(
            {"url":browser_url,"question":q,"answer":answer})

    if st.session_state.browser_ss:
        st.markdown("#### 📸 Screenshot")
        st.markdown('<div class="ss-frame">', unsafe_allow_html=True)
        st.image(st.session_state.browser_ss, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.download_button("⬇️ Download Screenshot", data=st.session_state.browser_ss,
                           file_name="screenshot.png", mime="image/png")

    if st.session_state.browser_log:
        st.markdown("#### 🗒️ Session Log")
        for entry in reversed(st.session_state.browser_log):
            with st.container():
                st.markdown(f'<div class="card">🔗 <b>{entry["url"]}</b><br>❓ <i>{entry["question"]}</i>'
                            f'<div class="answer-block">{entry["answer"]}</div></div>',
                            unsafe_allow_html=True)

    st.markdown("#### ⚡ Quick Visit")
    presets = {"📖 Wikipedia":"https://en.wikipedia.org/wiki/Artificial_intelligence",
               "📰 Hacker News":"https://news.ycombinator.com",
               "🐍 Python Docs":"https://docs.python.org/3/",
               "📊 arXiv AI":"https://arxiv.org/list/cs.AI/recent"}
    pcols = st.columns(len(presets))
    for col,(label,url) in zip(pcols,presets.items()):
        with col:
            if st.button(label, key=f"p_{label}"):
                st.session_state["b_url"] = url; st.rerun()

# ════════════════════════════════════════════════
# TAB 3 — WEB SEARCH
# ════════════════════════════════════════════════
with tab_search:
    st.markdown("### 🔍 AI Web Search")
    st.markdown("Search the web and let Gemini synthesise a cited, accurate answer.")

    s_query = st.text_input("Search query",
                             placeholder="Latest AI research breakthroughs 2025",
                             key="s_query")
    sc1, sc2 = st.columns([1,4])
    with sc1: num_results = st.slider("Results", 3, 10, 5, key="s_num")
    with sc2: deep_search = st.checkbox("🔬 Deep Search (fetch full top result)", key="s_deep")

    if st.button("🔍 Search & Synthesize", type="primary", key="s_btn") and s_query:
        with st.spinner(f"Searching: *{s_query}*…"):
            results, answer = search_and_synthesize(s_query)

        if deep_search and results:
            top_url = results[0].get("url","")
            if top_url.startswith("http"):
                with st.spinner(f"📖 Deep reading: {top_url}…"):
                    _, deep_text = browser_screenshot_and_text(top_url)
                if deep_text and not deep_text.startswith("["):
                    with st.spinner("Re-synthesizing…"):
                        answer = gemini_ask(
                            f"Query: {s_query}\n\nFull page ({top_url}):\n{deep_text}\n\n"
                            f"Prior answer:\n{answer}\n\nGive a more detailed answer.",
                            system="Research assistant with full page access. Be detailed and accurate.",
                        )

        st.session_state.search_results = results
        st.session_state["last_s_answer"] = answer
        st.session_state["last_s_query"]  = s_query

    if st.session_state.get("last_s_answer"):
        st.markdown("#### 💡 Synthesized Answer")
        st.markdown(f'<div class="answer-block">{st.session_state["last_s_answer"]}</div>',
                    unsafe_allow_html=True)
        if st.session_state.search_results:
            with st.expander(f"📋 Sources ({len(st.session_state.search_results)})"):
                for i,r in enumerate(st.session_state.search_results, 1):
                    st.markdown(f"**[{i}] [{r['title']}]({r['url']})**")
                    st.caption(r["snippet"]); st.divider()

        fu = st.text_input("Ask a follow-up", key="s_fu")
        if st.button("➡️ Follow-up", key="s_fu_btn") and fu:
            ctx = (f"Query: {st.session_state.get('last_s_query','')}\n"
                   f"Answer: {st.session_state['last_s_answer']}")
            with st.spinner("Answering…"):
                ans = gemini_ask(f"{ctx}\n\nFollow-up: {fu}",
                                 system="Answer follow-ups based on prior search context.")
            st.markdown(f'<div class="answer-block">{ans}</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════
# TAB 4 — ASSIGNMENT SOLVER
# ════════════════════════════════════════════════
with tab_assign:
    st.markdown("### 📚 AI Assignment Solver")
    st.markdown("Paste your question — PowerGPT searches the web for current info "
                "and gives you a complete, step-by-step answer.")

    ac1, ac2 = st.columns([3,1])
    with ac1:
        assign_q = st.text_area("📝 Question", height=160, key="a_q",
            placeholder=("e.g. Explain the difference between supervised and unsupervised learning.\n\n"
                         "Write a Python function for the nth Fibonacci number using DP.\n\n"
                         "What are the causes and effects of the French Revolution?"))
    with ac2:
        st.markdown("**⚙️ Options**")
        use_web   = st.checkbox("🔍 Search web",    value=True,  key="a_web")
        deep_mode = st.checkbox("🔬 Deep analysis", value=False, key="a_deep")
        subject   = st.selectbox("Subject", ["Auto-detect","Computer Science","Mathematics",
                                             "Physics","Chemistry","History",
                                             "Economics","Biology","English"], key="a_subj")

    if st.button("🚀 Solve Assignment", type="primary", key="a_solve") and assign_q.strip():
        web_ctx = ""
        if use_web:
            sq = (f"{subject}: " if subject != "Auto-detect" else "") + assign_q[:200]
            with st.spinner("🔍 Searching for context…"):
                results, _ = search_and_synthesize(sq)
                web_ctx = "\n\n".join(
                    f"[{i+1}] {r['title']}: {r['snippet']}"
                    for i,r in enumerate(results[:4]))

        extra = (f"\n\nSubject: {subject}." if subject != "Auto-detect" else "")
        if deep_mode: extra += "\nDeep analysis mode: extra depth, multiple examples, edge cases."

        with st.spinner("🧠 Solving… (may take a moment)"):
            answer = solve_assignment(assign_q, web_ctx, extra)

        st.session_state.assign_history.append(
            {"question":assign_q,"answer":answer,"subject":subject})

    if st.session_state.assign_history:
        latest = st.session_state.assign_history[-1]
        st.markdown("---")
        st.markdown(f"#### ✅ Answer  ·  `{latest['subject']}`")

        dl1, dl2, _ = st.columns([1,1,4])
        with dl1:
            st.download_button("⬇️ Download", data=latest["answer"],
                               file_name="answer.txt", mime="text/plain")
        with dl2:
            if st.button("📋 Send to Chat", key="a2chat"):
                st.session_state.messages.append(
                    {"role":"assistant",
                     "content":f"**Assignment Answer:**\n\n{latest['answer']}"})
                st.success("Sent to Chat ✓")

        st.markdown(f'<div class="answer-block">', unsafe_allow_html=True)
        st.markdown(latest["answer"])
        st.markdown("</div>", unsafe_allow_html=True)

        if len(st.session_state.assign_history) > 1:
            with st.expander(f"📂 Previous answers ({len(st.session_state.assign_history)-1})"):
                for e in reversed(st.session_state.assign_history[:-1]):
                    st.markdown(f"**Q:** {e['question'][:120]}…")
                    st.markdown(e["answer"][:400] + "…"); st.divider()
    else:
        st.markdown("#### 💡 Example Questions")
        examples = [
            ("💻 CS",    "Explain time and space complexity of quicksort with a detailed example."),
            ("📐 Math",  "Find eigenvalues and eigenvectors of the matrix [[4,1],[2,3]]."),
            ("⚛️ Physics","Derive the equation of motion for a damped harmonic oscillator."),
            ("📜 History","Discuss the main causes and long-term effects of World War I."),
        ]
        for icon_label, ex_q in examples:
            if st.button(f"{icon_label}: {ex_q[:65]}…", key=f"ex_{icon_label}"):
                st.session_state["a_q"] = ex_q; st.rerun()
