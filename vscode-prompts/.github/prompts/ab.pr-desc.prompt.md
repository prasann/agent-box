Review the branch changes and generate a PR description in GitHub-ready Markdown format.

**Requirements:**
1. **Format**: Use bullet points grouped by logical category (e.g., Bug Fixes, Features, Refactoring, Data Model Changes)
2. **Content**: Focus on meaningful changes only—exclude:
   - Test updates/additions
   - Documentation changes
   - Code formatting/linting fixes
   - Comment updates
   - Import cleanup
3. **Structure**: Use H2 headers for categories, nested bullets for related changes
4. **Clarity**: State what changed and the impact (why it matters)
5. **Output**: Plain Markdown ready to paste into GitHub PR description

**Example output:**
```markdown
## Bug Fixes
- Fixed shipment filtering to handle null CUT/WSLR dates correctly
- Resolved state validation error in async workflow execution

## Refactoring
- Extracted Pydantic models from workflow logic
  - Moved validation schemas to dedicated module
  - Added type-safe state transitions
- Simplified error handling in data fetch operations

## Data Model Changes
- Added optional `processed_at` timestamp to OOSState
- Extended shipment schema to include carrier metadata
```

Generate the PR description now.