---
name: diagram-prompts
description: Create and refine concise natural-language prompts for DrawIO and other diagram-generation tools. Use when turning documents or requirements into diagram prompts, choosing diagram views and boundaries, reviewing generated diagram screenshots, or writing targeted change requests. Covers canvas sizing, component placement, exact connections, readable styling, and deciding when to redraw. Produces prompts rather than diagram files unless explicitly requested.
---

# Diagram Prompts

Turn source material into clear visual instructions for a diagramming tool.
Separate architectural reasoning from the prompt that the user copies.

## 1. Agree on the View Before Drawing

Identify the audience, the question the diagram answers, and the intended
medium: document, slide, print or interactive canvas.

Choose one primary organizing principle:

| View | Organizing principle |
| --- | --- |
| Logical/component | Responsibilities and dependencies |
| Deployment/environment | Where components run and which calls cross environments |
| Network | Verified connectivity, zones, ingress/egress and enforcement points |
| Request/sequence | Participants and time-ordered interactions |
| Data/persistence | Ownership, reads/writes, stores and lifecycle |

Do not silently turn a logical diagram into a deployment diagram, or call an
environment overview a verified network topology. Split views when necessary.

If the user asks to discuss first, discuss rather than editing files or jumping
to a prompt. Offer a small number of useful views, not an exhaustive catalog.

## 2. Establish the Component and Connection Inventory

Read the supplied source locally where possible. Extract only:

- Components and their concise display names.
- Containment, hosting and placement.
- Directed relationships, including mandatory intermediaries.
- Relevant alternatives, optional capabilities and unresolved assumptions.

Distinguish source facts, user-provided placements, assumptions and unknowns.
An internal service is not automatically on-premises. A cloud dependency is not
automatically inside the application's hosting service. Shared branding does
not imply the same endpoint, process or deployment.

Resolve placement questions that change the layout with the user. Do not invent
subnets, regions, firewalls, private links or deployment facts to fill gaps.
Keep an assumption visible in surrounding notes when using a user-approved
working placement. Never describe a draft design as validated deployment.

Write an edge list before designing the layout:

```text
Caller -> Access gateway -> Application
Application -> Model gateway -> Model endpoint
Application -> Business gateway -> Business API
Application -> Store A
Application -> Store B
```

Differentiate endpoints with similar names. Explicitly prohibit bypass arrows
where an intermediary is mandatory. Avoid separate response arrows unless
response behavior is important to the selected view.

## 3. Make Boundaries Consistent

Every enclosure must have an explainable meaning.

- Deployment view: outer environments, nested hosting/service containers.
- Logical view: functional modules, not incidental location enclosures.
- Network view: only verified network/security zones and controls.
- Sequence view: participant lanes and optional/conditional fragments.

Nested service containers are valid inside environments, but label their role
clearly. Avoid scattering location tags through functional groupings and then
adding a large legend to explain the mixture.

Do not add Memory, Security or Observability boxes merely for decoration.
Use individual service boxes when extra grouping adds no meaning.
Keep SDK modules inside the application; do not imply they are microservices.

## 4. Plan the Canvas and Layout Together

Specify the canvas early, not after repeated cramped generations.

- For a moderately detailed landscape overview, a useful starting target is
  1600 x 1000 canvas units. Use 16:9 when slide presentation is the requirement.
- Treat dimensions as a requested target, not a verified tool capability.
- A single canvas is not inherently cramped; page size, auto-fit, zoom and
  export scaling are separate concerns.
- If the page is fixed, simplify labels, collapse detail or split views.
  Do not solve density by repeatedly shrinking text.

Assign relative placement before styling:

1. Main flow aligned across the middle.
2. Closely related dependencies above their consumers.
3. Stores below the components that access them.
4. Downstream dependencies beside their callers.
5. Separate corridors for cross-environment and feedback paths.

Use whitespace deliberately. Starting guides, not universal constraints:

- Container padding: 24-32 canvas units plus dedicated heading space.
- Between related boxes: 24-40 units.
- Major routing corridors: 60-100 units, adjusted to line count.
- Between parallel connectors: 16-24 units.

Avoid global instructions such as "spread everything horizontally".
Compress sparse areas selectively and expand congested hubs selectively.
Aim for readable export dimensions, not just a diagram that fits at editor zoom.

Collapse detail that belongs in another view. A representative application box
is often better than every internal role in a deployment overview.
Mention alternative hosts in a caption unless comparison is the purpose.

## 5. Write a Compact Create Prompt

The diagram tool needs objects, containment, placement, edges and styling.
It does not need the reasoning process, source history or approval register.

Use this structure, replacing placeholders with concrete instructions:

```text
Create a NEW editable [diagram type], titled "[title]".

CANVAS
[Dimensions/aspect target, reading direction, outer margin.]

CONTAINMENT AND PLACEMENT
[Named outer containers and their contents.]
[Nested containers, relative placement and alignment.]

CONNECTIONS
[Explicit source -> destination list and short labels.]
[Required intermediary paths and important prohibited shortcuts.]

ROUTING
[Distinct corridors, attachment points, heading clearance.]
[Which feedback/cross-boundary lines need separation.]

STYLE
[Readable typography, restrained colors, padding and export background.]
[Small legend if line styles have distinct meanings.]
[Short caption only when needed.]
```

Make the block standalone for use in a fresh tool session.
Use short labels rather than prose inside boxes.
Keep architecture caveats and references outside the copyable block unless
they change interpretation. A draft title can avoid repeated "proposed" labels,
but do not erase meaningful distinctions between optional, future and current
capabilities.

Typography must match the requested canvas. For a 1600 x 1000 target, a
starting hierarchy is 22 title / 18 headings / 14 box text / 12 connector labels,
in the tool's supported units. Do not treat these as universal minimums.
Resize boxes for text, not text for boxes. Allow padding and separate subtitles.
Keep icons small and beside text. White background and subtle fills usually
export well; honor the user's medium and theme.

Do not send confidential source content to an external diagramming service.
Prepare prompts locally and use only approved destinations.

## 6. Review Generated Diagrams in the Right Order

Review screenshots or native diagrams without assuming visual neatness implies
correctness. At low resolution, qualify uncertain endpoints rather than
asserting an error. Ask for native files or a closer view when necessary.

Check:

1. **Semantics:** correct component inventory, placement and containment?
2. **Edges:** every arrow starts/ends at the intended component? Any bypasses,
   missing edges, duplicate paths or accidental junctions?
3. **Hierarchy:** does the main flow stand out? Consistent boundary meanings?
4. **Routing:** lines clear of headings, labels and unrelated boxes?
5. **Readability:** sufficient spacing, unclipped text and usable export scale?
6. **Polish:** alignment, line weights, icons, grid and canvas cropping?

Pay particular attention to stores: arrows routed near model or retrieval
boxes must not accidentally attach to them instead of the application.
Connections should terminate on components, not their container headings.
Crossings are not junctions; use line jumps where unavoidable.

Name concrete defects and prioritize them. Do not respond to every screenshot
with another generic spacing/style prescription.

## 7. Refine or Redraw Deliberately

**Refine** when the structure is sound and defects are local:
overlaps, labels, endpoint errors, uneven spacing or a congested corridor.

**Redraw** when the organizing principle, containment or detail level changes,
or when repeated edits preserve an unsuitable layout.

For an edit prompt, state exactly what stays unchanged and limit the scope:

```text
Refine the existing diagram; do not recreate it.
Preserve [specific regions, components and relationships].

Change only:
1. [Concrete defect and desired result.]
2. [Concrete placement/routing change.]
3. [Readability adjustment with box resizing, not font shrinking.]

Do not add components, infer locations or change unrelated relationships.
```

Prefer one bounded revision over a long list of unrelated improvements.
If natural-language edits repeatedly fail, offer precise manual adjustments or
native-file editing when available instead of another speculative prompt.
Do not claim token limits or a tool configuration caused a defect without
evidence. A fresh session is a practical reset, not a diagnosis.

## Deliverables and Completion

- Discuss options before prompts when the user requests it.
- If Markdown files are requested, keep one current create prompt per view;
  include a targeted change prompt only when useful, not every obsolete attempt.
- Update the relevant file when explicitly asked to persist a revision.
- Follow repository frontmatter/templates and Markdown validation for saved
  workspace documents. Do not change unrelated documentation.
- A prompt passing lint does not verify its generated diagram.
- Finish with the exact source/destination paths worth checking after generation.
- Stop polishing when semantics and readability are satisfactory.

Keep this skill project-neutral. Do not add customer names, internal service
placements, confidential source excerpts or task-specific assumptions.
