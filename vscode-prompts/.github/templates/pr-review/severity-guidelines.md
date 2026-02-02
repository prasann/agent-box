# Review Severity Guidelines

## CRITICAL (Must fix before merge)

**Blocking issues only**: Security vulnerabilities, data loss risks, constitution MUST violations, broken functionality, application crashes.

**Examples**: SQL injection, XSS, exposed credentials, operations that corrupt/lose data, API changes without migration, crashes in core paths.

**Template**:
```
**CRITICAL**: <issue>
<explanation-with-evidence>
**Risk**: <specific-risk>
**Required Action**: <what-must-be-done>
**Reference**: <guideline>
```

---

## DEFAULT (All other feedback)

**Everything else**: Missing tests, type safety, documentation gaps, import hygiene, incorrect patterns, architecture violations, code quality, performance, error handling, style, refactoring opportunities, suggestions.

**Template**:
```
**Issue**: <brief-description>
<explanation>
**Suggestion**: <concrete-fix-with-example>
**Reference**: <guideline>
```

---

## Decision Tree

```
Security | Data loss | Constitution MUST | Broken functionality?
├─ Yes → CRITICAL
└─ No → DEFAULT
```

**When in doubt, use DEFAULT.** Reserve CRITICAL only for immediate risks or blocking issues.
