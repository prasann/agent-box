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
5. **Output**: 
   - Create a file named `PR_DESCRIPTION.md` in the workspace root
   - Write ONLY the PR description content (no explanations, no code fences)
   - The file should be ready to copy-paste directly into GitHub

**Example format for PR_DESCRIPTION.md:**
```
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

**CRITICAL**: 
1. Create the file `PR_DESCRIPTION.md` at the workspace root
2. Write ONLY the markdown content (no code fences, no explanations)
3. After creating the file, simply confirm it was created

Generate the PR description now.