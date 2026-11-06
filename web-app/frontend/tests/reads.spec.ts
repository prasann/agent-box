import { expect, test } from "@playwright/test"

test("Reads search, evidence, consent, capture failures and source preview", async ({ page }, info) => {
  const reading = {
    id: "reading-1", title: "Latency numbers every engineer should know", url: "https://example.org/latency?v=1#memory",
    capture_status: "captured", captured_at: "2026-10-23T12:00:00Z", last_error: null,
    cloud_allowed: 0, note: "", membership_count: 1,
  }
  const passage = { id: "passage-1", heading: "Memory latency", text: "A memory reference takes nanoseconds; a network round trip takes milliseconds." }
  let lastSearch: Record<string, unknown> = {}
  let accepted = false
  await page.route("**/api/**", async route => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    let body: unknown = {}
    if (path === "/api/agents") body = [{ id: "reads", name: "Reads", status: "healthy", description: "Saved reading search", actions: [] }]
    if (path === "/api/library") body = { items: [], groups: {} }
    if (path === "/api/health") body = { status: "healthy", services: {} }
    if (path === "/api/reads/status") body = { total: 1, captured: 1, documents: [reading], sources: [], providers: { lexical: true, llm: true, decision: false }, jobs: [] }
    if (path === "/api/reads/search") {
      lastSearch = request.postDataJSON()
      body = { query: lastSearch.query, mode: "lexical-only", partial: false, warnings: [], calls: 0,
        assessed_packs: 0, eligible_packs: 0, elapsed_seconds: 0.01, ambiguous: false,
        results: [{ ...reading, category: "content-match", excerpt: passage.text, heading: passage.heading }] }
    }
    if (path === "/api/reads/documents/reading-1") {
      if (request.method() === "PATCH") Object.assign(reading, request.postDataJSON())
      body = { ...reading, passages: [passage] }
    }
    if (path === "/api/reads/capture") body = { outcomes: [{ document: reading.id, state: "failed", error: "Page requires authorization" }] }
    if (path === "/api/reads/snapshots") {
      expect(request.headers()["x-reads-request"]).toBe("1")
      accepted = new URL(request.url()).searchParams.get("dry_run") === "false"
      body = { count: 1, added: 1, removed: 0 }
    }
    await route.fulfill({ json: body })
  })
  await page.goto("/")
  await page.getByRole("navigation").getByRole("button", { name: "Reads", exact: true }).click()
  await expect(page.getByRole("heading", { name: "Reads", exact: true })).toBeVisible()
  await expect(page.getByRole("option", { name: "Microsoft Decision" })).toHaveAttribute("disabled", "")
  await page.getByLabel("What do you remember?").fill("memory latency")
  await page.getByRole("button", { name: "Search", exact: true }).click()
  await expect(page.getByText(passage.text)).toBeVisible()
  expect(lastSearch.local_only).toBe(true)
  expect(lastSearch.provider).toBe("lexical")
  await expect(page.getByRole("link", { name: reading.title })).toHaveAttribute("href", reading.url)
  await page.screenshot({ path: `/tmp/reads-${info.project.name}-search.png`, fullPage: true })
  await page.getByRole("button", { name: "Inspect reading" }).click()
  await expect(page.getByRole("heading", { name: reading.title })).toBeVisible()
  const approval = page.getByRole("checkbox", { name: /Allow this reading/ })
  await expect(approval).not.toBeChecked()
  await page.getByLabel("Notes", { exact: true }).fill("Useful memory and network comparison")
  await approval.check()
  await page.getByRole("button", { name: "Save changes" }).click()
  await expect(page.getByRole("button", { name: "Save changes" })).toBeDisabled()
  expect(reading.cloud_allowed).toBe(true)
  expect(reading.note).toBe("Useful memory and network comparison")
  await page.getByRole("button", { name: "Refresh public capture" }).click()
  await expect(page.getByRole("alert")).toHaveText("Page requires authorization")
  await expect(page.getByText(passage.text)).toBeVisible()
  await page.screenshot({ path: `/tmp/reads-${info.project.name}-collection.png`, fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.getByRole("tab", { name: "Sources" }).click()
  await page.getByText("Adapter snapshot", { exact: true }).click()
  await page.getByLabel("Preview adapter snapshot").setInputFiles({ name: "synthetic.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify({ complete: true })) })
  await expect(page.getByText("1 bookmarks · 1 added · 0 removed")).toBeVisible()
  expect(accepted).toBe(false)
  await page.getByRole("button", { name: "Accept complete snapshot" }).click()
  await expect(page.getByText("Snapshot accepted.")).toBeVisible()
  expect(accepted).toBe(true)
})