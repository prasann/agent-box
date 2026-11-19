---
name: agb-pull-story
description: Import an Azure DevOps work item into the target project's specs folder. Use when asked to pull or import an Azure DevOps story by work item ID.
---

# Import an Azure DevOps story

1. Identify the target project and work item ID. Ask for any missing organization or project information required by the available integration.
2. Use the available Azure DevOps work-item integration to fetch the work item. Tool names vary by client; do not assume a particular MCP tool name.
3. If no suitable integration is configured, or the request fails, explain the missing integration or error and stop. Never invent work item content.
4. Save `specs/ado-{work-item-id}-{title-slug}.md` inside the target project, not the toolkit repository. Use a lowercase, hyphen-separated filename-safe title slug.
5. Include only the title and description, including acceptance criteria. Preserve the source content; do not add implementation plans or inferred requirements.
6. Ask before overwriting an existing file, then confirm the saved path.
