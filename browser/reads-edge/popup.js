const folder = document.querySelector("#folder")
const status = document.querySelector("#status")
const items = document.querySelector("#items")
const accept = document.querySelector("#accept")
let preview = null

async function send(message) {
  const response = await chrome.runtime.sendMessage(message)
  if (!response?.ok) throw new Error(response?.error || "Extension request failed")
  if (response.result?.lastError) throw new Error(response.result.lastError)
  return response.result
}

function showFolders(node, depth = 0) {
  if (node.url) return
  if (node.id !== "0") {
    const option = document.createElement("option")
    option.value = node.id
    option.textContent = `${"  ".repeat(depth)}${node.title || "Bookmarks"} [${node.id}]`
    folder.append(option)
  }
  for (const child of node.children || []) showFolders(child, depth + 1)
}

const [tree] = await chrome.bookmarks.getTree()
showFolders(tree)
const state = await chrome.storage.local.get(["folderId", "lastSync", "lastError", "pending"])
if (state.folderId) folder.value = state.folderId
status.textContent = state.lastError || (state.pending ? "Sync pending" : state.lastSync ? `Last sync: ${new Date(state.lastSync).toLocaleString()}` : "Not connected")
folder.addEventListener("change", () => { preview = null; accept.hidden = true; items.replaceChildren() })

for (const action of ["preview", "accept", "sync", "capture"]) {
  document.querySelector(`#${action}`).addEventListener("click", async event => {
    event.target.disabled = true
    status.textContent = "Working..."
    try {
      if (action === "preview") {
        preview = await send({ action, folderId: folder.value })
        items.replaceChildren()
        for (const item of preview.items) {
          const row = document.createElement("li")
          row.textContent = `${item.title} — ${item.folder_path}`
          items.append(row)
        }
        status.textContent = `${preview.items.length} bookmarks in this subtree`
        accept.hidden = false
      } else {
        if (action === "accept" && !preview) throw new Error("Preview a folder first")
        const result = await send({ action, snapshot: preview })
        status.textContent = action === "capture" ? "Captured locally" : result?.pending ? "Sync pending" : "Snapshot accepted"
        if (action === "accept") accept.hidden = true
      }
    } catch (error) { status.textContent = error.message }
    finally { event.target.disabled = false }
  })
}