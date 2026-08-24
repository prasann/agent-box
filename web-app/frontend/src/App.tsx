import { useEffect, useMemo, useState } from "react"
import type { FormEvent } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  BookOpen,
  Check,
  ChevronRight,
  CircleAlert,
  Command,
  Copy,
  ExternalLink,
  FileText,
  Gauge,
  Library,
  Moon,
  RefreshCw,
  Search,
  Sun,
  Terminal,
  Type,
} from "lucide-react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import "./App.css"

type View = "dashboard" | "findtab" | "text" | "shell" | "library"
type Status = "healthy" | "unavailable"

type Agent = {
  id: Exclude<View, "dashboard">
  name: string
  description: string
  status: Status
  actions: { id: string; name: string }[]
}

type Health = {
  status: string
  services: Record<string, { status: Status; detail: string; remedy?: string | null }>
}

type SearchResult = {
  id: number
  url: string
  title: string
  category?: string
  summary?: string
  topics: string[]
  time_ago: string
}

type LibraryItem = {
  id: string
  name: string
  description: string
  kind: string
  path: string
  vscode_url: string
}

type LibraryDetail = LibraryItem & {
  content: string
  metadata: Record<string, unknown>
}

type Run = {
  id: string
  agent_id: string
  action_id: string
  status: string
  created_at: string
  error?: string
}

const request = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(body.detail || "Control Center request failed")
  }
  return response.json()
}

const navItems: { id: View; label: string; icon: typeof Gauge }[] = [
  { id: "dashboard", label: "Dashboard", icon: Gauge },
  { id: "text", label: "Text", icon: Type },
  { id: "findtab", label: "FindTab", icon: Search },
  { id: "library", label: "Library", icon: Library },
  { id: "shell", label: "Shell", icon: Terminal },
]

const iconForAgent = {
  findtab: Search,
  text: Type,
  shell: Terminal,
  library: Library,
} as const

const controlCenterQuotes = [
  "Local first. Explicit always.",
  "Automate the repeatable; inspect the important.",
  "Small tools. Clear intent. Reliable outcomes.",
  "Every useful system starts with an observable state.",
  "Keep the human in command and the agents in formation.",
  "Good automation leaves an audit trail.",
  "Fast feedback beats hidden cleverness.",
  "A quiet dashboard means the machinery is working.",
  "Build controls before adding velocity.",
  "The best command center reduces uncertainty.",
]

function StatusDot({ status }: { status: Status }) {
  return <span className={`status-dot ${status}`} aria-label={status} />
}

function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="empty-state">
      <CircleAlert size={24} />
      <strong>{title}</strong>
      <span>{body}</span>
    </div>
  )
}

function SearchPanel({ compact = false }: { compact?: boolean }) {
  const [query, setQuery] = useState("")
  const searchMutation = useMutation({
    mutationFn: () =>
      request<{ results: SearchResult[] }>("/api/findtab/search", {
        method: "POST",
        body: JSON.stringify({ query, limit: compact ? 6 : 18, use_llm: true }),
      }),
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (query.trim()) searchMutation.mutate()
  }

  return (
    <section className={compact ? "search-section compact" : "search-section"}>
      <form className="search-box" onSubmit={submit}>
        <Search size={20} />
        <input
          aria-label="Search FindTab"
          placeholder="Find that article, documentation page, or repo..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button className="primary-button" disabled={searchMutation.isPending}>
          {searchMutation.isPending ? "Searching..." : "Search"}
        </button>
      </form>
      {searchMutation.error && <p className="error">{searchMutation.error.message}</p>}
      {searchMutation.data && (
        <div className="result-grid">
          {searchMutation.data.results.map((result) => (
            <a
              className="result-card"
              href={result.url}
              key={result.id}
              target="_blank"
              rel="noreferrer"
            >
              <div className="result-heading">
                <span className="result-category">{result.category || "bookmark"}</span>
                <ExternalLink size={15} />
              </div>
              <h3>{result.title}</h3>
              <p>{result.summary || result.url}</p>
              <div className="topic-row">
                {result.topics.slice(0, 3).map((topic) => (
                  <span className="chip" key={topic}>
                    {topic}
                  </span>
                ))}
                <span className="time">{result.time_ago}</span>
              </div>
            </a>
          ))}
          {!searchMutation.data.results.length && (
            <EmptyState title="No matches" body="Try broader keywords or refresh the index." />
          )}
        </div>
      )}
    </section>
  )
}

function Dashboard({
  agents,
  navigate,
}: {
  agents: Agent[]
  navigate: (view: View, libraryItem?: string) => void
}) {
  return (
    <>
      <header className="page-heading hero-heading">
        <div className="hero-palette" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
        <div>
          <h1>
            Your <span className="hero-blue">agents</span>, one{" "}
            <span className="hero-green">command center</span>.
          </h1>
          <p>Search your knowledge, run trusted workflows, and inspect the library behind them.</p>
        </div>
        <div className="hero-mark">
          <Command size={28} />
          <span>Mission Control</span>
        </div>
      </header>
      <TextView compact />
      <div className="dashboard-search">
        <div className="section-heading">
          <div>
            <h2>Find something you visited</h2>
          </div>
        </div>
        <SearchPanel compact />
      </div>
      <section>
        <div className="section-heading">
          <div>
            <h2>Available agents</h2>
          </div>
          <span className="muted">{agents.length} registered</span>
        </div>
        <div className="agent-grid">
          {agents.map((agent) => {
            const Icon = iconForAgent[agent.id] || Gauge
            return (
              <button className="agent-card" key={agent.id} onClick={() => navigate(agent.id)}>
                <div className="agent-icon">
                  <Icon size={22} />
                </div>
                <div className="agent-content">
                  <div className="agent-title">
                    <h3>{agent.name}</h3>
                    <StatusDot status={agent.status} />
                  </div>
                  <p>{agent.description}</p>
                  <span className="agent-action">
                    {agent.actions.length} actions <ChevronRight size={15} />
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </section>
    </>
  )
}

function FindTabView() {
  const queryClient = useQueryClient()
  const [run, setRun] = useState<Run | null>(null)
  const [progress, setProgress] = useState("")
  const status = useQuery({
    queryKey: ["findtab-status"],
    queryFn: () => request<Record<string, unknown>>("/api/findtab/status"),
  })
  const indexMutation = useMutation({
    mutationFn: () =>
      request<Run>("/api/findtab/index", {
        method: "POST",
        body: JSON.stringify({ force: false }),
      }),
    onSuccess: setRun,
  })

  useEffect(() => {
    if (!run) return
    const events = new EventSource(`/api/runs/${run.id}/events`)
    events.addEventListener("progress", (event) => {
      setProgress(JSON.parse((event as MessageEvent).data).message)
    })
    const finish = () => {
      events.close()
      queryClient.invalidateQueries({ queryKey: ["findtab-status"] })
      setProgress("Index refresh complete")
    }
    events.addEventListener("completed", finish)
    events.addEventListener("failed", (event) => {
      setProgress(JSON.parse((event as MessageEvent).data).message)
      events.close()
    })
    return () => events.close()
  }, [run, queryClient])

  const lastIndexed =
    typeof status.data?.last_processed_at === "string"
      ? new Intl.DateTimeFormat(undefined, {
          dateStyle: "medium",
          timeStyle: "short",
        }).format(new Date(status.data.last_processed_at))
      : "Not indexed yet"
  const metrics = [
    { label: "Saved pages", value: status.data?.total ?? "—", tone: "blue" },
    { label: "Enriched", value: status.data?.enriched ?? "—", tone: "green" },
    { label: "Pending", value: status.data?.pending ?? "—", tone: "amber" },
    { label: "Last indexed", value: lastIndexed, tone: "blue", compact: true },
  ]

  return (
    <div className="findtab-page">
      <header className="page-heading findtab-heading">
        <div>
          <h1>Find anything worth revisiting.</h1>
          <p>Semantic search across the browser history you chose to keep.</p>
        </div>
        <button
          className="secondary-button"
          onClick={() => indexMutation.mutate()}
          disabled={indexMutation.isPending || Boolean(run && progress !== "Index refresh complete")}
        >
          <RefreshCw size={16} /> Refresh index
        </button>
      </header>
      {(progress || indexMutation.error) && (
        <div className="notice">
          <RefreshCw size={16} />
          {indexMutation.error?.message || progress}
        </div>
      )}
      <SearchPanel />
      <div className="findtab-metrics">
        {metrics.map((metric) => (
          <div
            className="findtab-metric"
            data-compact={metric.compact || undefined}
            data-tone={metric.tone}
            key={metric.label}
          >
            <span>{metric.label}</span>
            <strong>{String(metric.value)}</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

function TextView({ compact = false }: { compact?: boolean }) {
  const [text, setText] = useState("")
  const [copied, setCopied] = useState(false)
  const [clipboardError, setClipboardError] = useState("")
  const mutation = useMutation({
    mutationFn: (mode: "fix" | "rewrite") =>
      request<{ result: string }>("/api/text", {
        method: "POST",
        body: JSON.stringify({ text, mode }),
      }),
  })

  const copy = async () => {
    if (!mutation.data) return
    await navigator.clipboard.writeText(mutation.data.result)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1500)
  }

  const useClipboard = async () => {
    try {
      setText(await navigator.clipboard.readText())
      setClipboardError("")
    } catch {
      setClipboardError("Clipboard access was blocked. Allow access or paste into the text area.")
    }
  }

  return (
    <>
      {compact ? (
        <div className="section-heading">
          <div>
            <h2>Polish text</h2>
          </div>
        </div>
      ) : (
        <header className="page-heading">
          <div>
            <h1>Polish text without losing your voice.</h1>
            <p>Paste in, import from the clipboard, and copy the result.</p>
          </div>
        </header>
      )}
      <div className={compact ? "text-workspace compact" : "text-workspace"}>
        <section className="editor-panel">
          <div className="panel-label">
            <label htmlFor={compact ? "source-text-compact" : "source-text"}>Original</label>
            <button className="clipboard-button" type="button" onClick={useClipboard}>
              <Copy size={14} /> Use clipboard
            </button>
          </div>
          <textarea
            id={compact ? "source-text-compact" : "source-text"}
            placeholder="Paste text here..."
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          {clipboardError && <p className="inline-error">{clipboardError}</p>}
          <div className="button-row">
            <button
              className="primary-button"
              disabled={!text.trim() || mutation.isPending}
              onClick={() => mutation.mutate("fix")}
            >
              Fix grammar
            </button>
            <button
              className="secondary-button"
              disabled={!text.trim() || mutation.isPending}
              onClick={() => mutation.mutate("rewrite")}
            >
              Rewrite
            </button>
          </div>
        </section>
        <section className="editor-panel result-panel">
          <div className="panel-label">
            <span>Result</span>
            <button className="icon-button" onClick={copy} disabled={!mutation.data}>
              {copied ? <Check size={17} /> : <Copy size={17} />}
            </button>
          </div>
          <div className="result-text">
            {mutation.isPending
              ? "Working..."
              : mutation.error?.message || mutation.data?.result || "Your revised text appears here."}
          </div>
        </section>
      </div>
    </>
  )
}

function ShellView() {
  const preview = useQuery({
    queryKey: ["shell-preview"],
    queryFn: () =>
      request<{
        total: number
        kept: number
        removed: number
        pct_removed: number
        sample: { command: string; reason: string }[]
      }>("/api/shell/preview"),
    enabled: false,
  })

  return (
    <>
      <header className="page-heading">
        <div>
          <h1>Understand cleanup before it happens.</h1>
          <p>The Control Center is intentionally read-only. Actual purging stays in the CLI.</p>
        </div>
        <button className="primary-button" onClick={() => preview.refetch()}>
          <Terminal size={16} /> Generate preview
        </button>
      </header>
      {preview.error && <p className="error">{preview.error.message}</p>}
      {preview.data ? (
        <>
          <div className="stat-grid four">
            {(["total", "kept", "removed", "pct_removed"] as const).map((key) => (
              <div className="stat-card" key={key}>
                <span>{key.replace("_", " ")}</span>
                <strong>
                  {key === "pct_removed"
                    ? `${preview.data[key].toFixed(1)}%`
                    : preview.data[key]}
                </strong>
              </div>
            ))}
          </div>
          <div className="command-list">
            {preview.data.sample.map((item, index) => (
              <div className="command-row" key={`${item.command}-${index}`}>
                <code>{item.command}</code>
                <span>{item.reason}</span>
              </div>
            ))}
          </div>
        </>
      ) : (
        <EmptyState
          title="No preview generated"
          body="Run the preview to inspect impact. Nothing will be changed."
        />
      )}
    </>
  )
}

function LibraryView({
  selected,
  setSelected,
}: {
  selected: string | null
  setSelected: (id: string) => void
}) {
  const [filter, setFilter] = useState("")
  const [kindFilter, setKindFilter] = useState("all")
  const catalog = useQuery({
    queryKey: ["library"],
    queryFn: () =>
      request<{ items: LibraryItem[]; groups: Record<string, number> }>("/api/library"),
  })
  const detail = useQuery({
    queryKey: ["library-item", selected],
    queryFn: () => request<LibraryDetail>(`/api/library/${selected}`),
    enabled: Boolean(selected),
  })
  const filtered = (catalog.data?.items || []).filter(
    (item) =>
      (kindFilter === "all" || item.kind === kindFilter) &&
      (item.name.toLowerCase().includes(filter.toLowerCase()) ||
        item.path.toLowerCase().includes(filter.toLowerCase())),
  )
  const kindOrder = ["agents", "prompts", "skills", "instructions", "hooks"]
  const availableKinds = kindOrder.filter((kind) => catalog.data?.groups[kind])

  return (
    <>
      <header className="page-heading">
        <div>
          <h1>The operating system behind your agents.</h1>
          <p>Read-only access to prompts, skills, agents, instructions, and hooks.</p>
        </div>
      </header>
      <div className="library-filters" aria-label="Filter library by type">
        <button
          className={kindFilter === "all" ? "active" : ""}
          onClick={() => setKindFilter("all")}
        >
          All <span>{catalog.data?.items.length || 0}</span>
        </button>
        {availableKinds.map((kind) => (
          <button
            className={kindFilter === kind ? "active" : ""}
            data-kind={kind}
            key={kind}
            onClick={() => setKindFilter(kind)}
          >
            {kind} <span>{catalog.data?.groups[kind]}</span>
          </button>
        ))}
      </div>
      <div className="library-layout">
        <aside className="library-index">
          <div className="filter-input">
            <Search size={16} />
            <input
              aria-label="Filter library"
              placeholder="Filter library..."
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            />
          </div>
          <div className="library-items">
            {filtered.map((item) => (
              <button
                className={selected === item.id ? "library-item active" : "library-item"}
                data-kind={item.kind}
                key={item.id}
                onClick={() => setSelected(item.id)}
              >
                <FileText size={16} />
                <span>
                  <strong>{item.name}</strong>
                  <span className="library-item-meta">
                    <span className="kind-tag">{item.kind}</span>
                    <small>{item.path}</small>
                  </span>
                </span>
              </button>
            ))}
          </div>
        </aside>
        <article className="library-reader">
          {detail.data ? (
            <>
              <div className="reader-heading">
                <div>
                  <h2>{detail.data.name}</h2>
                  <code>{detail.data.path}</code>
                </div>
                <a className="secondary-button" href={detail.data.vscode_url}>
                  <ExternalLink size={16} /> Open in VS Code
                </a>
              </div>
              <div className="markdown-body">
                <Markdown remarkPlugins={[remarkGfm]}>{detail.data.content}</Markdown>
              </div>
            </>
          ) : (
            <EmptyState title="Choose an item" body="Select a library entry to read it here." />
          )}
        </article>
      </div>
    </>
  )
}

function CommandPalette({
  open,
  close,
  agents,
  libraryItems,
  navigate,
}: {
  open: boolean
  close: () => void
  agents: Agent[]
  libraryItems: LibraryItem[]
  navigate: (view: View, libraryItem?: string) => void
}) {
  const [query, setQuery] = useState("")
  const choices = useMemo(
    () =>
      [
        ...agents.map((agent) => ({
          label: agent.name,
          detail: "Agent",
          view: agent.id,
          libraryItem: undefined,
        })),
        ...libraryItems.map((item) => ({
          label: item.name,
          detail: `${item.kind} · ${item.path}`,
          view: "library" as View,
          libraryItem: item.id,
        })),
      ].filter((item) => item.label.toLowerCase().includes(query.toLowerCase())),
    [agents, libraryItems, query],
  )

  if (!open) return null
  return (
    <div className="palette-backdrop" onMouseDown={close}>
      <div className="palette" onMouseDown={(event) => event.stopPropagation()}>
        <div className="palette-input">
          <Search size={18} />
          <input autoFocus placeholder="Jump to anything..." value={query} onChange={(event) => setQuery(event.target.value)} />
          <kbd>esc</kbd>
        </div>
        <div className="palette-results">
          {choices.slice(0, 10).map((choice, index) => (
            <button
              key={`${choice.label}-${index}`}
              onClick={() => {
                navigate(choice.view, choice.libraryItem)
                close()
              }}
            >
              <BookOpen size={16} />
              <span>{choice.label}</span>
              <small>{choice.detail}</small>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function App() {
  const [view, setView] = useState<View>("dashboard")
  const [selectedLibraryItem, setSelectedLibraryItem] = useState<string | null>(null)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [quoteIndex, setQuoteIndex] = useState(0)
  const [theme, setTheme] = useState(document.documentElement.dataset.theme || "dark")
  const agents = useQuery({ queryKey: ["agents"], queryFn: () => request<Agent[]>("/api/agents") })
  const health = useQuery({ queryKey: ["health"], queryFn: () => request<Health>("/api/health"), refetchInterval: 30_000 })
  const libraryCatalog = useQuery({
    queryKey: ["library"],
    queryFn: () => request<{ items: LibraryItem[]; groups: Record<string, number> }>("/api/library"),
  })

  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setPaletteOpen(true)
      }
      if (event.key === "Escape") setPaletteOpen(false)
    }
    window.addEventListener("keydown", keydown)
    return () => window.removeEventListener("keydown", keydown)
  }, [])

  useEffect(() => {
    const timer = window.setInterval(
      () => setQuoteIndex((current) => (current + 1) % controlCenterQuotes.length),
      8_000,
    )
    return () => window.clearInterval(timer)
  }, [])

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark"
    document.documentElement.dataset.theme = next
    localStorage.setItem("mission-control-theme", next)
    setTheme(next)
  }

  const navigate = (nextView: View, libraryItem?: string) => {
    if (libraryItem) setSelectedLibraryItem(libraryItem)
    setView(nextView)
  }

  const content = () => {
    if (view === "findtab") return <FindTabView />
    if (view === "text") return <TextView />
    if (view === "shell") return <ShellView />
    if (view === "library") {
      return (
        <LibraryView
          selected={selectedLibraryItem}
          setSelected={setSelectedLibraryItem}
        />
      )
    }
    return (
      <Dashboard
        agents={agents.data || []}
        navigate={navigate}
      />
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => setView("dashboard")}>
          <span className="brand-mark">🚀</span>
          <span>
            <strong>Prasanna's</strong>
            <small>Control Center</small>
          </span>
        </button>
        <nav>
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                className={view === item.id ? "nav-item active" : "nav-item"}
                key={item.id}
                onClick={() => setView(item.id)}
              >
                <Icon size={18} />
                {item.label}
              </button>
            )
          })}
        </nav>
        <div className="sidebar-footer">
          <div className="principle">
            <span className="principle-icon">●</span>
            <span>
              <strong>Private to this Mac</strong>
              <small>Bound to localhost only</small>
            </span>
          </div>
          <div className="principle">
            <span className="principle-icon">⌘</span>
            <span>
              <strong>Local execution</strong>
              <small>Scripts run on this machine</small>
            </span>
          </div>
          <blockquote key={quoteIndex}>“{controlCenterQuotes[quoteIndex]}”</blockquote>
          <div className="quote-progress" aria-hidden="true">
            {controlCenterQuotes.map((_, index) => (
              <span className={index === quoteIndex ? "active" : ""} key={index} />
            ))}
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <button className="command-trigger" onClick={() => setPaletteOpen(true)}>
            <Search size={16} />
            Jump to agent, skill, or prompt
            <kbd>⌘ K</kbd>
          </button>
          <div className="health-row">
            {Object.entries(health.data?.services || {}).map(([name, service]) => (
              <div className="health-item" key={name}>
                <button className="health-pill" aria-label={`${name}: ${service.status}`}>
                  <StatusDot status={service.status} />
                  {name}
                </button>
                <div className="health-tooltip" role="tooltip">
                  <div className="health-tooltip-heading">
                    <StatusDot status={service.status} />
                    <strong>{name}</strong>
                    <span>{service.status === "healthy" ? "Ready" : "Needs attention"}</span>
                  </div>
                  <p>{service.detail}</p>
                  {service.remedy && (
                    <div className="health-remedy">
                      <span>Terminal remedy</span>
                      <code>{service.remedy}</code>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <button className="icon-button" onClick={toggleTheme} aria-label="Toggle theme">
              {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
            </button>
          </div>
        </header>
        <main>{content()}</main>
      </div>
      <CommandPalette
        open={paletteOpen}
        close={() => setPaletteOpen(false)}
        agents={agents.data || []}
        libraryItems={libraryCatalog.data?.items || []}
        navigate={navigate}
      />
    </div>
  )
}

export default App
