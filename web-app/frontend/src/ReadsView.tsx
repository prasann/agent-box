import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { BookOpen, Check, ExternalLink, FileUp, RefreshCw, Save, Search, ShieldCheck } from "lucide-react"
import "./ReadsView.css"

type Reading = {
  id: string
  title: string
  url: string
  note: string
  cloud_allowed: number
  capture_status: string
  captured_at: string | null
  last_error: string | null
  membership_count: number
}
type Passage = { id: string; heading: string; text: string }
type Source = { id: string; source_id: string; profile_id: string; folder_id: string; revision: number }
type Collection = {
  total: number
  captured: number
  documents: Reading[]
  sources: Source[]
  providers: Record<string, boolean>
  jobs: { document: string; state: string; attempts: number; last_error: string | null }[]
}
type SearchResult = {
  query: string
  mode: string
  partial: boolean
  warnings: string[]
  calls: number
  assessed_packs: number
  eligible_packs: number
  elapsed_seconds: number
  ambiguous: boolean
  results: {
    id: string; title: string; url: string; category: string; excerpt: string | null
    heading: string; captured_at: string | null; capture_status: string; last_error: string | null
  }[]
}

async function api<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch(`/api/reads${path}`, {
    method,
    headers: { "Content-Type": "application/json", "X-Reads-Request": "1" },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(typeof error.detail === "string" ? error.detail : "Reads request rejected")
  }
  return response.json()
}

function ReadingEditor({ document, refresh }: { document: Reading & { passages: Passage[] }; refresh: () => void }) {
  const [note, setNote] = useState(document.note)
  const [cloud, setCloud] = useState(Boolean(document.cloud_allowed))
  const save = useMutation({
    mutationFn: () => api(`/documents/${document.id}`, "PATCH", { note, cloud_allowed: cloud }),
    onSuccess: refresh,
  })
  const capture = useMutation({
    mutationFn: () => api<{ outcomes: { state: string; error?: string }[] }>("/capture", "POST", { document: document.id }),
    onSuccess: refresh,
  })
  const dirty = note !== document.note || cloud !== Boolean(document.cloud_allowed)
  return <article className="reads-detail">
    <div className="reads-detail-heading">
      <div><h2>{document.title || document.url}</h2><a href={document.url} target="_blank" rel="noreferrer">{document.url} <ExternalLink size={13} /></a></div>
      <button className="icon-button" title="Refresh public capture" aria-label="Refresh public capture" disabled={capture.isPending} onClick={() => capture.mutate()}><RefreshCw size={17} className={capture.isPending ? "reads-spin" : ""} /></button>
    </div>
    <div className="reads-meta"><span>{document.capture_status}</span><span>{document.membership_count} membership{document.membership_count === 1 ? "" : "s"}</span><span>{document.captured_at ? `Captured ${new Date(document.captured_at).toLocaleString()}` : "Not captured"}</span></div>
    {document.last_error && <p className="reads-warning" role="status">{document.last_error}. {document.passages.length > 0 && "Showing the last successful capture."}</p>}
    {capture.error && <p className="error" role="alert">{capture.error.message}</p>}
    {capture.data?.outcomes.filter(item => item.error).map((item, index) => <p className="error" role="alert" key={index}>{item.error}</p>)}
    <label className="reads-field">Notes<textarea value={note} maxLength={10000} rows={3} onChange={event => setNote(event.target.value)} /></label>
    <label className="reads-check reads-consent"><input type="checkbox" checked={cloud} onChange={event => setCloud(event.target.checked)} /><span>Allow this reading's title, URL, notes, and text to be sent to configured cloud assessors.</span></label>
    <div className="reads-actions"><button className="secondary-button" disabled={!dirty || save.isPending} onClick={() => save.mutate()}>{save.isSuccess && !dirty ? <Check size={15} /> : <Save size={15} />} Save changes</button>{save.error && <span className="error" role="alert">{save.error.message}</span>}</div>
    <h3 className="reads-evidence-label">Captured evidence <span>{document.passages.length} passages</span></h3>
    {document.passages.length === 0 ? <div className="reads-empty"><BookOpen size={24} /><strong>Metadata only</strong><span>{document.capture_status}</span></div> : document.passages.map(passage => <section className="reads-passage" key={passage.id}>{passage.heading && <h4>{passage.heading}</h4>}<p>{passage.text}</p></section>)}
  </article>
}

export default function ReadsView() {
  const cache = useQueryClient()
  const [tab, setTab] = useState<"search" | "collection" | "sources">("search")
  const [query, setQuery] = useState("")
  const [constraints, setConstraints] = useState("")
  const [provider, setProvider] = useState("lexical")
  const [localOnly, setLocalOnly] = useState(true)
  const [filter, setFilter] = useState("")
  const [selected, setSelected] = useState<string | null>(null)
  const [snapshot, setSnapshot] = useState<unknown>(null)
  const [fileError, setFileError] = useState("")
  const collection = useQuery({ queryKey: ["reads"], queryFn: () => api<Collection>("/status"), refetchInterval: 5000 })
  const detail = useQuery({ queryKey: ["reading", selected], queryFn: () => api<Reading & { passages: Passage[] }>(`/documents/${selected}`), enabled: Boolean(selected) })
  const refresh = () => {
    void cache.invalidateQueries({ queryKey: ["reads"] })
    void cache.invalidateQueries({ queryKey: ["reading"] })
  }
  const search = useMutation({ mutationFn: () => api<SearchResult>("/search", "POST", { query, constraints, provider, local_only: localOnly }) })
  const capture = useMutation({ mutationFn: () => api<{ outcomes: { document: string; state: string; error?: string }[] }>("/capture", "POST", {}), onSuccess: refresh })
  const preview = useMutation({ mutationFn: (data: unknown) => api<{ count: number; added: number; removed: number }>("/snapshots?dry_run=true", "POST", data) })
  const accept = useMutation({ mutationFn: () => api("/snapshots?dry_run=false", "POST", snapshot), onSuccess: () => { refresh(); setSnapshot(null); preview.reset() } })
  const readings = collection.data?.documents || []
  const filtered = readings.filter(item => `${item.title} ${item.url}`.toLowerCase().includes(filter.toLowerCase()))
  const inspect = (id: string) => { setSelected(id); setTab("collection") }

  return <div className="reads-view">
    <header className="page-heading reads-heading"><div><h1>Reads</h1><p>Saved readings. Original evidence.</p></div><button className="secondary-button" onClick={() => { refresh() }} title="Refresh collection"><RefreshCw size={16} /> Refresh</button></header>
    <div className="reads-coverage" aria-label="Capture coverage"><div><strong>{collection.data?.total ?? "-"}</strong><span>readings</span></div><div><strong>{collection.data?.captured ?? "-"}</strong><span>captured</span></div><div><strong>{collection.data ? collection.data.total - collection.data.captured : "-"}</strong><span>metadata only</span></div><div className="reads-privacy"><ShieldCheck size={16} /><span>{localOnly ? "Local-only search" : "Approved readings only"}</span></div></div>
    <div className="reads-tabs" role="tablist" aria-label="Reads views">{(["search", "collection", "sources"] as const).map(value => <button id={`reads-tab-${value}`} aria-controls={`reads-panel-${value}`} role="tab" aria-selected={tab === value} key={value} className={tab === value ? "active" : ""} onClick={() => setTab(value)}>{value === "search" ? "Search" : value === "collection" ? "Collection" : "Sources"}{value === "sources" && <span>{collection.data?.sources.length || 0}</span>}</button>)}</div>
    {collection.isPending && <p className="muted" role="status">Loading collection...</p>}
    {collection.error && <p className="error" role="alert">{collection.error.message}</p>}
    {tab === "search" && <section role="tabpanel" id="reads-panel-search" aria-labelledby="reads-tab-search">
      <form className="reads-search" onSubmit={event => { event.preventDefault(); search.mutate() }}>
        <label htmlFor="reads-query">What do you remember?</label>
        <div className="reads-query"><Search size={20} /><input id="reads-query" value={query} maxLength={2000} placeholder="That explanation of latency numbers..." onChange={event => setQuery(event.target.value)} /><button className="primary-button" disabled={!query.trim() || search.isPending}><Search size={16} />{search.isPending ? "Searching..." : "Search"}</button></div>
        <div className="reads-search-options"><label className="reads-field">Assessor<select value={provider} onChange={event => setProvider(event.target.value)}><option value="lexical">Local lexical</option><option value="llm" disabled={!collection.data?.providers.llm}>Structured LLM{!collection.data?.providers.llm ? " · Not configured" : ""}</option><option value="decision" disabled={!collection.data?.providers.decision}>Microsoft Decision{!collection.data?.providers.decision ? " · Not configured" : ""}</option></select></label><label className="reads-field reads-constraints">Constraints<input value={constraints} maxLength={2000} placeholder="Not the Azure one" onChange={event => setConstraints(event.target.value)} /></label><label className="reads-check"><input type="checkbox" checked={localOnly} onChange={event => setLocalOnly(event.target.checked)} />Local only</label></div>
      </form>
      {search.error && <p className="error" role="alert">{search.error.message}</p>}
      {search.data && <div className="reads-search-results" aria-live="polite">
        <div className="reads-meta"><strong>{search.data.results.length} matches</strong><span>{search.data.mode}</span><span>{search.data.elapsed_seconds}s</span><span>{search.data.calls} model calls</span>{search.data.eligible_packs > 0 && <span>{search.data.assessed_packs}/{search.data.eligible_packs} evidence packs assessed</span>}</div>
        {search.data.warnings.map(warning => <p className="reads-warning" key={warning}>{warning}</p>)}
        {search.data.partial && <p className="reads-warning"><strong>Partial search.</strong> Not all eligible evidence was assessed.</p>}
        {search.data.ambiguous && <p className="reads-warning">Several possible matches. Which of these headings sounds closest?</p>}
        {search.data.results.map(item => <article className="reads-result" key={item.id}><div className="reads-result-heading"><h2><a href={item.url} target="_blank" rel="noreferrer">{item.title || item.url}<ExternalLink size={15} /></a></h2><span className="reads-badge">{item.category.replaceAll("-", " ")}</span></div><a className="reads-url" href={item.url} target="_blank" rel="noreferrer">{item.url}</a>{item.heading && <h3>{item.heading}</h3>}{item.excerpt && <blockquote>{item.excerpt}</blockquote>}{item.last_error && <p className="reads-warning">{item.last_error}. Last successful capture retained.</p>}<div className="reads-meta"><span>{item.captured_at ? `Captured ${new Date(item.captured_at).toLocaleDateString()}` : "No captured text"}</span><button className="reads-link" onClick={() => inspect(item.id)}><BookOpen size={14} /> Inspect reading</button></div></article>)}
        {search.data.results.length === 0 && <div className="reads-empty"><Search size={24} /><strong>{search.data.partial ? "No confirmed match in assessed evidence" : "No matching evidence"}</strong></div>}
      </div>}
      {!search.data && !search.isPending && <div className="reads-empty"><BookOpen size={28} /><strong>{readings.length ? "Your saved reading collection" : "No saved readings connected"}</strong><span>{readings.length ? `${readings.length} readings · ${collection.data?.captured || 0} captured` : "Awaiting the first accepted source snapshot"}</span></div>}
    </section>}
    {tab === "collection" && <section role="tabpanel" id="reads-panel-collection" aria-labelledby="reads-tab-collection">
      <div className="reads-toolbar"><div className="filter-input"><Search size={16} /><input aria-label="Filter readings" placeholder="Filter readings..." value={filter} onChange={event => setFilter(event.target.value)} /></div><button className="secondary-button" disabled={capture.isPending || !readings.length} onClick={() => capture.mutate()}><RefreshCw size={16} className={capture.isPending ? "reads-spin" : ""} />{capture.isPending ? "Capturing..." : "Capture pending"}</button></div>
      {capture.error && <p className="error" role="alert">{capture.error.message}</p>}
      {capture.data && <div role="status">{capture.data.outcomes.length === 0 ? <p className="muted">No pending captures ready to run.</p> : capture.data.outcomes.map(item => <p className={item.error ? "reads-warning" : "muted"} key={item.document}>{readings.find(reading => reading.id === item.document)?.title}: {item.error || item.state}</p>)}</div>}
      <div className="reads-collection"><div className="reads-index">{filtered.map(item => <button className={selected === item.id ? "reads-index-item active" : "reads-index-item"} key={item.id} onClick={() => setSelected(item.id)}><BookOpen size={16} /><span><strong>{item.title || item.url}</strong><small>{item.capture_status} · {item.cloud_allowed ? "Cloud approved" : "Local only"}</small>{item.last_error && <small className="reads-error-label">{item.last_error}</small>}</span></button>)}{!filtered.length && <div className="reads-empty"><strong>No readings</strong></div>}</div><div className="reads-reader">{selected && detail.isPending ? <p role="status">Loading reading...</p> : detail.error ? <p className="error" role="alert">{detail.error.message}</p> : detail.data ? <ReadingEditor key={`${detail.data.id}:${detail.data.note}:${detail.data.cloud_allowed}`} document={detail.data} refresh={refresh} /> : <div className="reads-empty"><BookOpen size={24} /><strong>No reading selected</strong></div>}</div></div>
    </section>}
    {tab === "sources" && <section role="tabpanel" id="reads-panel-sources" aria-labelledby="reads-tab-sources">
      <div className="section-heading"><h2>Connected sources</h2><span className="muted">Edge · Native messaging</span></div>
      {collection.data?.sources.map(source => <div className="reads-source" key={source.id}><BookOpen size={22} /><div><h3>{source.source_id}</h3><dl><dt>Profile</dt><dd>{source.profile_id}</dd><dt>Folder ID</dt><dd>{source.folder_id}</dd><dt>Accepted revision</dt><dd>{source.revision}</dd></dl></div></div>)}
      {!collection.data?.sources.length && <div className="reads-empty"><BookOpen size={24} /><strong>No source connected</strong><span>Awaiting an accepted Reads subtree snapshot</span></div>}
      <details className="reads-snapshot"><summary><FileUp size={16} /> Adapter snapshot</summary><input type="file" accept=".json,application/json" aria-label="Preview adapter snapshot" onChange={async event => {
        setFileError(""); preview.reset(); accept.reset(); setSnapshot(null)
        const file = event.target.files?.[0]
        if (!file) return
        try {
          if (file.size > 4 * 1024 * 1024) throw new Error("Snapshot exceeds 4 MB")
          const parsed: unknown = JSON.parse(await file.text()); setSnapshot(parsed); preview.mutate(parsed)
        } catch (error) { setFileError(error instanceof Error ? error.message : "Invalid snapshot") }
      }} />{fileError && <p className="error" role="alert">{fileError}</p>}{preview.error && <p className="error" role="alert">{preview.error.message}</p>}{preview.isPending && <p role="status">Validating snapshot...</p>}{preview.data && <div className="reads-actions"><p>{preview.data.count} bookmarks · {preview.data.added} added · {preview.data.removed} removed</p><button className="primary-button" disabled={accept.isPending} onClick={() => accept.mutate()}><Check size={16} /> Accept complete snapshot</button></div>}{accept.error && <p className="error" role="alert">{accept.error.message}</p>}{accept.isSuccess && <p role="status">Snapshot accepted.</p>}</details>
    </section>}
  </div>
}