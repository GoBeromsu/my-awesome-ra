# Optimized Playwright Patterns

Token-efficient Playwright patterns for visual verification.

## Login Sequence (Reusable)

Standard login flow for all Playwright verifications:

```
1. browser_navigate: http://localhost/login

2. browser_fill_form: [
     {name: "Email", ref: "e5", type: "textbox", value: "demo@example.com"},
     {name: "Password", ref: "e7", type: "textbox", value: "Demo@2024!Secure"}
   ]

3. browser_click: {element: "Login button", ref: "e26"}

4. browser_wait_for: {time: 2}
```

**Credentials**: `demo@example.com` / `Demo@2024!Secure`

## Project Navigation

After login, navigate to a project:

```
5. browser_click: {element: "Project link", ref: "eXX"}
   # Note: ref will vary, use snapshot to find exact ref

6. browser_wait_for: {text: "References"}
   # Wait for editor to load
```

## Token-Saving Strategies

### 1. Use Screenshot First

Screenshots are smaller than snapshots. Use when you just need visual confirmation:

```
browser_take_screenshot → ~500 tokens
browser_snapshot → ~2000-5000 tokens
```

Only use snapshot if you need element refs for interaction.

### 2. Element-Specific Snapshot

Instead of full page snapshot:

```
# Full page (expensive)
browser_snapshot

# Element only (cheaper)
browser_snapshot: {ref: "panel-element"}
```

### 3. Check Console Without Visual

Catches runtime errors without screenshot overhead:

```
browser_console_messages: {level: "error"}
```

Use this for:
- Runtime error detection
- React error boundaries
- Network failures

### 4. Batch Operations

Combine multiple checks in single session:

```
# BAD: Multiple sessions
browser_navigate → login → close
browser_navigate → login → check feature A → close
browser_navigate → login → check feature B → close

# GOOD: Single session
browser_navigate → login → check feature A → check feature B → close
```

## Common Verification Flows

### CSS Change Verification (~4000 tokens)

```
1. Login sequence (4 steps)
2. Navigate to feature (2 steps)
3. browser_take_screenshot → visual check (1 step)
4. browser_close (1 step)
```

Total: 8 tool calls

### Component Logic Verification (~6000 tokens)

```
1. Login sequence (4 steps)
2. Navigate to feature (2 steps)
3. browser_snapshot → find element refs (1 step)
4. browser_click → interact with component (1 step)
5. browser_snapshot → verify state change (1 step)
6. browser_close (1 step)
```

Total: 10 tool calls

### Full User Flow Verification (~10000 tokens)

```
1. Login sequence (4 steps)
2. Navigate to project (2 steps)
3. browser_snapshot → initial state (1 step)
4. browser_click → trigger action (1 step)
5. browser_wait_for → wait for response (1 step)
6. browser_snapshot → verify result (1 step)
7. browser_console_messages → check errors (1 step)
8. browser_take_screenshot → visual record (1 step)
9. browser_close (1 step)
```

Total: 13 tool calls

## Evidence Panel Specific Flows

### Verify Panel Opens

```
1. Login and navigate to project
2. browser_snapshot → find "References" tab
3. browser_click → open References panel
4. browser_wait_for: {text: "Search evidence"}
5. browser_snapshot → verify panel UI
```

### Verify Search Works

```
1. Login and navigate to project
2. Open References panel
3. browser_type → enter search query
4. browser_click → search button
5. browser_wait_for: {time: 2} → wait for results
6. browser_snapshot → verify results displayed
```

## Error Recovery

If element ref is stale or not found:

```
1. browser_snapshot → get fresh refs
2. Retry the action with new ref
```

If page doesn't load:

```
1. browser_wait_for: {time: 5} → longer wait
2. browser_snapshot → check current state
3. If still broken, browser_navigate → retry from start
```
