# Product-First Web Cleanup Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the shipped PlantGuard runtime UI into a standard web app that exposes only image analysis, voice and audio, chat, and settings, while removing mobile-shell and developer-facing runtime clutter.

**Architecture:** Keep the work centered on [mobile_spa_app.py](/Users/Development/PlantGuard/mobile_spa_app.py). First lock in the desired behavior with failing UI tests, then simplify the runtime shell, then prune runtime-only mobile dependencies and obsolete tests only after reference checks confirm they are unused by the kept web shell.

**Tech Stack:** Python, Streamlit, pytest, Playwright, ripgrep

---

## Chunk 1: Lock In The Simplified Web Shell

### Task 1: Replace mobile-shell expectations with product-shell expectations

**Files:**
- Modify: `/Users/Development/PlantGuard/tests/test_ui.py`
- Modify: `/Users/Development/PlantGuard/tests/test_mobile_ui_regressions.py`
- Reference: `/Users/Development/PlantGuard/mobile_spa_app.py`

- [ ] **Step 1: Write the failing tests for the kept shell**

```python
def test_app_exposes_only_product_tabs() -> None:
    labels = get_runtime_tab_labels()
    assert labels == ["Image Analysis", "Voice & Audio", "Chat", "Settings"]


def test_removed_developer_surfaces_are_absent() -> None:
    text = render_main_shell_text()
    assert "Model Management" not in text
    assert "Component Status" not in text
    assert "Quick Test" not in text
    assert "Mobile Components" not in text
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:
```bash
.venv/bin/python -m pytest tests/test_ui.py tests/test_mobile_ui_regressions.py -q
```

Expected:
- at least one failure proving the old mobile/developer shell is still present

- [ ] **Step 3: Remove obsolete mobile-only test expectations**

Delete or rewrite assertions that require:
- `MobileLayoutManager`
- `MobileHeader`
- `MobileInputRibbon`
- `MobileContentTabs`
- mobile-only status/readiness displays

- [ ] **Step 4: Re-run the targeted tests and confirm they still fail only on missing implementation**

Run:
```bash
.venv/bin/python -m pytest tests/test_ui.py tests/test_mobile_ui_regressions.py -q
```

Expected:
- failures now reflect the intended runtime cleanup, not stale test assumptions

- [ ] **Step 5: Commit the red test baseline**

```bash
git add tests/test_ui.py tests/test_mobile_ui_regressions.py
git commit -m "test: lock in simplified web shell"
```

## Chunk 2: Rewrite The Runtime Shell

### Task 2: Simplify the Streamlit entrypoint into a standard web app

**Files:**
- Modify: `/Users/Development/PlantGuard/mobile_spa_app.py`
- Reference: `/Users/Development/PlantGuard/docs/superpowers/specs/2026-03-15-product-first-web-cleanup-design.md`
- Test: `/Users/Development/PlantGuard/tests/test_ui.py`

- [ ] **Step 1: Keep the failing tests visible while editing**

Run:
```bash
.venv/bin/python -m pytest tests/test_ui.py -q
```

- [ ] **Step 2: Remove mobile-shell runtime imports and fields that no longer belong on the app instance**

Delete runtime dependence on:
- `MobileLayoutManager`
- `MobileHeader`
- `MobileInputRibbon`
- `MobileContentTabs`
- `mobile_testing_framework`

- [ ] **Step 3: Collapse the main shell into four direct user tabs**

Implement a runtime layout shaped like:

```python
tab_image, tab_audio, tab_chat, tab_settings = st.tabs(
    ["Image Analysis", "Voice & Audio", "Chat", "Settings"]
)
```

Inside those tabs:
- keep direct image upload and prediction
- keep direct audio upload and transcription
- keep direct chat rendering instead of a placeholder button
- move model selectors and performance mode into settings

- [ ] **Step 4: Remove developer-facing UI sections**

Delete:
- model status dashboard
- quick actions
- `Model Management`
- `App Info`
- `Component Status`
- mobile component rendering block
- emergency copy that exists only to restart or inspect the mobile shell

- [ ] **Step 5: Run the targeted tests and make them pass**

Run:
```bash
.venv/bin/python -m pytest tests/test_ui.py tests/test_mobile_ui_regressions.py -q
```

Expected:
- targeted UI tests pass against the simplified shell

- [ ] **Step 6: Commit the shell rewrite**

```bash
git add mobile_spa_app.py tests/test_ui.py tests/test_mobile_ui_regressions.py
git commit -m "feat: simplify app to product-first web shell"
```

## Chunk 3: Prune Runtime-Only Mobile Dependencies Safely

### Task 3: Remove dead runtime dependencies and keep only what the app still uses

**Files:**
- Modify or Delete: `/Users/Development/PlantGuard/src/ui/components/mobile_layout_manager.py`
- Modify or Delete: `/Users/Development/PlantGuard/src/ui/components/mobile_header.py`
- Modify or Delete: `/Users/Development/PlantGuard/src/ui/components/mobile_input_ribbon.py`
- Modify or Delete: `/Users/Development/PlantGuard/src/ui/components/mobile_content_tabs.py`
- Modify: `/Users/Development/PlantGuard/tests/test_mobile_component_infrastructure.py`
- Modify: `/Users/Development/PlantGuard/tests/simple_test.py`
- Reference: repository-wide search output

- [ ] **Step 1: Search for remaining runtime and test references**

Run:
```bash
rg -n "MobileLayoutManager|MobileHeader|MobileInputRibbon|MobileContentTabs|mobile_testing_framework|get_ai_testing_framework" .
```

Expected:
- a concrete list of remaining dependencies to keep, rewrite, or delete

- [ ] **Step 2: Delete only files confirmed unused by the kept runtime shell**

Use this rule:
- if a module is unused after the shell rewrite, delete it
- if tests still need it for unrelated infrastructure, keep it but remove app runtime coupling

- [ ] **Step 3: Rewrite or delete obsolete tests**

Remove tests whose only purpose was to validate:
- mobile-shell readiness/status behavior
- mobile testing framework integration through the shipped app shell

- [ ] **Step 4: Run focused cleanup verification**

Run:
```bash
.venv/bin/python -m pytest tests/test_ui.py tests/test_mobile_ui_regressions.py tests/simple_test.py -q
```

Expected:
- the retained UI tests pass
- deleted mobile-shell expectations are no longer referenced

- [ ] **Step 5: Commit the pruning work**

```bash
git add mobile_spa_app.py src/ui/components tests/test_ui.py tests/test_mobile_ui_regressions.py tests/simple_test.py
git commit -m "refactor: prune unused mobile runtime dependencies"
```

## Chunk 4: Full Verification And Manual Smoke Test

### Task 4: Prove the simplified web shell works end to end

**Files:**
- Modify if needed: `/Users/Development/PlantGuard/mobile_spa_app.py`
- Reference: `/Users/Development/PlantGuard/tests/test_make_mobile_functionality.py`

- [ ] **Step 1: Run the focused automated verification**

Run:
```bash
.venv/bin/python -m pytest tests/test_ui.py tests/test_mobile_ui_regressions.py tests/test_make_mobile_functionality.py -q
```

Expected:
- all focused verification tests pass

- [ ] **Step 2: Start the app**

Run:
```bash
make mobile
```

- [ ] **Step 3: Verify HTTP response**

Run:
```bash
curl -I http://localhost:8502
```

Expected:
- `HTTP/1.1 200 OK`

- [ ] **Step 4: Smoke-test the retained UI in the browser**

Check:
- only four tabs are visible
- no model management, quick test, app info, component status, or mobile components sections remain
- settings includes model selection

- [ ] **Step 5: Commit the final cleanup adjustments**

```bash
git add mobile_spa_app.py tests/test_ui.py tests/test_mobile_ui_regressions.py tests/test_make_mobile_functionality.py
git commit -m "test: verify product-first web cleanup"
```
