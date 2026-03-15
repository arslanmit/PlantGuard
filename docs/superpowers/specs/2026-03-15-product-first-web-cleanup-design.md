# Product-First Web Cleanup Design

## Summary

PlantGuard's current runtime UI mixes end-user workflows with developer-facing controls, mobile-shell scaffolding, runtime test tooling, and status panels. The product should instead present a standard responsive web interface focused on four user-facing areas:

- Image analysis
- Voice and audio
- Chat
- Settings

Settings should include model selection and user-facing performance preferences. The runtime app should no longer depend on the mobile shell or testing framework.

## Goals

- Remove developer-facing controls from the shipped app UI.
- Remove the mobile-shell runtime experience so the app behaves like a standard web application.
- Keep image, audio, chat, and settings functional.
- Keep model selection available, but only inside settings.
- Reduce runtime coupling to internal testing and diagnostic infrastructure.

## Non-Goals

- Reworking the training pipeline, model registry, or core adapter architecture.
- Removing backend validation or production training code.
- Broad repo-wide deletion based only on naming or assumptions.
- Redesigning the user flows beyond what is required to simplify the shell.

## Current State

The current runtime entrypoint in [mobile_spa_app.py](/Users/Development/PlantGuard/mobile_spa_app.py) contains:

- model status panels
- quick test actions
- a `Model Management` tab
- `App Info` and `Component Status` expanders
- runtime hooks into `mobile_testing_framework`
- mobile-shell runtime dependencies such as `MobileLayoutManager`, `MobileHeader`, `MobileInputRibbon`, and `MobileContentTabs`

This creates two problems:

1. The shipped product exposes operational and debugging affordances that are not part of the end-user experience.
2. The runtime app is coupled to mobile-only shell components and testing helpers that are not required for the retained product flows.

## Chosen Approach

Use a product-first cleanup centered on the runtime entrypoint.

- Rewrite the app shell in [mobile_spa_app.py](/Users/Development/PlantGuard/mobile_spa_app.py) as a standard Streamlit web app with four tabs: image, audio, chat, and settings.
- Move model selection controls into the settings tab.
- Remove runtime UI sections for model status, testing, component status, app info, and quick actions.
- Remove runtime use of the mobile testing framework.
- Remove runtime dependence on the mobile shell.
- Delete mobile-shell modules only if repository search confirms they are no longer imported or required after the runtime shell cleanup.

This keeps the cleanup focused on the shipped product while avoiding unsafe deletion of infrastructure that may still serve tests or non-UI workflows.

## UI Design

### Top-Level Structure

The runtime app should expose exactly four primary tabs:

1. Image Analysis
2. Voice & Audio
3. Chat
4. Settings

There should be no additional management, status, or testing areas in the user-facing shell.

### Image Analysis

- Keep image upload and image analysis.
- Keep result presentation for prediction name and confidence.
- Keep technical details only if they are directly useful to end users; otherwise prefer a concise results view.
- Remove duplicate status scaffolding surrounding the image flow.

### Voice & Audio

- Keep audio file upload and transcription.
- Keep optional text-response generation if already supported by the retained adapters.
- Remove placeholder copy that redirects users to another hidden or separate interface.

### Chat

- Keep a direct chat flow in the main app.
- Remove buttons that only acknowledge another tab or another interface.
- Prefer rendering the existing chat component directly if it still fits the simplified shell.

### Settings

- Keep model selection here.
- Keep user-facing performance preferences here.
- Do not expose testing controls, component diagnostics, or engineering-only runtime state here.

## Runtime Architecture

### Implementation Units

The cleanup should preserve clear boundaries between the runtime shell and the retained feature flows.

Recommended units:

- **App shell**: owns top-level page structure, tab layout, and adapter bootstrap.
- **Image flow renderer**: owns image upload, prediction execution, and result presentation.
- **Audio flow renderer**: owns audio upload, transcription, and optional text response display.
- **Chat flow renderer**: owns direct chat interaction in the kept web shell.
- **Settings renderer**: owns model selection and user-facing performance preferences.

Boundary rule:

- Feature renderers consume adapters and render UI.
- The app shell coordinates shared state and top-level layout.
- Testing and diagnostics do not sit on the runtime execution path.

### Runtime Entrypoint

The runtime entrypoint remains [mobile_spa_app.py](/Users/Development/PlantGuard/mobile_spa_app.py), but it should behave as a standard web app shell rather than a mobile-first SPA shell.

Responsibilities that remain:

- load core adapters
- render the four retained user flows
- handle user-level settings changes
- surface recoverable errors to the user

Responsibilities to remove from runtime:

- component-health dashboards
- test harness entrypoints
- mobile-shell status tracking
- mobile-shell fallback rendering
- developer-focused restart and refresh controls

### Core Adapters

Keep the existing adapter loading path unless cleanup requires minor reshaping to support the simplified shell.

- `VisionAdapter` remains the image-analysis runtime dependency.
- `AudioAdapter` remains the voice and audio runtime dependency.
- `TextAdapter` remains the chat and optional response-generation runtime dependency.

No changes are planned to adapter contracts unless required to support the simplified UI flow.

### Mobile-Shell Dependencies

The runtime should no longer depend on:

- `MobileLayoutManager`
- `MobileHeader`
- `MobileInputRibbon`
- `MobileContentTabs`

If these modules are not used elsewhere after the shell rewrite, they become deletion candidates. If they are still referenced by tests or non-runtime code that should remain, remove only the app runtime dependency and keep the files.

### Testing Framework Dependency

The runtime should no longer import or instantiate `mobile_testing_framework` or expose `get_ai_testing_framework()` driven controls. Testing infrastructure is not part of the shipped product shell.

If the testing framework is still used by dedicated tests or internal validation commands, keep it outside the runtime app path.

## File Scope

### Expected Primary Edits

- [mobile_spa_app.py](/Users/Development/PlantGuard/mobile_spa_app.py)
- affected UI tests that currently assert the removed mobile or developer-facing surfaces

### Possible Deletion Candidates

- mobile-shell UI modules used only by the removed shell
- runtime UI tests that only cover removed status or testing surfaces

### Explicitly Out Of Scope

- training infrastructure
- model registry implementation
- production training workflow
- core model validation logic unrelated to the runtime shell

## Error Handling

- If a retained adapter is unavailable, the corresponding user flow should show a clear user-facing error instead of a developer diagnostic panel.
- The app should continue rendering unaffected tabs when one adapter fails.
- Settings changes that fail should return a direct user-facing error and leave the previous working state intact.
- Shell initialization should not depend on mobile-only components, so failure modes tied to missing mobile shell state should disappear.

## Testing Strategy

### Runtime UI Tests

Update or replace UI tests so they validate:

- the app renders the four retained tabs
- developer/test/status surfaces are absent
- settings contains model selection
- the image, audio, and chat paths still render without mobile-shell components

### Deletion Safety

Before deleting any mobile-shell module:

- run repository search for imports and references
- confirm the file is not required by the retained runtime shell
- confirm test updates account for the removal

### Manual Verification

Manual browser verification should confirm:

- the app loads as a normal web application
- image analysis works
- audio upload and processing work
- chat is directly accessible
- settings exposes model selection and user-facing preferences
- no developer/test/status panels remain

## Risks

### Risk: Over-deleting shared UI modules

Some mobile-named modules may still be referenced by tests or helper code. Blind deletion would create avoidable regressions.

Mitigation:

- remove runtime references first
- delete files only after repository-wide usage confirmation

### Risk: Chat path is still wired as a placeholder

The current chat tab includes placeholder behavior instead of a direct chat flow.

Mitigation:

- explicitly convert the retained chat tab into a direct runtime flow during cleanup

### Risk: Tests are coupled to removed UI elements

Existing UI tests may assert the presence of mobile-shell or developer-facing surfaces.

Mitigation:

- rewrite tests around retained product behavior rather than patching old expectations

## Acceptance Criteria

The cleanup is complete when all of the following are true:

- the runtime app renders only image analysis, voice and audio, chat, and settings
- settings includes model selection
- `Model Management`, quick tests, app info, component status, and runtime AI test controls are gone from the shipped UI
- the runtime app no longer depends on the mobile shell
- runtime imports and execution no longer depend on the mobile testing framework
- any deleted module has been confirmed unused by the retained runtime path
- updated tests validate the simplified web shell
