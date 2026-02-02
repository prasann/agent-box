````chatskill
# Code Reviewer Skill

Analyze code changes and generate review comments based on project conventions and best practices.

## Purpose

This skill performs the core review analysis:
1. Analyze changed files against project conventions
2. Detect issues across multiple categories
3. Generate review comments with appropriate severity
4. Support focused reviews on specific aspects
5. Perform cross-file consistency checks

## Invocation

**When**: After session initialization, when ready to analyze code

**Input**:
```json
{
  "files_changed": ["src/example.py", "tests/test_example.py"],
  "conventions": {
    "loaded_files": ["testing.instructions.md"],
    "critical_rules": ["No unused imports", "TDD required"]
  },
  "focus_areas": ["testing", "types"],  // Optional: specific areas to emphasize
  "state_file": ".copilot-tracking/pr-reviews/feature-1234.state.json"
}
```

**Output**:
```json
{
  "success": true,
  "files_analyzed": 12,
  "comments_generated": 15,
  "pending_comments": [
    {
      "id": "comment-1",
      "file": "src/example.py",
      "line": 42,
      "severity": "HIGH",
      "category": "type-safety",
      "comment": "Missing type annotation...",
      "suggestion": "Add return type: ...",
      "reference": "code-structure.instructions.md",
      "status": "pending"
    }
  ],
  "summary": {
    "critical": 2,
    "default": 13
  }
}
```

## Implementation

### 1. Prepare Context

Load `templates/pr-review/severity-guidelines.md` and `comment-examples.md`. Parse conventions into checklist. Determine scope from focus areas (comprehensive vs targeted).

### 2. Analyze Files

For each file in `files_changed`, read content and diff. Apply checks:

**A. Import Hygiene**: Unused imports (F401)
- Severity: DEFAULT
- Ref: code-and-documentation-hygiene.instructions.md

**B. Type Safety**: Missing annotations, incorrect TypedDict, unnecessary cast(), dict[str, Any] where TypedDict exists
- Severity: DEFAULT
- Ref: code-structure.instructions.md, langgraph-patterns.instructions.md

**C. Testing**: New functions without tests, missing edge/error cases
- Severity: DEFAULT
- Ref: testing.instructions.md

**D. Documentation**: README out of sync, missing API docs
- Severity: DEFAULT
- Ref: code-and-documentation-hygiene.instructions.md

**E. Comments**: Temporal markers, narrative, contradictions, obvious comments
- Severity: DEFAULT
- Ref: copilot-instructions.md

**F. Architecture**: LangGraph immutability, pure nodes, SRP violations, complexity >50 lines
- Severity: DEFAULT (CRITICAL if breaks functionality)
- Ref: langgraph-patterns.instructions.md, code-structure.instructions.md

**G. Security**: SQL injection, hardcoded secrets, auth issues, exposed data
- Severity: CRITICAL
- Ref: Security best practices

**H. Performance**: N+1 queries, inefficient algorithms, missing pagination
- Severity: DEFAULT (CRITICAL if causes outage)
- Ref: Performance best practices

### 3. Cross-File Checks

- **Consistency**: Same concept named differently (user_id vs userId)
- **Completeness**: Implementation without tests, missing docs
- **Breaking changes**: Signature changes, removed methods

Comment includes all related file:line references.

### 4. Generate Comments

Create comment objects using `templates/pr-review/comment-examples.md` format:
```json
{
  "id": "comment-1",
  "file": "path/to/file.py",
  "line": 42,
  "severity": "CRITICAL" | "DEFAULT",
  "category": "type-safety",
  "comment": "<formatted text>",
  "suggestion": "<code if applicable>",
  "reference": "<guideline>",
  "status": "pending"
}
```

Classify severity using `templates/pr-review/severity-guidelines.md` decision tree:
- Security, data loss, constitution MUST, broken functionality → CRITICAL
- Everything else → DEFAULT

### 5. Focus Filtering

If focus areas specified:
- **Primary**: Detailed comments for focus area
- **Secondary**: Brief CRITICAL comments outside focus
- **Suppress**: Skip DEFAULT outside focus

### 6. Update State

Write comments to `pendingComments` array. Update `filesReviewed`, `lastUpdated`, set `reviewStatus` to "pending-approval". Preserve existing approved/skipped/revised comments.

### 7. Return Results

Return summary with counts by severity, category, and file.

## Severity Classification

**CRITICAL** (blocking): Security, data loss, constitution MUST, broken functionality, crashes

**DEFAULT** (all else): Tests, types, docs, imports, quality, architecture, performance, style

Decision tree:
```
Security | Data loss | Constitution MUST | Broken functionality?
├─ Yes → CRITICAL
└─ No → DEFAULT
```

## Category Definitions

- **imports**: Import hygiene, unused imports, import patterns
- **type-safety**: Type annotations, TypedDict usage, cast() usage
- **testing**: Test coverage, test quality, TDD compliance
- **documentation**: README sync, API docs, inline documentation
- **comments**: Comment quality, temporal markers, policy violations
- **architecture**: Design patterns, module boundaries, complexity
- **security**: Vulnerabilities, secrets, authentication, data exposure
- **performance**: N+1 queries, algorithm efficiency, optimization
- **consistency**: Naming, duplication, cross-file consistency

## Special Cases

- **Large files (>500 lines)**: Focus on changed sections only
- **Legacy code**: Focus on new code, note if perpetuating bad patterns
- **Generated code**: Skip detailed analysis, flag only CRITICAL
- **Test files**: Check AAA pattern, coverage, isolation

## Error Handling

- **File read errors**: Skip file with note, continue
- **Diff parse errors**: Analyze full file instead
- **Convention parsing errors**: Use general best practices
- **Large PRs**: Batch 5-10 files, ask to continue between batches

## Tools

`read_file`, `changes`, `grep_search`, `usages`, `problems`

## References

- `templates/pr-review/severity-guidelines.md`
- `templates/pr-review/comment-examples.md`
- `templates/shared/state-schema.json`

````
