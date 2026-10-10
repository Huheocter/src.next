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
- The old custom-homepage behavior is not ported in this commit. The safe implementation needs a dedicated preference/migration design, URL validation, policy precedence, incognito semantics, and unit tests. The `active_homepage` shortcut must not be added without tracing all readers/writers and validating URLs.

Decision: **do not merge the legacy HomepageManager.java**. Treat Chromium 155's implementation as the base and port only a narrowly defined, testable Kiwi behavior after its settings UI and preference contract are mapped.

## Port sequence

1. Inventory and classify each legacy change into user-facing Kiwi functionality, required build/resource wiring, Chromium compatibility adaptation, or obsolete/unwanted behavior.
2. Establish the Chromium 155 baseline with a clean Android build before applying Kiwi changes, so upstream build failures can be distinguished from port regressions.
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

The workflow `.github/workflows/port_kiwi_patch_chromium_155.yml` runs a read-only inventory and uploads `kiwi-port-inventory.md`. It does not apply code, compile Chromium, or create an APK. It is a planning/triage step only.
