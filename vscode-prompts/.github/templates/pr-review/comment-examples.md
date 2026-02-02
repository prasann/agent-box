# Professional Comment Examples

## Style Requirements

✅ **DO**: Direct, factual, evidence-based, concrete suggestions, references to conventions
❌ **DON'T**: Emojis (except structural headers), conversational filler, vague opinions, apologetic language

---

## Type Safety

```
**Issue**: Missing type annotation for return value

The function `process_data()` returns a dictionary but has no return type annotation. 
Based on the function logic, this should return `dict[str, Any] | None`.

**Suggestion**: 
def process_data() -> dict[str, Any] | None:
    ...

**Reference**: Type safety requirements in code-structure.instructions.md
```

```
**Issue**: Unnecessary cast() after Pydantic validation

Pydantic validation already guarantees type correctness. The cast() on line 42 is 
redundant and obscures the actual type safety.

**Suggestion**: Remove cast() and use the validated result directly:
validated_state = StateSchema(**raw_data)
# No cast needed - Pydantic ensures type correctness

**Reference**: TypedDict patterns in langgraph-patterns.instructions.md
```

---

## Import Hygiene

```
**Issue**: Unused imports detected

Lines 3-5 import `Dict`, `Optional`, and `asyncio` but none are used in this file.

**Action**: Remove unused imports or run `ruff check --select F401 --fix`

**Reference**: Import hygiene (zero-tolerance) in code-and-documentation-hygiene.instructions.md
```

---

## Missing Tests

```
**Issue**: Missing test coverage for new feature

The new `calculate_discount()` function has no corresponding tests. Per project TDD 
requirements, all new functions must have tests covering:
- Happy path
- Edge cases (zero/negative values)
- Error conditions

**Action**: Add tests/test_discount.py with test cases for all branches

**Reference**: TDD requirements in testing.instructions.md
```

---

## Documentation Sync

```
**Issue**: README.md out of sync with code structure

The folder restructure moved `src/core/langgraph/` → `src/langgraph/` but README.md 
still shows the old structure in the "Project Structure" section (lines 45-60).

**Action**: Update README.md project structure diagram to reflect new paths

**Reference**: Documentation synchronization requirement in code-and-documentation-hygiene.instructions.md
```

---

## Architecture

```
**Issue**: Consider extracting data transformation logic

The `process_request()` function handles HTTP parsing, business logic, and database 
operations (lines 100-250, 150 lines). This violates single responsibility principle.

**Suggestion**: Extract into separate functions:
- `parse_request_data()` - HTTP layer
- `validate_business_rules()` - Business logic
- `persist_to_db()` - Data layer

**Benefit**: Improved testability and maintainability

**Reference**: Code structure guidelines in code-structure.instructions.md
```

---

## Security (CRITICAL)

```
**CRITICAL**: SQL injection vulnerability

Line 87 constructs SQL query using string concatenation with user input:
query = f"SELECT * FROM users WHERE id = {user_id}"

**Risk**: Attackers can inject arbitrary SQL to access/modify/delete data

**Required Action**: Use parameterized queries:
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))

**Reference**: Security best practices for database operations
```

---

## Performance

```
**Issue**: N+1 query pattern detected

Lines 120-125 execute database query inside loop, resulting in O(n) queries:
for user in users:
    profile = db.get_profile(user.id)  # N queries

**Impact**: Performance degradation with large user lists (>100 users)

**Suggestion**: Use batch query:
user_ids = [u.id for u in users]
profiles = db.get_profiles_batch(user_ids)  # 1 query

**Benefit**: Reduces database round-trips from O(n) to O(1)
```

---

## Comment Policy

```
**Issue**: Remove temporal markers from code comments

Lines 45, 67, and 89 contain temporal references:
- "TODO: After Q4 migration..." (line 45)
- "Phase 2: Will implement..." (line 67)
- "Updated 2025-02-01" (line 89)

**Action**: Remove temporal markers or convert to behavior/intent descriptions

**Reference**: Comment policy in code-and-documentation-hygiene.instructions.md
```

---

## What Makes a Good Comment

1. **Specific**: References exact lines, files, functions
2. **Evidenced**: Shows code snippet or points to specific pattern
3. **Actionable**: Clear steps to resolve, ideally with code example
4. **Justified**: Explains WHY, not just WHAT
5. **Referenced**: Links to project conventions
6. **Scoped**: One issue per comment
7. **Professional**: Factual tone without filler
