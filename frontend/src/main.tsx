import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowUp,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronDown,
  Compass,
  ExternalLink,
  Globe2,
  LoaderCircle,
  MessageSquarePlus,
  PanelLeftClose,
  ShieldCheck,
  Sparkles,
  Square,
  X,
} from "lucide-react";
import {
  fetchSources,
  streamChat,
  waitForBackend,
  type Health,
  type Source,
} from "./api";
import "./style.css";

type Language = "en" | "ar";
type Chat = {
  id: number;
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
  pending?: boolean;
  error?: boolean;
  model?: string;
  total?: number;
  draft?: boolean;
};
const copy = {
  en: {
    new: "New conversation",
    workspace: "YOUR WORKSPACE",
    explore: "Explore properties",
    library: "Source library",
    title: "A world of property.\nA clearer perspective.",
    subtitle:
      "Explore Dar Global and Wasalt in one conversation.\nAsk a question. Follow the sources. Find your next insight.",
    placeholder: "Ask about a project, a place, or a property service…",
    foot: "AI can make mistakes. Check the sources before making a decision.",
    welcome: "PROPERTY INTELLIGENCE, IN CONVERSATION",
    badge: "Dar Global + Wasalt",
    sources: "Sources",
    ask: "Ask a question",
    waking: "Waking the free server. This can take about a minute…",
    connecting: "Connecting to your workspace…",
    ready: "Ready to explore",
    failed: "Server unavailable · click to retry",
    synthetic: "Demo content",
    syntheticBody:
      "This workspace currently uses fictional fixtures. Website content is awaiting permission.",
    live: "Collected source snapshot",
    close: "Close",
    clear: "Clear conversation",
    thinking: "Finding the right perspective…",
    draft: "Generating · citations pending verification",
    error: "This answer could not be completed. Please try again.",
    key: "OpenRouter is not configured yet. The interface is ready; model answers need a server-side API key.",
    quota:
      "Free model quota or capacity is unavailable. Please try again later.",
    rate: "Too many requests. Wait a minute and try again.",
    timeout: "The free service took too long to respond. Please retry.",
    stopped: "Response stopped. Ask again to retry.",
    sample: "Try a starting point",
    docs: "Collection notes",
    noSources: "Source metadata is not available yet.",
    snapshot: "Snapshot",
    syntheticSource: "Fictional fixture · not website evidence",
  },
  ar: {
    new: "محادثة جديدة",
    workspace: "مساحة العمل",
    explore: "استكشف العقارات",
    library: "مكتبة المصادر",
    title: "عالم من العقارات.\nرؤية أكثر وضوحاً.",
    subtitle:
      "استكشف دار جلوبال ووصلت في محادثة واحدة.\nاسأل، وتحقق من المصادر، واكتشف المزيد.",
    placeholder: "اسأل عن مشروع أو موقع أو خدمة عقارية…",
    foot: "قد يخطئ الذكاء الاصطناعي. تحقق من المصادر قبل اتخاذ أي قرار.",
    welcome: "معرفة عقارية عبر المحادثة",
    badge: "دار جلوبال + وصلت",
    sources: "المصادر",
    ask: "اطرح سؤالاً",
    waking: "جارٍ تشغيل الخادم المجاني. قد يستغرق ذلك نحو دقيقة…",
    connecting: "جارٍ الاتصال بمساحة العمل…",
    ready: "جاهز للاستكشاف",
    failed: "الخادم غير متاح · اضغط للمحاولة",
    synthetic: "محتوى تجريبي",
    syntheticBody:
      "تستخدم هذه المساحة بيانات خيالية حالياً، بانتظار الإذن باستخدام محتوى المواقع.",
    live: "لقطة من المصادر المجمعة",
    close: "إغلاق",
    clear: "مسح المحادثة",
    thinking: "جارٍ البحث في المصادر…",
    draft: "جارٍ إنشاء الإجابة · المراجع قيد التحقق",
    error: "تعذر إكمال الإجابة. يرجى المحاولة مجدداً.",
    key: "لم يتم إعداد OpenRouter بعد. الواجهة جاهزة، وتحتاج الإجابات إلى مفتاح API على الخادم.",
    quota: "حصة النموذج المجاني أو سعته غير متاحة حالياً. حاول لاحقاً.",
    rate: "طلبات كثيرة. انتظر دقيقة ثم حاول مجدداً.",
    timeout: "استغرقت الخدمة المجانية وقتاً طويلاً. حاول مجدداً.",
    stopped: "تم إيقاف الإجابة. أعد السؤال للمحاولة.",
    sample: "ابدأ بسؤال",
    docs: "ملاحظات جمع البيانات",
    noSources: "بيانات المصادر غير متاحة بعد.",
    snapshot: "تاريخ الجمع",
    syntheticSource: "بيانات خيالية · ليست دليلاً من الموقع",
  },
};
const prompts = {
  en: [
    [
      "01",
      "Discover the destinations",
      "What can you tell me about Dar Global’s projects?",
      "Dar Global",
    ],
    [
      "02",
      "Understand the possibilities",
      "How does Wasalt help people find a property?",
      "Wasalt",
    ],
    [
      "03",
      "See the bigger picture",
      "How are Dar Global and Wasalt different?",
      "Compare",
    ],
  ],
  ar: [
    ["01", "اكتشف الوجهات", "ماذا تعرف عن مشاريع دار جلوبال؟", "دار جلوبال"],
    ["02", "تعرّف على الخيارات", "كيف تساعد وصلت في البحث عن عقار؟", "وصلت"],
    ["03", "شاهد الصورة الأشمل", "ما الفرق بين دار جلوبال ووصلت؟", "مقارنة"],
  ],
};

function App() {
  const [lang, setLang] = useState<Language>("en");
  const [messages, setMessages] = useState<Chat[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<
    "connecting" | "waking" | "ready" | "failed"
  >("connecting");
  const [health, setHealth] = useState<Health | null>(null);
  const [busy, setBusy] = useState(false);
  const [library, setLibrary] = useState(false);
  const [sourceList, setSourceList] = useState<Source[]>([]);
  const [sidebar, setSidebar] = useState(false);
  const connection = useRef<AbortController | null>(null);
  const generation = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const t = copy[lang];

  async function connect() {
    connection.current?.abort();
    const controller = new AbortController();
    connection.current = controller;
    setStatus("connecting");
    try {
      const state = await waitForBackend(controller.signal, () =>
        setStatus("waking"),
      );
      setHealth(state);
      setStatus("ready");
      setSourceList(await fetchSources(controller.signal));
    } catch {
      if (!controller.signal.aborted) setStatus("failed");
    }
  }
  useEffect(() => {
    void connect();
    return () => {
      connection.current?.abort();
      generation.current?.abort();
    };
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  }, [lang]);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(value = input) {
    const question = value.trim();
    if (!question || busy || question.length > 2000) return;
    const id = Date.now();
    const controller = new AbortController();
    generation.current = controller;
    const history = messages
      .filter((m) => !m.pending && !m.error)
      .slice(-4)
      .map((m) => ({ role: m.role, content: m.text.slice(0, 2000) }));
    setMessages((prev) => [
      ...prev,
      { id, role: "user", text: question },
      { id: id + 1, role: "assistant", text: "", pending: true },
    ]);
    setInput("");
    setBusy(true);
    const update = (patch: Partial<Chat>) =>
      setMessages((prev) =>
        prev.map((m) => (m.id === id + 1 ? { ...m, ...patch } : m)),
      );
    try {
      const state = await waitForBackend(controller.signal, () =>
        setStatus("waking"),
      );
      setHealth(state);
      setStatus("ready");
      let answer = "";
      await streamChat(
        { message: question, history, language: lang },
        controller.signal,
        (event) => {
          if (event.kind === "delta") {
            answer += String(event.data.text);
            update({ text: answer, draft: true });
          }
          if (event.kind === "done")
            update({
              text: String(event.data.answer),
              sources: event.data.sources as Source[],
              model: event.data.model as string,
              total: event.data.total_ms as number,
              draft: false,
              pending: false,
            });
        },
      );
    } catch (error) {
      const code = error instanceof Error ? error.message : "";
      const text = controller.signal.aborted
        ? t.stopped
        : code === "not_configured"
          ? t.key
          : code === "quota"
            ? t.quota
            : code === "rate_limit"
              ? t.rate
              : ["timeout", "wake_timeout"].includes(code)
                ? t.timeout
                : t.error;
      update({ text, error: true, pending: false, draft: false, sources: [] });
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    generation.current?.abort();
    setMessages([]);
    setInput("");
    setSidebar(false);
    inputRef.current?.focus();
  }
  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebar ? "open" : ""}`}>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            reset();
          }}
          aria-label="Atlas home"
        >
          <span className="brand-icon">
            <Compass size={23} strokeWidth={1.5} />
          </span>
          atlas<span className="brand-period">.</span>
        </a>
        <button className="new-chat" onClick={reset}>
          <MessageSquarePlus size={17} />
          {t.new}
          <span>↗</span>
        </button>
        <div className="nav-label">{t.workspace}</div>
        <nav>
          <button
            className="nav-item active"
            onClick={() => {
              setLibrary(false);
              setSidebar(false);
            }}
          >
            <Compass size={18} />
            {t.explore}
            <span className="nav-dot" />
          </button>
          <button
            className="nav-item"
            onClick={() => {
              setLibrary(true);
              setSidebar(false);
            }}
          >
            <BookOpen size={18} />
            {t.library}
            <span className="nav-count">{sourceList.length || "—"}</span>
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="profile">
            <span className="profile-avatar">A</span>
            <div>
              <strong>Atlas workspace</strong>
              <small>
                {lang === "ar"
                  ? "مساعد البحث العقاري"
                  : "Your property research companion"}
              </small>
            </div>
            <ChevronDown size={14} />
          </div>
        </div>
      </aside>
      {sidebar && (
        <button
          className="scrim"
          aria-label={t.close}
          onClick={() => setSidebar(false)}
        />
      )}
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-toggle"
              onClick={() => setSidebar(!sidebar)}
              aria-label="Toggle navigation"
            >
              <PanelLeftClose size={20} />
            </button>
            <span>Workspace</span>
            <span className="slash">/</span>
            <strong>{t.explore}</strong>
          </div>
          <div className="header-actions">
            <span className="grounded">
              <span />
              {lang === "ar" ? "مدعوم بالمصادر" : "Grounded in sources"}
            </span>
            <button
              className="language"
              onClick={() => setLang(lang === "en" ? "ar" : "en")}
              aria-label="Switch language"
            >
              <Globe2 size={15} />
              {lang === "en" ? "العربية" : "English"}
            </button>
          </div>
        </header>
        <main
          className={messages.length ? "conversation-main" : "welcome-main"}
        >
          {!messages.length ? (
            <section className="welcome">
              <div className="eyebrow">
                <span className="tiny-star">✧</span>
                {t.welcome}
              </div>
              <h1>
                {t.title.split("\n").map((line, i) => (
                  <React.Fragment key={line}>
                    {i > 0 && <br />}
                    {i === 1 ? <em>{line}</em> : line}
                  </React.Fragment>
                ))}
              </h1>
              <p className="intro">
                {t.subtitle.split("\n").map((line, i) => (
                  <React.Fragment key={line}>
                    {i > 0 && <br />}
                    {line}
                  </React.Fragment>
                ))}
              </p>
              <div className="partner-row">
                <span className="partner-name dar">
                  DAR<span>GLOBAL</span>
                </span>
                <span className="partner-divider" />
                <span className="partner-name wasalt">
                  wasalt<span className="wasalt-mark">⌁</span>
                </span>
                <span className="partner-caption">
                  {lang === "ar"
                    ? "مصدران. محادثة واحدة."
                    : "Two perspectives. One conversation."}
                </span>
              </div>
              <div className="starting-label">
                <span>{t.sample}</span>
                <span className="label-line" />
              </div>
              <div className="prompt-grid">
                {prompts[lang].map(([n, title, question, company]) => (
                  <button
                    className="prompt-card"
                    key={n}
                    onClick={() => void send(question)}
                  >
                    <div className="card-top">
                      <span>{n}</span>
                      <ArrowUpRight size={18} />
                    </div>
                    <h2>{title}</h2>
                    <p>{question}</p>
                    <span className="company-tag">{company}</span>
                  </button>
                ))}
              </div>
              <div className="welcome-note">
                <ShieldCheck size={15} />
                {lang === "ar"
                  ? "مصادر واضحة. إجابات مدروسة."
                  : "Clear sources. Considered answers."}
              </div>
            </section>
          ) : (
            <section
              className="messages"
              aria-label="Conversation"
              aria-live="polite"
            >
              {messages.map((m) => (
                <article
                  className={`message ${m.role} ${m.error ? "error" : ""}`}
                  key={m.id}
                >
                  <div className="message-avatar">
                    {m.role === "assistant" ? (
                      <Compass size={20} />
                    ) : lang === "ar" ? (
                      "أ"
                    ) : (
                      "Y"
                    )}
                  </div>
                  <div className="message-body">
                    <div className="message-name">
                      {m.role === "assistant"
                        ? "Atlas"
                        : lang === "ar"
                          ? "أنت"
                          : "You"}
                      {m.draft && (
                        <span className="draft-label">{t.draft}</span>
                      )}
                    </div>
                    <div className="answer-text">
                      {m.text || (
                        <span className="thinking">
                          <LoaderCircle size={15} />
                          {t.thinking}
                        </span>
                      )}
                    </div>
                    {!!m.sources?.length && (
                      <details className="answer-sources">
                        <summary className="source-heading">
                          <BookOpen size={13} />
                          {t.sources}
                          <ChevronDown size={13} className="source-chevron" />
                        </summary>
                        <div className="source-cards">
                        {m.sources.map((s) => (
                          <a
                            key={s.id}
                            className="source-link"
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <span className="source-number">{s.id}</span>
                            <div>
                              <strong>{s.title}</strong>
                              <small>
                                {s.synthetic
                                  ? t.syntheticSource
                                  : `${new URL(s.url).hostname} · ${new Date(s.collected_at).toLocaleDateString(lang)}`}
                              </small>
                            </div>
                            <ExternalLink size={13} />
                          </a>
                        ))}
                        </div>
                      </details>
                    )}
                    {m.model && (
                      <div className="answer-meta">
                        {m.model}
                        {m.total !== undefined &&
                          ` · ${(m.total / 1000).toFixed(1)}s`}
                      </div>
                    )}
                  </div>
                </article>
              ))}
              <div ref={bottom} />
            </section>
          )}
        </main>
        <div className="composer-area">
          {health?.synthetic && (
            <div className="fixture-notice">
              <span>{t.synthetic}</span>
              {t.syntheticBody}
            </div>
          )}
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <div className="composer-input">
              <Sparkles size={20} className="input-sparkle" />
              <textarea
                ref={inputRef}
                aria-label={t.ask}
                placeholder={t.placeholder}
                value={input}
                maxLength={2000}
                rows={2}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter" &&
                    !e.shiftKey &&
                    !e.nativeEvent.isComposing
                  ) {
                    e.preventDefault();
                    void send();
                  }
                }}
              />
            </div>
            <div className="composer-toolbar">
              <span className="corpus-badge">
                <span />
                {t.badge}
              </span>
              <div className="send-group">
                <span className="keyboard-hint">↵</span>
                {busy ? (
                  <button
                    type="button"
                    className="send-button stop"
                    aria-label="Stop response"
                    onClick={() => generation.current?.abort()}
                  >
                    <Square size={15} />
                  </button>
                ) : (
                  <button
                    className="send-button"
                    disabled={!input.trim()}
                    aria-label={t.ask}
                  >
                    <ArrowUp size={19} />
                  </button>
                )}
              </div>
            </div>
          </form>
          <div className="composer-footer">
            <span>{t.foot}</span>
            <button
              className={`connection ${status}`}
              onClick={() => status === "failed" && void connect()}
            >
              <span />
              {t[status]}
            </button>
          </div>
        </div>
        <footer className="page-footer">
          <span>
            ATLAS <span className="footer-dot">/</span> PROPERTY INTELLIGENCE
          </span>
          <span>
            {lang === "ar" ? "مساحة للاستكشاف." : "Space to explore."}
          </span>
        </footer>
      </div>
      {library && (
        <div className="modal-backdrop" onClick={() => setLibrary(false)}>
          <section
            className="source-modal"
            role="dialog"
            aria-modal="true"
            aria-label={t.library}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-heading">
              <div>
                <div className="eyebrow">ATLAS / RESEARCH</div>
                <h2>{t.library}</h2>
              </div>
              <button onClick={() => setLibrary(false)} aria-label={t.close}>
                <X size={22} />
              </button>
            </div>
            <p className="modal-note">
              {health?.synthetic ? t.syntheticBody : t.live}
            </p>
            {sourceList.length ? (
              sourceList.map((s) => (
                <a
                  className="library-source"
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  key={s.url}
                >
                  <BookOpen size={18} />
                  <div>
                    <strong>{s.title}</strong>
                    <small>
                      {s.synthetic
                        ? t.syntheticSource
                        : `${t.snapshot}: ${new Date(s.collected_at).toLocaleDateString(lang)}`}
                    </small>
                  </div>
                  <ArrowUpRight size={17} />
                </a>
              ))
            ) : (
              <p>{t.noSources}</p>
            )}
            <div className="modal-foot">
              <Check size={15} />
              {lang === "ar"
                ? "روابط المصادر فقط. لا يتم نشر النصوص الكاملة هنا."
                : "Source links only. Full collected text is not published here."}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
