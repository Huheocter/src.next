# Kiwi-to-Chromium 155 port audit

Status: **not build-ready**. This document records the compatibility review; it does not claim that Kiwi features have been ported or that an APK has been built.

## Baseline

- Chromium source version on the `chromium` branch: `155.0.8059.39`.
- Legacy Kiwi integration patch reviewed: `543d5c3b5be0dd6bd84b7f2fb05618093d0494f8` (`Apply Kiwi changes to Chromium version 105.0.5195.24`).
- The legacy patch changes 217 existing files. It is not a clean set of independent Kiwi-only files.
- A full rebase and a direct cherry-pick both conflict heavily against Chromium 155. The failed attempts were isolated to upgrade/test branches; the `kiwi` branch was left unchanged.

## Findings and risk

The patch spans Android UI/settings, browser core, extensions, Blink rendering, content, base APIs, resource strings and GN build configuration. A successful textual merge would not demonstrate source/API compatibility.

The legacy patch also contains patterns that must not be blindly carried forward:
- unconditional `if (true)` / `|| true` build and feature gates;
- `#if 0` blocks around existing behavior;
- changes to extension permission/validation and resource-loading paths;
- changes in Blink request handling and dark-mode painting;
- API migrations from Chromium 105-era `base::Value` interfaces;
- old Android tab-switcher and toolbar implementations that may no longer match Chromium 155 APIs.

These are review flags, not a claim that every listed change is necessarily exploitable or incorrect. Each must be understood in context before porting.

## First feature review: homepage behavior

Files reviewed:
- Legacy Kiwi: `chrome/android/java/src/org/chromium/chrome/browser/homepage/HomepageManager.java`
- Chromium 155: same path on the `chromium` branch.

Findings:
- Kiwi's legacy file has unconditional branches such as `if (true) return "chrome://newtab";` and an unconditional preference read from the app preference key `active_homepage`. Those override the normal partner/custom-homepage selection logic.
- Kiwi also adds `shouldCloseAppWithZeroTabs()`, reading `close_browser_after_last_tab`; this is a separate behavior and must be traced to the zero-tab lifecycle before it can be ported.
- Chromium 155 has materially changed this class: it uses `GURL`, native homepage policy synchronization, `ChromeSharedPreferences`, NTP URL resolvers, incognito-aware homepage resolution, and navigation APIs. Copying the old class or its methods wholesale would break current behavior and may not compile.
- The old custom-homepage behavior is not ported yet. A safe implementation needs a dedicated preference/migration design, URL validation, policy precedence, incognito semantics, and unit tests. The `active_homepage` shortcut must not be added without tracing all readers/writers and validating URLs.

Decision: **do not merge the legacy HomepageManager.java**. Treat Chromium 155's implementation as the base and port only a narrowly defined, testable Kiwi behavior after its settings UI and preference contract are mapped.

## Third feature review: close app after last tab

A follow-up source comparison confirmed that Chromium 155 already has a zero-tab close policy, but it is **not equivalent** to Kiwi's legacy preference:

- Kiwi 105 adds static `HomepageManager.shouldCloseAppWithZeroTabs()`, which reads the app preference `close_browser_after_last_tab` and defaults to `false`.
- Chromium 155's `HomepageManager.shouldCloseAppWithZeroTabs()` is an instance method. It returns true when the homepage is enabled and the resolved homepage is not the NTP; it does not read Kiwi's `close_browser_after_last_tab` key.
- Chromium 155 calls this method from `ChromeTabbedActivity` when the total tab count reaches zero. That caller has also evolved to account for pending closure and multi-window window-removal behavior.

Decision: **do not replace Chromium 155's policy with the old static method**. A faithful Kiwi port needs to add/migrate the preference, expose it through the current settings UI, define its precedence relative to homepage/NTP behavior, and add tests for normal/incognito tabs, pending closure, and multi-window. Merely changing the method would silently change the zero-tab lifecycle and could cause unexpected app exits.

Relevant source paths:
- Legacy: `chrome/android/java/src/org/chromium/chrome/browser/homepage/HomepageManager.java` and `chrome/android/java/src/org/chromium/chrome/browser/ChromeTabbedActivity.java` on `kiwi`.
- Current: same paths on `chromium`.

This is a verified compatibility difference, not an implemented feature.

## Second feature review: classic tab switcher and bottom toolbar

The legacy patch modifies tab-list and tab-grid binding/layout behavior, reads `active_tabswitcher` (`classic` / `grid`), and changes tab-group behavior when `enable_bottom_toolbar` is set.

Risks and required work:
- The old patch assumes Chromium 105-era tab-list coordinator and layout behavior. Restoring those snippets without checking Chromium 155's current classes, model properties, and lifecycle could create compile failures or subtle tab-selection/scroll regressions.
- The tab-switcher preference is read in multiple UI layers, so porting only one conditional would leave inconsistent behavior between the grid dialog, list, and selection editor.
- The bottom-toolbar flag affects tab-group state and cannot be treated as a purely visual layout change; its interactions with tab-strip visibility, multi-window mode, orientation, and tab creation must be tested.
- These changes are not applied to the Chromium 155 branch yet. The next code change should be a small, coherent vertical slice (preference + current UI integration + tests), not a partial copy of the old layout snippets.

## Fourth feature review: tab switcher compatibility details

A closer review of the legacy `TabListCoordinator` / `TabListMediator` changes identifies concrete reasons not to transplant those snippets directly:

- The legacy code spreads `active_tabswitcher` preference reads across the coordinator, mediator, factory, and binders instead of resolving one validated mode at a single boundary. Partial porting could make the main switcher, group dialog, selection editor, and scroll behavior disagree.
- Some legacy comparisons use Java reference identity (`componentName != "..."`) instead of string value equality. This can behave incorrectly when the same component name is represented by a different String object.
- A legacy read uses `getString("active_tabswitcher", "classic")` in a span-count condition. With no stored preference, the default itself selects classic layout, unlike the other reads whose default is `default`. That can unintentionally force one-column layout for users who never selected classic mode.
- The classic layout uses `Resources.getSystem().getDisplayMetrics().density` for offsets instead of the active view/context's display metrics, and injects negative item-decoration spacing. This needs layout tests across display density, orientation, and multi-window rather than a textual port.
- Old code also contains commented-out alternate mode/span logic. Those comments are not an implementation contract and should not be revived as code without checking Chromium 155's current architecture.

Decision: keep Chromium 155's current tab management implementation as the base. If classic mode is ported, first introduce a single preference parser with an explicit default and enum-like validated values; then wire that mode into the current factory/coordinator and add tests for default/grid/list/classic, low-end-device behavior, orientation, dialogs, and scroll restoration. Do not yet modify production tab UI code until those test seams are identified.

## Build feasibility gate

The official Chromium Android build guide lists a 64-bit Linux machine, at least 8 GB RAM (more than 16 GB recommended), and at least 100 GB free disk as system requirements. A normal Android browser build uses GN and then `autoninja -C out/Default chrome_public_apk`. Therefore a green inventory workflow is not evidence of a build, and a standard small hosted runner should not be assumed capable of producing the full APK without a verified build environment.

Reference: https://chromium.googlesource.com/chromium/src/+/main/docs/android_build_instructions.md

## Port sequence

1. Inventory and classify each legacy change into user-facing Kiwi functionality, required build/resource wiring, Chromium compatibility adaptation, or obsolete/unwanted behavior.
2. Establish the Chromium 155 baseline with a clean Android build in a suitably provisioned Linux build environment before applying Kiwi changes, so upstream build failures can be distinguished from port regressions.
3. Port extension support in small, reviewable commits: build targets/resources, extension lifecycle and protocol handling, permission parsing, then Android UI. Preserve Chromium 155 security checks unless a specific Kiwi requirement justifies a narrowly scoped, reviewed change.
4. Port Android UX separately: bottom toolbar, tab switcher, menu/settings, homepage, icons and strings. Update to current APIs instead of restoring old classes wholesale.
5. Port Blink/night-mode changes last, with targeted tests and a clear reason for each rendering-engine modification.
6. Validate with formatting/static checks, GN generation, Java/C++ compilation, tests where available, then produce and install an APK. Only mark complete after a successful build and artifact verification.

## Current acceptance criteria

- The `kiwi` branch remains unchanged.
- No automatic rebase/cherry-pick of the 217-file patch onto Chromium 155.
- No APK is advertised until a successful workflow artifact is available and verified.
- The port remains incomplete until compilation and install/runtime checks pass.

## Automation status

The workflow `.github/workflows/port_kiwi_patch_chromium_155.yml` runs unit tests for both audit tools, generates the categorized inventory, scans added legacy-patch lines for review flags, and uploads `kiwi-port-inventory.md` plus `kiwi-patch-risk-scan.md`. The latest verified run for commit `8cf846fb32cda816c36e53e73cb8b4b0153170c1` completed successfully: [run #7](https://github.com/Huheocter/src.next/actions/runs/38036257595). This verifies the audit tooling only; it does not apply Kiwi code, compile Chromium, or create an APK. It remains a planning/triage step.
