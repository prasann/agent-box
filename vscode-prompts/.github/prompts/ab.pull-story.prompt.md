---
description: "Fetch Azure DevOps work item via MCP and save to specs folder"
---

# Azure DevOps Story Import

## Instructions

1. Use `mcp_ado_wit_get_work_item` MCP tool to fetch the specified work item
2. Create markdown file: `specs/ado-{work-item-id}-{title-slug}.md`
3. Include only:
   * Title
   * Description (with acceptance criteria)

## Usage

```plaintext
@workspace pull story {STORY_NUMBER} into specs/
```