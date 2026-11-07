# Persistent configuration reconstruction

This is a host-testable C reconstruction of syscon 1.0.52 configuration logic, not a flashable replacement. The pinned original ARM instructions are the differential oracle. The following entry points have corresponding implementations in `src/config.c`:

| Original | Reconstructed operation |
| --- | --- |
| `0x27dc`, `0x2810`, `0x282c`, `0x2840` | Readable/writable fields, XOR checksum, slot validation |
| `0x27a8` | `syscon_store_erase` |
| `0x28d4` | Internal slot encoder and eight-word programming |
| `0x296c`, `0x29a0`, `0x2cb8` | Legacy last-match reads and first-blank selection |
| `0x2abc` | Runtime configuration compaction |
| `0x2f0c` | Append |
| `0x2fa0` | Namespace initialization |
| `0x32c8` | Runtime configuration update |
| `0x2d08`, `0x2d94`, `0x2df8` | Packed 22-byte runtime settings decode |

The native API exposes the flash peripheral and assertion/reset boundary explicitly. It does not implement the original hardware register driver. Return `-1` represents reaching an assertion that resets the original firmware; it is not an original return value. Return `-2` identifies an input not yet supported by this reconstruction. `syscon_config_set` does not automatically update host-owned runtime RAM; callers explicitly invoke `syscon_config_load`, while the original entry point reloads runtime settings on successful mutation.

## Behavior preserved

- Slots are 64 bytes: two 31-byte strings and their XOR checksums. An unused slot must contain all `0xff`; an erased first byte alone is insufficient.
- Last matching key wins even if that slot has invalid checksums. The original invokes validation for diagnostics and ignores its result during key search and value extraction.
- Reading truncates values to 30 bytes and cuts at the first semicolon. A checksum-invalid latest value can therefore suppress a write if its extracted string matches the requested value.
- Runtime update skips identical values. Empty values are refused on the ordinary append path, but can be written during compaction when the namespace is full.
- Compaction starts with the requested key/value, scans the 15 old slots in reverse order, and retains the newest distinct keys. It checks key readability and both checksums but does not check value readability. More than eight distinct retained entries fails before erasing.
- Compaction writes the new entry first, then the retained entries in reverse-chronological order. It fails immediately after an unsuccessful erase, blank check, or double-word program, leaving prior effects intact.
- Namespace initialization only checks that `confVersion` is found; it does not require the value `1`. If absent, it erases and appends `confVersion=1`, ignoring those intermediate return statuses, then asserts if lookup still fails.
- Boolean parsing is case-sensitive. Timers parse signed 32-bit decimal values, reject negative values and trailing junk, and clamp accepted values to 3–30 seconds. Hardware revision occupies eight bytes with the final byte forced to NUL.

## Flash model and its limits

`tools/config_oracle.py` replaces only peripheral-dependent functions: MAIN write/erase unprotection, status reporting, blank verification, programming, erasing, watchdog feeding, diagnostic UART, and the assertion boundary. It executes the original configuration algorithms and libc functions. Programming is modeled as atomic eight-byte operations with no zero-to-one transitions. Injected failed operations return terminal DONE/fail status 1; success is DONE/PASS status 3. Failed operations leave memory unchanged for that single operation; earlier operations remain visible. This does not simulate a power interruption within a flash programming pulse or the silicon ECC state.

The helper at `0x7b44` writes zero to `CMDWEPROTA/B/C`; it does not clear status. This was corrected by checking TI's official FLASHCTL register definitions (`analysis/ti-hw-flashctl.h`). The high-level model assumes those MAIN regions are unprotected; the lower-level controller tests represent the actual mask writes.

The erase loop requests a **sector erase at every 64-byte slot address**. Each request erases the containing 1 KiB sector, including the last 64 bytes beyond the runtime namespace's 960 used bytes. The size comes from TI's [`DL_FLASHCTL_SECTOR_SIZE` for MSPM0L11xx/L13xx](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/2_08_00_03/docs/english/driverlib/mspm0l11xx_l13xx_api_guide/html/group___f_l_a_s_h_c_t_l.html). The exact board silicon identity remains to be read from hardware.

## Outstanding coverage

- A checksum-valid corrupt legacy value containing `%` reaches the original `snprintf` as a format string with absent variadic arguments during compaction. Its output depends on the original stack. The host reconstruction returns `-2` at this boundary; it must not be represented as equivalent for arbitrary corrupt flash contents.
- Diagnostic UART output, watchdog timing, real flash-controller status/ECC behavior, reset behavior, and a boot-to-power-state end-to-end execution are outside this module's completed boundary.
- These tests do not establish full-firmware equivalence, safety to flash, or byte-identical ARM output for this module.

## Validation

Run `syscon-re/.venv/bin/python -m pytest -q syscon-re/tests/test_config_updates.py` from the workspace root. The test groups compare complete 1 KiB flash contents, ordered flash operations and statuses, return outcomes, and packed runtime RAM with the original machine code. Scenarios include repeated writes until compaction/full capacity, corrupt records, legacy delimiters, sector-tail erasure, injected failures at individual flash operations, initialization failures, empty keys and values, and numerical parsing boundaries.

## Serial command integration

`src/config_commands.c` implements eleven command handlers through `syscon_config_dispatch`: the runtime and identity variants of GET, SET, FIND, DUMP, and ERASE, plus CONFIG_INTERNAL. This adapter reloads the packed runtime state when the corresponding original handler does. An identical runtime update returns early without reloading; a successful identity append does reload. Runtime erase reloads settings, while identity erase leaves the previous runtime cache untouched until a subsequent reload. CONFIG_INTERNAL reports the cached runtime state, not fresh flash contents.

The two erase passwords differ in the original image: runtime erase checks `particle` (`0xb1f4`), while identity erase checks `B23000` (`0xb1b1`). The differential pipeline caught and corrected an initial incorrect assumption that they were the same. These are literal firmware command gates, not host/account credentials.

The commands preserve the original fixed `sscanf` scanset behavior: up to 31 non-colon characters per conversion, nonempty fields, and successful conversions even when the final literal colon is absent. FIND uses the original signed 32-bit decimal conversion semantics, mutates the index string into the recovered key, and requires a valid slot. DUMP reports nonblank invalid slots, retains slot ordering, and emits the rejected-slot warning count. Failed erases report the original `Invalid password` message even if the failure was a controller error after a correct password.

`tests/test_config_commands.py` connects the reconstructed UART parser to those C handlers and compares every emitted response/echo event, both 1 KiB flash sectors, ordered controller operations, and all 22 runtime bytes against `tools/config_protocol_oracle.py`. The ARM side executes the original UART parser **and actual configuration handlers**; only the output transport and the explicitly described peripheral boundaries are substituted. It includes fragmented input, echo on/off, repeated updates through compaction, corrupt latest records, dump rejection behavior, malformed and oversized fields, both erase paths, and flash-failure responses. An assertion/reset is still represented by an explicit host exception/callback boundary, not by simulated boot/recovery.

Validation checkpoint: the nine configuration-core groups and seven UART integration groups passed together: **16 passed in 23.74 seconds**. The UART groups are separately runnable with `syscon-re/.venv/bin/python -m pytest -q syscon-re/tests/test_config_commands.py`.
