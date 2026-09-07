# Try the unified manifest, tidy revision history and compatibility diagnostics

This test combines Jellyfin-Enhanced PRs [#799](https://github.com/n00bcodr/Jellyfin-Enhanced/pull/799) and [#800](https://github.com/n00bcodr/Jellyfin-Enhanced/pull/800), and jellyfin-plugins [#2](https://github.com/n00bcodr/jellyfin-plugins/pull/2). Nothing needs merging first.

Use this repository URL in a disposable Jellyfin 12 or 10.11 server:

```text
https://raw.githubusercontent.com/4eh5xitv6787h645ebv/jellyfin-plugins/test/pr799-unified-manifest/tests/pr799/manifest.json
```

The catalog is the proposed unified manifest. Only the two Enhanced `12.5.0.0` ZIP URLs/checksums and their changelog prefixes differ: they point to the updated #799 test builds, including revision deduplication and compatibility diagnostics, with the red mismatch banner removed. The ZIP URLs are pinned to a commit. Older revisions retain the original release assets. If you previously installed this test version, uninstall it, restart, reinstall from the same URL, restart and hard-refresh the browser to replace the earlier `12.5.0.0` test DLL and cached scripts.

## Quick test on Jellyfin 12

1. Use a fresh test server. Under **Dashboard → Plugins → Manage Repositories**, add the URL above. If reusing a test server, disable other repositories providing Jellyfin Enhanced first: a stale repository can win the same-version tie. Remove any existing Enhanced installation and restart before testing this build.
2. Refresh the Plugins page. **Jellyfin Enhanced appears as one card**, including while it is not installed.
3. Before Enhanced is installed, open that card and expand **Revision History**. There are two `12.5.0.0` entries. One targets 12 and the other 10.11; the client-side deduplication cannot run until Enhanced is active.
4. Expand the **second `12.5.0.0` entry**, labelled as the jf10/10.11 test build. Click its **Install** button and confirm, then restart Jellyfin.
5. Hard-refresh the browser. Revision History now has **one visible entry per version**. Run the checker below: expected `builtFor: jf12`, `hostTarget: jf12`, `mismatch: false`, then **PASS**. The API still contains both rows; only the displayed list is deduplicated. The configuration page has no wrong-build banner.
6. To compare the first entry, uninstall Enhanced, restart, then repeat with the **first `12.5.0.0` entry**. It also loads `jf12`. Default Install should do the same.

```sh
python3 verify.py --server http://localhost:8096 --username admin
```

Download `verify.py` from this directory first. It uses only Python's standard library and prompts for the password without printing or saving it. It logs in as the administrator and reads the catalog and guard endpoint; it does not install or change plugins.

The reason both clicks resolve identically: the web client sends the **plugin version string and repository URL**, not `targetAbi` or the selected ZIP. Within this manifest both rows share those request values. Jellyfin resolves to the first compatible row, and jf12 is ordered first.

## Check other plugins

While Enhanced is active, open JavaScript Injector's Revision History: repeated versions should appear once there too. For another independent example, add Ani-Sync's official repository (`https://raw.githubusercontent.com/vosmiic/jellyfin-ani-sync/master/manifest.json`) and inspect its history; the repeated `2.1.0.0` entries become one visible entry. Neither other plugin needs installing. Navigate between plugin pages and expand revisions to confirm that their original install buttons still work. The feature preserves the first entry in the catalog's order and hides later duplicates without changing server responses or handlers.

## Jellyfin 10.11 comparison

Add the **same URL** to a separate Jellyfin 10.11 test server. Only the 10.11 row survives the ABI filter. Install and restart, then run the checker against that server. Expected: `builtFor: jf10`, `hostTarget: jf10`, `mismatch: false`, **PASS**.

## Existing manifest URLs

The `10.11/manifest.json`, `12/manifest.json`, `10.10/manifest.json`, and `legacy/manifest.json` files inside this test directory are byte-identical to `manifest.json`. They model the old URLs being retained as mirrors. For example, replacing the configured URL with:

```text
https://raw.githubusercontent.com/4eh5xitv6787h645ebv/jellyfin-plugins/test/pr799-unified-manifest/tests/pr799/10.11/manifest.json
```

still selects jf12 on Jellyfin 12. These are test URLs; the actual existing n00bcodr URLs do not change until the PRs are merged/published.

## Optional diagnostic test

On the disposable Jellyfin 12 server, first install the correct test build above. Stop Jellyfin, replace only its installed `Jellyfin.Plugin.JellyfinEnhanced.dll` with the DLL from `assets/Jellyfin.Plugin.JellyfinEnhanced_10.11.0.zip`, and start it again. The matching ZIP is linked in this directory; this intentionally bypasses catalog selection.

The logs contain `BUILD/HOST MISMATCH`. The red configuration-page banner has been removed; the endpoint and logging remain available for diagnostics.

```sh
python3 verify.py --server http://localhost:8096 --username admin --expect-mismatch
```

Expected: `builtFor: jf10`, `hostTarget: jf12`, `mismatch: true`, **PASS**. Restore the jf12 DLL while Jellyfin is stopped after testing. #799 warns; it does not prevent loading.

## What this does not guarantee

Historical releases that never had a Jellyfin 12 build remain installable. For example, choosing `11.12.0.0` installs its only build, jf10, even on Jellyfin 12. That is separate from selecting either row of a paired version. Old published DLLs also do not contain the new guard. This manifest preserves those historical entries as the PR proposes.

The unmodified guard's remediation text links to the intended upstream canonical URL. That URL returned 404 when this test was prepared on 7 September 2026; use the fork test URL until upstream publishes it.

## Source and prior validation

The source and asset hashes are recorded in [`assets/provenance.json`](assets/provenance.json). The plugin source is available at the pinned guard commit linked there, under GPL-3.0 (license included). It was built with .NET SDK 10.0.108:

```sh
dotnet build Jellyfin.Plugin.JellyfinEnhanced/JellyfinEnhanced.csproj -c Release -p:JellyfinTarget=jf12 -o out/jf12
dotnet build Jellyfin.Plugin.JellyfinEnhanced/JellyfinEnhanced.csproj -c Release -p:JellyfinTarget=jf10 -o out/jf10
```

Both builds passed with zero warnings/errors. The updated plugin was tested on Jellyfin 12 RC6 and 10.11.11 with the standalone preview removed: Enhanced, Ani-Sync and JavaScript Injector each show one entry per version; navigation, repeated initialization without subscriber growth, preserved intercepted install parameters, teardown, and banner removal pass without browser page errors. The matching diagnostics endpoint reports the correct build on both servers. Browser regression scripts are kept local rather than included in the PR.

Earlier tests on the original manifest verified default installation, identical requests and DLL hashes from both `12.4.1.0` revision buttons, and the older-version exception. The current upstream source hash check in the original manifest PR has drifted for two Jellyfin master files; those pins were not changed by this test bundle. Automatic updates and future Jellyfin releases are not covered by these results.
