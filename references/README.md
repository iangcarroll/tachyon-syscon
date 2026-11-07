# External hardware references

Downloaded references are local cache files, not firmware source. The pinned
[fetch manifest](fetch-manifest.json) records their URLs, sizes and SHA-256 hashes.
The build itself needs no hardware-reference payloads; the MCU emulator and
profile tests need the small TI group.

From the repository root:

```sh
make references-fetch
make references-check
```

`references-check` performs no download or write. Missing or corrupt files fail
verification. Normal fetching verifies downloads before atomic publication and
can restore missing extracted files from a verified device pack.

| Group | Purpose | Download size |
| --- | --- | ---: |
| `test-ti` (default) | TI headers, device pack and verified SVD extraction | 3.18 MB |
| `hardware-tachyon` | Tachyon comparison documentation and debug adapter assets | 6.04 MB |
| `hardware-other` | Other Particle schematics, CAD and supporting documents | 511.05 MB |

Optional groups are explicit:

```sh
.venv/bin/python tools/fetch_references.py --group hardware-tachyon
.venv/bin/python tools/fetch_references.py --group hardware-other
.venv/bin/python tools/fetch_references.py --check --group hardware-tachyon
```

Existing downloaded files remain available locally when removed from Git
tracking. Removing payloads from the current tree does not remove older Git
history. The compatibility command `tools/catalog_references.py` accepts the
same fetch/check options and no longer rewrites documentation or inventories.

The TI pack is version-pinned and its requested members are independently
hashed. The historical 21 header snapshots have an extra terminal newline;
the manifest explicitly pins both upstream and stored hashes and records that
transformation. A changed upstream response is never silently accepted.
Some optional web snapshots have mutable URLs; strict verification can fail if
they change. The manifest is an integrity contract, not a guarantee that every
upstream server will retain an old response forever.

The TI profile is evidence for the emulator, not identification of the attached
MCU. Other Particle products do not establish Tachyon pin mappings. Preserve
upstream license information when using the fetched files; the core pack fetch
also extracts its license. See [debug and recovery notes](../docs/debug-probe.md)
for the independent hardware gates.
