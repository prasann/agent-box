import assert from "node:assert/strict"
import { test } from "node:test"

const events = () => ({ addListener() {} })
globalThis.chrome = {
  runtime: { onMessage: events(), onStartup: events(), onInstalled: events() },
  bookmarks: { onCreated: events(), onChanged: events(), onMoved: events(), onRemoved: events() },
  alarms: { onAlarm: events() },
}
const { flatten } = await import("./background.js")

test("snapshot includes only selected subtree HTTP bookmarks and preserves exact URLs", () => {
  const items = flatten({ id: "17", title: "Reads", children: [
    { id: "18", title: "Reference", children: [
      { id: "19", title: "API", url: "https://example.org/docs?version=1#auth", dateAdded: 1000 },
    ] },
    { id: "20", title: "Not a reading", url: "edge://settings" },
  ] })
  assert.equal(items.length, 1)
  assert.equal(items[0].folder_path, "Reads/Reference")
  assert.equal(items[0].url, "https://example.org/docs?version=1#auth")
  assert.equal(items[0].item_id, "19")
})