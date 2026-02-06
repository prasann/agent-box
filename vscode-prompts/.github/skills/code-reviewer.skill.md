# Code Reviewer Skill

Analyze code changes, detect issues, generate review comments with severity classification.

## Input/Output

```json
Input: {
  "files_changed": ["src/example.py"],
  "conventions": { "loaded_files": [...], "critical_rules": [...] },
  "focus_areas": ["testing", "types"],  // optional
  "state_file": ".copilot-tracking/pr-reviews/feature-1234.state.json"
}

Output: {
  "files_analyzed": 12,
  "comments_generated": 15,
  "pending_comments": [
    { "id": "...", "file": "...", "line": 42, "severity": "CRITICAL|DEFAULT",
      "category": "...", "comment": "...", "suggestion": "...", "reference": "..." }
  ],
  "summary": { "critical": 2, "default": 13 }
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

**C. Testing**: Multiple aspects to validate:
- **Coverage**: New functions without tests, missing edge/error cases
- **Usefulness**: Tests that verify meaningful behavior, not library code
- **Validity**: Proper assertions that actually check expected outcomes
- *Steps

1. **Prepare**: Load severity guidelines, comment examples, parse conventions
2. **Analyze Files**: For each changed file, a

**D. Documentation**: README out of sync, missing API docs
- Severity: DEFAULT
- Ref: code-and-documentation-hygiene.instructions.md

**E. Comments**: Temporal markers, narrative, contradictions, obvious comments
- Severity: DEFAULT → DEFAULT

**B. Type Safety**: Missing annotations, incorrect TypedDict, unnecessary cast() → DEFAULT
**G. Security**: SQL injection, hardcoded secrets, auth issues, exposed data
- Severity: CRITICAL
- Ref: Security best practices

**H. Performance**: N+1 queries, inefficient algorithms, missing pagination
- Severity: DEFACoverage gaps, usefulness (not testing libraries), valid assertions (not `assert True`), redundancy, broken assertions → DEFAULT

**D. Documentation**: README sync, missing API docs → DEFAULT

**E. Comments**: Temporal markers, narrative, contradictions → DEFAULT

**F. Architecture**: Immutability violations, SRP, complexity >50 lines → DEFAULT (CRITICAL if breaks functionality)

**G. Security**: SQL injection, secrets, auth issues, data exposure → CRITICAL

**H. Performance**: N+1 queries, inefficient algorithms → DEFAULT (CRITICAL if causes outage)

3. **Cross-File Checks**: Consistency (naming), completeness (tests, docs), breaking changes
4. **Generate Comments**: Create comment objects with severity (CRITICAL: security/data loss/constitution MUST/broken functionality; DEFAULT: everything else), category, suggestion, reference
5. **Focus Filtering**: If focus areas specified, detailed for focus, brief CRITICAL outside focus, skip DEFAULT outside focus
6. **Update State**: Write to `pendingComments`, update metadata, set `reviewStatus: "pending-approval"`
7. **Return**: Summary by severity, category, fileTICAL
- **Test files**: Comprehensive validation required:
  - **AAA Pattern**: Arrange, Act, Assert structure
  - **Isolation**: Tests don't depend on each other or external state
  - **Meaningful Assertions**: Verify actual behavior, not just that code runs
    - ❌ `assert result` (what does True mean?)
    - ❌ `assert mock.called` (testing the mock, not the logic)
    - ❌ `assert len(results) > 0` (too vague)
    - ✅ `assert result == expected_value`
    - ✅ `assert user.email == "test@example.com"`
  - **Avoid Testing Libraries**: Don't test framework/library behavior
    - ❌ Testing that requests.get() makes HTTP calls
    - ❌ Testing that SQLAlchemy saves to database
    - ✅ Testing that your code calls the library correctly with right params
    - ✅ Testing your business logic that uses the library
  - **Redundancy Check**: Multiple tests covering identical scenarios
    - Look for tests with same setup, same execution, different names
    - Tests that vary trivially (different variable names, same logic)
    - Integration tests that duplicate unit test coverage without adding value
  - **Broken Assertions**: Common anti-patterns
    - Empty assertions or assertions that can never fail
    - Assertions on mocked return values instead of real behavior
    - Assertions that test test setup rather than production code
    - Missing assertions (test runs code but checks nothing)
  - **Test Value**: Each test should answer "what would break if I removed this?"
    - If answer is "nothing", test is redundant or invalid
    - If answer is "the test", test is testing itself, not the code

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

& Categories

**Severity**: CRITICAL (security, data loss, MUST rules, broken functionality) vs DEFAULT (everything else)

**Categories**: imports, type-safety, testing (coverage, usefulness, validity, redundancy), documentation, comments, architecture, security, performance,Test Validation (Critical)

- **AAA Pattern**: Arrange, Act, Assert
- **Meaningful Assertions**: ✅ `assert result == expected` ❌ `assert result` / `assert mock.called` / `assert len(x) > 0`
- **Avoid Testing Libraries**: ✅ Test your logic ❌ Test that requests.get() works
- **Redundancy**: Flag tests with same setup/execution, trivial variations, duplicate coverage
- **Broken Assertions**: Empty assertions, assertions that never fail, testing mocks not logic, missing assertions
- **Test Value**: Ask "what breaks if I remove this?" If "nothing" or "the test", flag it

## Special Cases

- **Large files (>500 lines)**: Changed sections only
- **Legacy code**: Focus on new code
- **Generated code**: Flag only CRITICAL
- **Large PRs (>20 files)**: Batch 5-10 files

## Error Handling

File read errors: skip with note. Diff parse errors: analyze full file. Large PRs: batch processing.

**Tools**: `read_file`, `changes`, `grep_search`, `usages`, `problems`
**Refs**: `templates/pr-review/severity-guidelines.md`, `comment-examples.md`, `