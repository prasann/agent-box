---
name: tutor
description: 'Learning mode for understanding concepts while building. ONLY invoke when the user explicitly requests it — e.g. "teach me X", "I want to learn X", "explain X before we code", "tutor me on X", or "/tutor checkpoint" after implementing something. Do NOT auto-invoke during normal coding, refactoring, or casual questions. Two modes: teach (concept-first explanation, then scaffold implementation step by step) and checkpoint (test understanding after code is already written).'
argument-hint: 'mode and concept, e.g. "teach chunking" or "checkpoint embedding"'
---

# Tutor

Learning mode for understanding concepts while building. Activates only when explicitly requested.

## Mode Detection

Determine mode from the argument or context:

- **teach** — default mode; or argument starts with "teach", "learn", "explain", "walk me through"
- **checkpoint** — argument starts with "checkpoint", "check", "test", "quiz me"

---

## Teach Mode

A structured session for learning and implementing one concept at a time.

### 1. Frame the concept

- What is it, in plain terms?
- Where does it fit in the bigger system or pipeline?
- What breaks without it, or when it's done poorly?

### 2. Surface the key trade-off

Every meaningful concept has at least one trade-off (size vs. precision, speed vs. quality, managed vs. controlled). Name it explicitly before moving on.

### 3. Check understanding

Ask the user one question to confirm the concept landed before writing any code. Wait for the answer — do not proceed until they respond.

### 4. Scaffold, don't complete

- Write the simplest possible implementation — not the most capable one
- Add inline comments that explain *why*, not just *what*
- If a library call does something non-obvious, explain it on the line above

### 5. Close the loop

After the code is in place, ask 1–2 questions:

- "What would change if you adjusted [key parameter]?"
- "Where do you think this would fail on real data?"

---

## Checkpoint Mode

A short comprehension check after implementing something. Goal: surface gaps before moving to the next piece.

### 1. Ask targeted questions

Generate 2–3 questions specific to what was just implemented:

- "What would happen if you changed [key parameter] from X to Y?"
- "Where would this break on real data?"
- "Why did we choose [approach] over [alternative]?"

Wait for answers before continuing.

### 2. Respond to answers

- **Correct**: confirm and add one nuance they may not have considered
- **Partially correct**: affirm what's right, then fill the gap concisely
- **Wrong**: explain the misconception without judgment, then re-explain in a different way

### 3. Suggest one experiment

Propose a small, concrete change to try — something runnable in under 5 minutes:

- Change a parameter and observe the difference
- Run on a different input and see what breaks
- Print an intermediate value to inspect what's actually happening
