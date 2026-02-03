---
description: "Generate tasks.md from spec and plan - simple sequential checklist"
---

# Task Generator

Break spec and plan into actionable task checklist.

## Input

User says: "Generate tasks" or "Create tasks for <feature>"

**Requires**: 
- `specs/<name>/spec.md` (what to build)
- `specs/<name>/plan.md` (how to build it)

## Output

`specs/<name>/tasks.md` - Sequential task checklist

## Steps

### 1. Find Spec Directory

**If user specifies**: Use that feature name
**If current branch**: Extract from branch name (`feature/1234-auth` → `specs/auth/`)
**If ambiguous**: List available specs, ask which one

### 2. Load Context

Read:
- `spec.md` - Acceptance criteria, scope
- `plan.md` - File structure, phases
- `.specify/memory/constitution.md` or `.github/instructions/` (if exists) - Repo-specific principles

### 3. Generate Task List

Create sequential tasks following plan phases:

**Format**:
```markdown
# Tasks: <Feature Name>

## Acceptance Criteria
(From spec.md - copied for reference)
- [ ] Criterion 1
- [ ] Criterion 2

## Phase 1: <Name>
- [ ] T001: Create <file>
- [ ] T002: Implement <component> in <file>
**Validation**: <how to verify this phase>

## Phase 2: <Name>
- [ ] T003: Add <function> to <file>
- [ ] T004: Connect <A> to <B>
**Validation**: <how to verify this phase>

## Phase 3: Testing
- [ ] T005: Add tests for <component>
- [ ] T006: Verify acceptance criteria
**Validation**: All tests pass
```

**Task Format Rules**:
- Sequential IDs (T001, T002, ...)
- Specific action + file path
- One task = one file or one clear action
- Grouped by phases (from plan.md)
- Mark [P] for parallelizable tasks
- Each phase has validation checkpoint

### 4. Validate Completeness

Check:
- All files from plan.md have tasks
- All acceptance criteria covered
- Phases match plan phases exactly
- Each phase has clear validation checkpoint
- No ambiguous tasks ("Make it work" ❌)

### 5. Save and Report

Write `specs/<name>/tasks.md`

Show summary:
```markdown
✓ Generated specs/auth/tasks.md

**Phase 1 (Core): 4 tasks
- Phase 2 (Endpoints): 3 tasks
- Phase 3 (Testing): 3 tasks
- Phase 4 (Integration): 2 tasks: 3
- Docs: 1

**Parallel opportunities**: T003, T004 can run together

**Next**: Review tasks, then run implementer
```

## Task Generation Patterns

### Pattern: API Feature (from plan phases)
```markdown
## Phase 1: Core Models
- [ ] T001: Create User model in src/models/user.py
- [ ] T002: Add password hashing in src/auth/security.py
**Validation**: Import models, hash function works

## Phase 2: Service Layer
- [ ] T003: Create UserService in src/services/user_service.py
- [ ] T004: Add authentication logic
**Validation**: Service methods callable, basic test

## Phase 3: API Endpoints
- [ ] T005: Add POST /login route in src/routes/auth.py
- [ ] T006: Add POST /signup route in src/routes/auth.py
**Validation**: Endpoints return 200, manual curl test

## Phase 4: Testing
- [ ] T007: Add UserService tests
- [ ] T008: Add API integration tests
**Validation**: All tests pass, coverage >80%
```

### Pattern: Refactor (from plan phases)
```markdown
## Phase 1: Extract
- [ ] T001: Extract function X from module.py to utils.py
- [ ] T002: Update imports in module.py
**Validation**: Tests still pass

## Phase 2: Clean Up
- [ ] T003: Remove deprecated code from module.py
- [ ] T004: Update documentation
**Validation**: No linter warnings
```

## Inline Clarifications

User can edit tasks.md directly:
```markdown
- [ ] T003: Implement UserService in src/services/user_service.py
  <!-- CLARIFICATION: Include password hashing, no OAuth yet -->
```

Agent reads clarifications when implementing.

## Iteration

If user says:
- "Break down T003 into smaller tasks": Add T003a, T003b, T003c
- "Skip documentation tasks": Remove docs tasks
- "Add task for X": Insert task in logical position

Always update tasks.md, keep numbering sequential.

## Error Handling

- **No spec/plan found**: List available specs or ask to create spec first
- **Ambiguous plan**: Ask clarifying questions (bulk)
- **Too many tasks (>20)**: Suggest breaking into phases
- **Too few tasks (<3)**: Suggest this might be too simple

## Principles

Follow `.github/guiding-principles.md`:
1. **Simplicity**: One task = one clear action
2. **Surgical**: Specific paths, no vague tasks
3. **Sequential**: Order shows dependencies
4. **Verifiable**: Clear done condition per task

**If constitution.md exists**: Adapt tasks to repo patterns (e.g., test-first, immutability checks)

## Example Session

Plan has 3 phases: Core, Endpoints, Testing

✓ Generated specs/authentication/tasks.md

**Tasks**: 10 total
- Phase 1 (Core): 3 tasks - Models and security
- Phase 2 (Endpoints): 3 tasks - Login/signup routes
- Phase 3 (Testing): 4 tasks - Unit + integration tests

Each phase has validation checkpoint.

Review and run @implementer when ready.

User: "Break down T003 into smaller steps"

Agent:
✓ Updated tasks.md
- T003a: Add login method to UserService
- T003b: Add signup method to UserService
- T003c: Add token generation

Now 12 tasks total, Phase 2 updated
Agent:mirror plan phases exactly
- Each phase has validation checkpoint
✓ Updated tasks.md
- T003a: Create User model
- T003b: Add password hashing
- T003c: Add token generation

Now 10 tasks total.
```

## Remember

- Tasks follow plan phases
- One task = one file or one action
- Sequential by default, mark [P] for parallel
- Specific, not vague
- Support inline clarifications
