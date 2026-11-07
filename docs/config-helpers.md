# Original-ABI configuration entries

`target/config_helpers.c` replaces the twelve previously folded namespace entries with independently callable ARM32 functions. `target/config_read.c` and `target/config_storage.c` add actual source-backed read/search, append/erase, parsing and runtime loading dependencies. These are additional target implementations; the host adapter in `src/config.c` is unchanged.

| Original entries | Target source | Behavior |
| --- | --- | --- |
| 3048, 3098, 30c0, 30e8, 30ec | config_helpers.c | Indexed lookup, runtime/identity slot blank checks and counts |
| 31d0, 3278, 3298, 32b0 | config_helpers.c | Identity erase, append, lookup and indexed lookup |
| 339c, 33b4, 3464 | config_helpers.c | Runtime lookup, erase and indexed lookup |
| 27dc, 2810, 282c, 2840, 296c, 29a0, 2cb8 | config_read.c | Field validation, checksum, record validation/read, search and lookup |
| 2738, 27a8, 28d4, 2d08, 2d94, 2df8, 2f0c | config_storage.c | Flash diagnostic, erase/write, boolean/integer parsing, runtime load and append |

The ABI uses target pointers and 32-bit integers, fixed original namespace addresses (`0xf800` and `0xfc00`), and the packed 22-byte runtime state at `0x20000030`. Original read-only string addresses are retained. Candidate code is relocated into an emulation region; the original flash is readable but not executable in the candidate CPU. This is not a flashable image or a byte-identical rebuild.

## Genuine integration and explicit dependencies

`tools/config_helpers_oracle.py` builds the configuration files together with reconstructed runtime memory, arithmetic, scanner/formatter, heap, stdio, target formatting adapters and `src/flash_controller.c`. No host libc or archive `libgcc` implements the target logic. The builder's manifest records exact source/header hashes, compiler and flags. No shared build script or ledger was modified.

The integrated tests run namespace append → field validation → slot search → actual nano `snprintf` → flash-controller programming → runtime reload, then lookup/indexed readback and namespace erase. Both ARM executions use the same register-triggered `FlashControllerModel`; this is a peripheral model at MMIO, not a replacement configuration or flash function. Watchdog writes at `0x40081108` are also observed. Tests compare the complete ordered FLASHCTL read/write trace, completed command events, controller register state, both 1 KiB flash sectors, runtime configuration bytes and errno. Integrated cases assert that **neither CPU invoked any function-entry hook**.

The model preserves repeated sector erases at 64-byte address increments, including erasure of the unused tail of the runtime namespace's sector. The sector geometry is the TI MSPM0L11xx/L13xx [`DL_FLASHCTL_SECTOR_SIZE` of 1024 bytes](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/2_08_00_03/docs/english/driverlib/mspm0l11xx_l13xx_api_guide/html/group___f_l_a_s_h_c_t_l.html). This does not establish electrical/ECC or power-interruption equivalence.

Explicit external boundaries in the standalone build:

- `syscon_cfg_assert` corresponds to `0x2678`. A generated BKPT symbol deliberately traps unbound assertion execution. Unit tests bind it to a recording callback that returns, so they verify the caller's post-assert behavior without pretending to reproduce system reset.
- `syscon_target_logger` uses the existing source-backed target adapter and logger. Its `syscon_target_uart_write`, `syscon_target_now` and `syscon_target_color` endpoints deliberately trap unless bound. Genuine configuration integration uses the original logging-disabled RAM flag, runs both logger bodies and reaches none of these endpoints. Separate dependency tests record logger arguments.
- `syscon_flash_*` is fully linked from reconstructed source; its register read/write callbacks perform actual volatile target MMIO accesses. No flash command endpoint is hooked in integrated cases.
- String routines, `syscon_rt_isalnum`, `syscon_rt_atoi`, `syscon_rt_strtol`, `syscon_rt_snprintf`, and their runtime dependencies are reconstructed source. Original read-only ctype/string data and initialized RAM are test inputs, not original executable dependencies.

## Preserved behaviors and test evidence

`tests/test_config_helpers.py` has twenty-one groups/parameter cases. It checks every byte of every valid slot for the two blank-check entry points, invalid and wrapping indices, raw dependency status propagation, both passwords, assertion continuation, and 31-byte input boundaries. Corrupt slots exercise key/value checksums, invalid characters and semicolon trimming. The source-backed tests include all 256 byte values at four field positions, latest-record lookup, full namespace rejection, zero/rounded erase sizes, each of the eight partial program failure points, blank/erase errors, and packed boolean/integer loading with overflow and 3–30 clamping. A fresh candidate CPU with a deliberately broken checksum function fails the integrated indexed-read comparison.

Reference instruction exercise for the twelve assigned entries reaches all their discovered instructions; this is not exhaustive input/path equivalence. Additional helper coverage retains visible gaps such as the append length diagnostic that normal validation rejects before reaching. The scoped machine-readable report is `analysis/config-helpers-test-instruction-coverage.json`; the mapping is `analysis/config-helpers-mapping.json`.

Validation: the twenty configuration cases passed in 4.69 seconds. Configuration plus runtime scanning and flash-controller tests then passed together: **41 passed in 18.56 seconds**. The module owns all its Unicorn CPU pairs until teardown and collects them outside execution. That ownership discipline and a prior per-call GC toggle did not establish a fix for a native `libunicorn` crash in larger selections. The controller integration now maps candidate flash backing read/write but **non-executable**, because its MMIO status callback applies peripheral writes using the emulator API. Every CPU-originated flash write is rejected by a test hook; dedicated negative controls deliberately attempt a CPU store and execution from original flash. Other candidate tests retain their normal read-only flash mapping. A subsequent affected-module selection passed with this controller-only backing change; the exact native root cause (`load_helper+0x848` during candidate `emu_start`) is not established.

## Remaining proof boundaries

`target/config_update.c` now provides compaction, namespace initialization and runtime update, with frame-address capture in `target/config_update_abi.S` for the stack-usage diagnostic. `tests/test_config_target_updates.py` exercises initialization sequencing, repeated compactions, corrupted records, duplicate keys, capacity bounds, enabled diagnostics and every retained-record program failure position.

`syscon_cfg_write_slot` copies keys and values literally into the persistent slot: at most 30 bytes per field, a NUL terminator, erased-byte padding and the existing checksums. Legacy `%` characters are preserved rather than interpreted as printf formats. This is an approved behavioral correction: ordinary configuration commands already reject `%`. The original instruction oracle remains a witness to the old corruption, while candidate tests check literal bytes, field bounds, flash effects, UART readback and fresh-boot persistence. `tools/config_target_counterexample.py` replays the historical `%u` case and writes its current result under `build/`; historical analysis snapshots describe earlier implementations. The old assembly frame adapter and numeric saved-return argument are removed.

No universal equivalence theorem, complete physical boot or hardware safety-to-flash result follows from these scoped tests. Historical checkpoint counts below describe their respective earlier runs.

After target logger integration and controller-backing negative controls, the affected logger/format/configuration selection passed **64 tests in 21.26 seconds**. The additional controller test verifies that CPU-originated flash stores fail the environment guard and original-flash instruction fetch raises `UC_ERR_FETCH_PROT`. Earlier twenty-case figures above describe their historical checkpoint.
