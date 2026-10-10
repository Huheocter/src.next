# Kiwi-to-Chromium 155 port audit

Status: **not build-ready**. This document records the first compatibility audit; it does not claim that Kiwi features have been ported or that an APK has been built.

## Baseline

- Chromium source version on the `chromium` branch: `155.0.8059.39`.
- Legacy Kiwi integration patch reviewed: `543d5c3b5be0dd6bd84b7f2fb05618093d0494f8` (`Apply Kiwi changes to Chromium version 105.0.5195.24`).
- The legacy patch changes 217 existing files. It is not a clean set of independent Kiwi-only files.
- A full rebase and a direct cherry-pick both conflict heavily against Chromium 155. The failed attempts were isolated to upgrade/test branches; the `kiwi` branch was left unchanged.

## Findings and risk

The patch spans Android UI/settings, browser core, extensions, Blink rendering, content, base APIs, resource strings and GN build configuration. This breadth means a successful textual merge would not demonstrate source/API compatibility.

The legacy patch also contains patterns that must not be blindly carried forward:
- unconditional `if (true)` / `|| true` build and feature gates;
- `#if 0` blocks around existing behavior;
- changes to extension permission/validation and resource-loading paths;
- changes in Blink request handling and dark-mode painting;
- API migrations from the Chromium 105-era `base::Value` interfaces;
- old Android tab-switcher and toolbar implementations that may no longer match Chromium 155 APIs.

These are review flags, not a claim that every listed change is necessarily exploitable or incorrect. Each must be understood in context before porting.

## Port sequence

1. **Inventory and classify** each legacy change into user-facing Kiwi functionality, required build/resource wiring, Chromium compatibility adaptation, or obsolete/unwanted behavior.
2. **Establish the Chromium 155 baseline** with a clean Android build before applying Kiwi changes, so upstream build failures can be distinguished from port regressions.
3. **Port extension support first** in small, reviewable commits: build targets/resources, extension lifecycle and protocol handling, permission parsing, then Android UI. Preserve Chromium 155 security checks unless a specific Kiwi requirement justifies a narrowly scoped, reviewed change.
4. **Port Android UX separately**: bottom toolbar, tab switcher, menu/settings, homepage, icons and strings. Update to current APIs instead of restoring old classes wholesale.
5. **Port Blink/night-mode changes last**, with targeted tests and a clear reason for each rendering-engine modification.
6. **Validate** with formatting/static checks, GN generation, Java/C++ compilation, tests where available, then produce and install an APK. Only mark complete after a successful build and artifact verification.

## Current acceptance criteria

- `kiwi` branch remains unchanged.
- No automatic rebase/cherry-pick of the 217-file patch onto Chromium 155.
- No APK is advertised until a successful workflow artifact is available and verified.
- The port remains incomplete until compilation and install/runtime checks pass.


## Latest automation update

The previous safe-trial workflow attempted a direct cherry-pick and failed as expected because the patch conflicts with Chromium 155. It has been replaced with a read-only inventory workflow; it no longer attempts a cherry-pick or pushes code.

- Inventory script: `tools/kiwi_port_inventory.py`
- Workflow: `.github/workflows/port_kiwi_patch_chromium_155.yml`
- Workflow output: a categorized `kiwi-port-inventory.md` artifact listing every changed path from the legacy patch.
- To run it: open the repository's **Actions** tab, select **Audit legacy Kiwi patch for Chromium 155**, choose **Run workflow**, and select branch `upgrade/kiwi-chromium-155-port`.

This inventory is a planning/triage step only. It does not port features, compile Chromium, or create an APK. The next implementation step is to select one small user-facing feature, port it against current APIs, and validate it independently before expanding scope.
