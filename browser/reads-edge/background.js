const HOST = "com.agentbox.reads"
let running = false
let sequence = Promise.resolve()

function serialized(action) {
  const result = sequence.then(action)
  sequence = result.catch(() => {})
  return result
}

async function identity() {
  const state = await chrome.storage.local.get(["profileId", "revision"])
  if (!state.profileId) {
    state.profileId = crypto.randomUUID()
    await chrome.storage.local.set({ profileId: state.profileId })
  }
  return state
}

export function flatten(node, path = []) {
  if (node.url) {
    if (!/^https?:\/\//i.test(node.url)) return []
    return [{ item_id: node.id, url: node.url, title: node.title || node.url,
      folder_path: path.join("/"), saved_at: node.dateAdded ? new Date(node.dateAdded).toISOString() : null }]
  }
  return (node.children || []).flatMap(child => flatten(child, [...path, node.title]))
}

async function snapshot(folderId) {
  const [root] = await chrome.bookmarks.getSubTree(folderId)
  if (!root || root.url) throw new Error("Selected bookmark folder is unavailable")
  const state = await identity()
  const revision = Math.max(Date.now(), (state.revision || 0) + 1)
  await chrome.storage.local.set({ revision })
  return { source_id: "edge", profile_id: state.profileId, folder_id: folderId,
    revision, complete: true, items: flatten(root) }
}

async function sendPending() {
  if (running) return
  running = true
  try {
    const { pending } = await chrome.storage.local.get("pending")
    if (!pending) return
    const response = await chrome.runtime.sendNativeMessage(HOST, { action: "snapshot", snapshot: pending })
    if (!response?.ok) throw new Error(response?.error || "Native host rejected snapshot")
    const current = await chrome.storage.local.get("pending")
    if (current.pending?.revision === pending.revision) {
      await chrome.storage.local.remove("pending")
      await chrome.storage.local.set({ lastSync: new Date().toISOString(), lastError: null })
    }
  } catch (error) {
    await chrome.storage.local.set({ lastError: error.message })
  } finally {
    running = false
  }
}

async function reconcile() {
  const { folderId } = await chrome.storage.local.get("folderId")
  if (!folderId) return
  try {
    const complete = await snapshot(folderId)
    await chrome.storage.local.set({ pending: complete })
    await sendPending()
  } catch (error) {
    await chrome.storage.local.set({ lastError: error.message })
  }
}

chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (sender.id !== chrome.runtime.id) return false
  const action = async () => {
    if (message.action === "preview") return snapshot(message.folderId)
    if (message.action === "accept") {
      const current = await snapshot(message.snapshot.folder_id)
      if (JSON.stringify(current.items) !== JSON.stringify(message.snapshot.items)) {
        throw new Error("Bookmarks changed after preview; preview the folder again")
      }
      await chrome.storage.local.set({ folderId: current.folder_id, pending: current })
      await chrome.alarms.create("reads-reconcile", { periodInMinutes: 1 })
      await sendPending()
      return chrome.storage.local.get(["lastSync", "lastError", "pending"])
    }
    if (message.action === "sync") { await reconcile(); return chrome.storage.local.get(["lastSync", "lastError", "pending"]) }
    if (message.action === "capture") {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      const { folderId } = await chrome.storage.local.get("folderId")
      if (!folderId) throw new Error("No accepted Reads folder")
      const selected = await snapshot(folderId)
      if (!selected.items.some(item => item.url === tab.url)) throw new Error("Current tab is not saved in the selected Reads subtree")
      const [{ result }] = await chrome.scripting.executeScript({ target: { tabId: tab.id },
        func: () => ({ url: location.href, html: document.documentElement.outerHTML }) })
      if (new TextEncoder().encode(result.html).length > 800000) throw new Error("Rendered page exceeds the 800 KB capture limit")
      const response = await chrome.runtime.sendNativeMessage(HOST, { action: "capture", ...result })
      if (!response?.ok) throw new Error(response?.error || "Capture rejected")
      return response.result
    }
    throw new Error("Unsupported extension action")
  }
  serialized(action).then(result => respond({ ok: true, result })).catch(error => respond({ ok: false, error: error.message }))
  return true
})

for (const event of [chrome.bookmarks.onCreated, chrome.bookmarks.onChanged, chrome.bookmarks.onMoved, chrome.bookmarks.onRemoved]) {
  event.addListener(() => { void serialized(reconcile) })
}
chrome.alarms.onAlarm.addListener(alarm => { if (alarm.name === "reads-reconcile") void serialized(reconcile) })
chrome.runtime.onStartup.addListener(() => { void serialized(reconcile) })
chrome.runtime.onInstalled.addListener(() => { void chrome.alarms.create("reads-reconcile", { periodInMinutes: 1 }); void serialized(reconcile) })