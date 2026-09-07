# Try the unified manifest and host compatibility guard

This test combines Jellyfin-Enhanced PRs [#799](https://github.com/n00bcodr/Jellyfin-Enhanced/pull/799) and [#800](https://github.com/n00bcodr/Jellyfin-Enhanced/pull/800), and jellyfin-plugins [#2](https://github.com/n00bcodr/jellyfin-plugins/pull/2). Nothing needs merging first.

Use this repository URL in a disposable Jellyfin 12 or 10.11 server:

```text
https://raw.githubusercontent.com/4eh5xitv6787h645ebv/jellyfin-plugins/test/pr799-unified-manifest/tests/pr799/manifest.json
```

The catalog is the proposed unified manifest. Only the two Enhanced `12.5.0.0` ZIP URLs/checksums and their changelog prefixes differ: they point to test builds that include the #799 guard. The ZIP URLs are pinned to a commit. This avoids pretending that the already published releases contain the new guard. Older revisions retain the original release assets.

## Quick test on Jellyfin 12

1. Use a fresh test server. Under **Dashboard → Plugins → Manage Repositories**, add the URL above. If reusing a test server, disable other repositories providing Jellyfin Enhanced first: a stale repository can win the same-version tie. Remove any existing Enhanced installation and restart before testing this build.
2. Refresh the Plugins page. **Jellyfin Enhanced appears as one card**, including while it is not installed.
3. Open that card and expand **Revision History**. There are two `12.5.0.0` entries. One targets 12 and the other 10.11.
4. Expand the **second `12.5.0.0` entry**, labelled as the jf10/10.11 test build. Click its **Install** button and confirm, then restart Jellyfin.
5. Run the checker below. Expected: `builtFor: jf12`, `hostTarget: jf12`, `mismatch: false`, then **PASS**. The configuration page should have no wrong-build warning.
6. To compare the first entry, uninstall Enhanced, restart, then repeat with the **first `12.5.0.0` entry**. It also loads `jf12`. Default Install should do the same.

```sh
python3 verify.py --server http://localhost:8096 --username admin
```

Download `verify.py` from this directory first. It uses only Python's standard library and prompts for the password without printing or saving it. It logs in as the administrator and reads the catalog and guard endpoint; it does not install or change plugins.

The reason both clicks resolve identically: the web client sends the **plugin version string and repository URL**, not `targetAbi` or the selected ZIP. Within this manifest both rows share those request values. Jellyfin resolves to the first compatible row, and jf12 is ordered first.

## Jellyfin 10.11 comparison

Add the **same URL** to a separate Jellyfin 10.11 test server. Only the 10.11 row survives the ABI filter. Install and restart, then run the checker against that server. Expected: `builtFor: jf10`, `hostTarget: jf10`, `mismatch: false`, **PASS**.

## Existing manifest URLs

The `10.11/manifest.json`, `12/manifest.json`, `10.10/manifest.json`, and `legacy/manifest.json` files inside this test directory are byte-identical to `manifest.json`. They model the old URLs being retained as mirrors. For example, replacing the configured URL with:

```text
https://raw.githubusercontent.com/4eh5xitv6787h645ebv/jellyfin-plugins/test/pr799-unified-manifest/tests/pr799/10.11/manifest.json
```

still selects jf12 on Jellyfin 12. These are test URLs; the actual existing n00bcodr URLs do not change until the PRs are merged/published.

## Optional warning test

On the disposable Jellyfin 12 server, first install the correct test build above. Stop Jellyfin, replace only its installed `Jellyfin.Plugin.JellyfinEnhanced.dll` with the DLL from `assets/Jellyfin.Plugin.JellyfinEnhanced_10.11.0.zip`, and start it again. The matching ZIP is linked in this directory; this intentionally bypasses catalog selection.

Open Enhanced's configuration page: the red **Wrong build for this Jellyfin version** banner should appear. The logs contain `BUILD/HOST MISMATCH`.

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

Both builds passed with zero warnings/errors. Local tests on Jellyfin 12 RC6 verified default installation, identical requests and DLL hashes from both `12.4.1.0` revision buttons in the exact original PR manifest, the older-version exception, and the guard endpoint/banner in both matching and mismatching states. The current upstream source hash check in the original PR has drifted for two Jellyfin master files; those pins were not changed by this test bundle. Automatic updates and future Jellyfin releases are not covered by those local results.
