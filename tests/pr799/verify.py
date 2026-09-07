#!/usr/bin/env python3
"""Check the installed PR #799 build through Jellyfin's authenticated API."""
import argparse
import getpass
import json
import sys
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True, help='Jellyfin URL, e.g. http://localhost:8096')
    parser.add_argument('--username', default='admin')
    parser.add_argument('--expect-mismatch', action='store_true', help='Only for the intentional wrong-build test')
    args = parser.parse_args()
    base = args.server.rstrip('/')
    authorization = 'MediaBrowser Client="PR799 verifier", Device="Test", DeviceId="pr799-verifier", Version="1.0"'

    def api(path, body=None, token=None):
        headers = {'Content-Type': 'application/json', 'Authorization': authorization}
        if token:
            headers['Authorization'] += ', Token="' + token + '"'
        request = urllib.request.Request(base + path, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)

    try:
        auth = api('/Users/AuthenticateByName', {'Username': args.username, 'Pw': getpass.getpass('Jellyfin password: ')})
        token = auth['AccessToken']
        compat = api('/JellyfinEnhanced/host-compat', token=token)
        print(json.dumps(compat, indent=2))
        expected = 'jf12' if int(compat['hostVersion'].split('.')[0]) >= 12 else 'jf10'
        passed = compat['hostTarget'] == expected and compat['mismatch'] == args.expect_mismatch
        passed = passed and ((compat['builtFor'] != expected) if args.expect_mismatch else (compat['builtFor'] == expected))
        if compat.get('pluginVersion') != '12.5.0.0':
            print('FAIL: Expected the test build version 12.5.0.0.')
            return 1
        packages = api('/Packages', token=token)
        entries = [p for p in packages if p.get('guid', '').replace('-', '') == 'f69e946a4b3c4e9a8f0a8d7c1b2c4d9b']
        if len(entries) != 1:
            print('FAIL: Expected one Enhanced catalog entry, found', len(entries))
            return 1
        rows = [v for v in entries[0]['versions'] if v['version'] == '12.5.0.0']
        print('Catalog rows for 12.5.0.0:', [(r['version'], r['targetAbi']) for r in rows])
        expected_abis = ['12.0.0.0', '10.11.0.0'] if expected == 'jf12' else ['10.11.0.0']
        passed = passed and [r['targetAbi'] for r in rows] == expected_abis
        print('PASS' if passed else 'FAIL', '— build/host compatibility and catalog ordering')
        return 0 if passed else 1
    except urllib.error.HTTPError as error:
        print('FAIL: Jellyfin returned HTTP', error.code, file=sys.stderr)
        if error.code == 404:
            print('Install the test manifest build and restart. Published releases do not include /host-compat.', file=sys.stderr)
        elif error.code in (401, 403):
            print('Use a Jellyfin administrator account.', file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as error:
        print('FAIL:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
