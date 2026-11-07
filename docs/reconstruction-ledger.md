# Reconstruction ledger

This is a function-by-function evidence inventory, not a completion percentage. The machine-readable companion is `analysis/reconstruction-ledger.json`; regenerate with `python3 tools/reconstruction_ledger.py` after reviewing the curated mapping when implementations change.

The current static inventory contains 389 identified functions. Their semantic states are:

| State | Count |
| --- | ---: |
| reconstructed_bounded | 389 |

“Reconstructed” means a scoped C adapter exists. It does not mean every input/path, original ABI, exact machine bytes, or board behavior is verified. “Folded” helpers are implemented only as effects within their tested callers, not complete generic entry points. All currently identified runtime candidates now have scoped replacements; undiscovered code and unsupported domains are not implied complete.

## Independent evidence axes

- Semantic mapping points to actual C sources, module tests, and scope documentation. Unreviewed Ghidra output and endpoint hooks do not count as replacement code.
- Original instruction exercise uses observed addresses from the pinned successful `analysis/full-suite-checkpoint.json` invocation, recomputed against the current hashed listing/ranges. Counts can differ from that report after static-analysis corrections. The snapshot may precede recent additions: a reconstructed routine with zero exercise at that checkpoint is not automatically unimplemented. Module tests and later scoped reports supply separate evidence.
- Nine rebuilt bodies have exact bytes: checksum `0x282c` (20 bytes), delay `0x7ae8` (10), memset `0x975a` (16), strchr `0x9828` (28), switch dispatch `0xc0` (18), `0xd4` (18), `0x2660` (20), divide-by-zero `0x3d0` (2), and float-to-int `0x135c` (64). Unresolved relocations disqualify strrchr. These isolated matches do not establish whole-firmware binary equivalence. Runtime archive fragments are listed separately; a short relocation-masked match does not establish identity. In particular, matches identifying `0x8f88` and `0x92f4` as newlib I/O routines are rejected generic-wrapper matches.
- The `target_abi` records identify standalone target interfaces, not universal input-domain equivalence. Two checksum theorems have distinct scopes: the host adapter uses a SRAM/sequential/AAPCS contract; the actual physical symbol has a full-register/read-event relation documented in `docs/physical-checksum-proof.md`. Neither proves all callers or the whole image.
- Hardware validation is `not_performed` for every ledger entry. A complete experimental target image links and boots in the model; no safe flash candidate is established.

The JSON includes hashes of every mapped source/test/document and static/coverage inputs. When the test checkpoint records initial code/test/tool hashes, the ledger checks whether inputs stayed unchanged during the run and still match current files; a missing historical hash record remains unverified.

Checkpoint test counts: `{'passed': 990, 'failed': 0, 'skipped': 0, 'error': 0, 'xfailed': 0, 'xpassed': 0, 'collected': 990}`. Inputs unchanged during the run: `True`. Current code matches that passed snapshot: `True`.

## Known application and HAL gaps

| Entry | Missing behavior |
| --- | --- |
| — | Every currently identified app/HAL entry has a scoped or caller-folded implementation. This does not cover arbitrary helper domains or full target integration. |

All currently identified compiler/libc runtime entries have source replacements and direct ARM comparisons. Arithmetic, memory, support, heap, stdio, and scan/printf scope is documented separately. The runtime builds use reviewed source rather than installed libc/libgcc archives. This does not prove complete path coverage or full-image ABI integration.

## Static inventory exceptions

FLASHCTL executes 44 instruction bytes copied from image `0xaaf0` to SRAM `0x20000000`, with a four-byte literal following them. The `0xaae0` veneer is identified, but the RAM body is not an extra flash function in the identified flash-function inventory. The JSON separately records successful scoped reports containing its actual RAM instruction addresses. Its modeled status/polling behavior is in `src/flash_controller.c` and `docs/flash-controller.md`.

Execution also discovered the `%p` block at `0x9256..0x9268`, previously missing from Ghidra's listing. It belongs to formatter `0x9038`; the JSON records which instruction addresses remain absent from the current listing. Updated static analysis can change counts without changing replacement correctness. Runtime fingerprints at non-entry/interior addresses are retained separately for future boundary review.

## Every identified function

`Exercise` is exercised/identified instruction addresses in the checkpoint, not semantic completion. `C` is a scoped replacement; `folded` is only its caller domain; `missing` is a known app/HAL gap; `runtime` is an unreconstructed runtime candidate.

| Entry | Static name | Semantic state | Source | Exercise |
| --- | --- | --- | --- | ---: |
| `0xc0` | `__gnu_thumb1_case_sqi` | C | `target/runtime_arithmetic_abi.S` | 9/9 |
| `0xd4` | `__gnu_thumb1_case_uqi` | C | `target/runtime_arithmetic_abi.S` | 9/9 |
| `0xe8` | `FUN_000000e8` | C | `src/runtime_arithmetic.c` | 132/132 |
| `0x1f4` | `FUN_000001f4` | C | `src/runtime_arithmetic.c` | 3/3 |
| `0x1fc` | `FUN_000001fc` | C | `src/runtime_arithmetic.c` | 229/229 |
| `0x3c8` | `FUN_000003c8` | C | `src/runtime_arithmetic.c` | 3/3 |
| `0x3d0` | `FUN_000003d0` | C | `target/runtime_arithmetic_abi.S` | 1/1 |
| `0x3d4` | `FUN_000003d4` | C | `target/runtime_arithmetic_abi.S` | 4/4 |
| `0x3dc` | `FUN_000003dc` | C | `target/runtime_arithmetic_abi.S` | 7/7 |
| `0x3ec` | `FUN_000003ec` | C | `src/runtime_arithmetic.c` | 5/5 |
| `0x3f8` | `FUN_000003f8` | C | `src/runtime_arithmetic.c` | 8/8 |
| `0x40c` | `FUN_0000040c` | C | `src/runtime_arithmetic.c` | 8/8 |
| `0x420` | `FUN_00000420` | C | `src/runtime_arithmetic.c` | 8/8 |
| `0x434` | `FUN_00000434` | C | `src/runtime_arithmetic.c` | 8/8 |
| `0x448` | `FUN_00000448` | C | `target/runtime_arithmetic_abi.S` | 27/27 |
| `0x488` | `FUN_00000488` | C | `src/runtime_arithmetic.c` | 45/45 |
| `0x4e4` | `FUN_000004e4` | C | `target/runtime_arithmetic_float.c` | 20/20 |
| `0x514` | `FUN_00000514` | C | `target/runtime_arithmetic_float.c` | 23/23 |
| `0x550` | `FUN_00000550` | C | `src/runtime_arithmetic.c` | 201/201 |
| `0x6e8` | `FUN_000006e8` | C | `vendor/gcc-soft-fp/addsf3.c` | 409/409 |
| `0xa24` | `FUN_00000a24` | C | `vendor/gcc-soft-fp/divsf3.c` | 255/271 |
| `0xc54` | `FUN_00000c54` | C | `src/runtime_arithmetic.c` | 38/38 |
| `0xca0` | `FUN_00000ca0` | C | `src/runtime_arithmetic.c` | 70/70 |
| `0xd2c` | `FUN_00000d2c` | C | `src/runtime_arithmetic.c` | 67/67 |
| `0xdb4` | `FUN_00000db4` | C | `vendor/gcc-soft-fp/mulsf3.c` | 277/282 |
| `0x1000` | `FUN_00001000` | C | `vendor/gcc-soft-fp/subsf3.c` | 425/425 |
| `0x135c` | `FUN_0000135c` | C | `vendor/gcc-soft-fp/fixsfsi.c` | 29/29 |
| `0x139c` | `FUN_0000139c` | C | `vendor/gcc-soft-fp/floatsisf.c` | 74/74 |
| `0x1438` | `FUN_00001438` | C | `vendor/gcc-soft-fp/floatunsisf.c` | 63/63 |
| `0x14bc` | `FUN_000014bc` | C | `vendor/gcc-soft-fp/adddf3.c` | 816/816 |
| `0x1b34` | `FUN_00001b34` | C | `vendor/gcc-soft-fp/subdf3.c` | 893/893 |
| `0x2258` | `FUN_00002258` | C | `vendor/gcc-soft-fp/fixdfsi.c` | 42/42 |
| `0x22c4` | `FUN_000022c4` | C | `vendor/gcc-soft-fp/extendsfdf2.c` | 66/66 |
| `0x2354` | `FUN_00002354` | C | `target/runtime_arithmetic_abi.S` | 7/7 |
| `0x2364` | `FUN_00002364` | C | `target/runtime_arithmetic_abi.S` | 7/7 |
| `0x2374` | `FUN_00002374` | C | `src/runtime_arithmetic.c` | 5/5 |
| `0x2380` | `FUN_00002380` | C | `src/runtime_arithmetic.c` | 8/8 |
| `0x2394` | `FUN_00002394` | C | `src/runtime_arithmetic.c` | 8/8 |
| `0x23a8` | `FUN_000023a8` | C | `src/runtime_arithmetic.c` | 8/8 |
| `0x23bc` | `FUN_000023bc` | C | `src/runtime_arithmetic.c` | 8/8 |
| `0x23d0` | `FUN_000023d0` | C | `src/runtime_arithmetic.c` | 21/21 |
| `0x240c` | `FUN_0000240c` | C | `src/runtime_arithmetic.c` | 9/9 |
| `0x2424` | `FUN_00002424` | C | `src/runtime_arithmetic.c` | 63/63 |
| `0x24a8` | `FUN_000024a8` | C | `src/runtime_arithmetic.c` | 99/99 |
| `0x2574` | `FUN_00002574` | C | `src/runtime_arithmetic.c` | 98/98 |
| `0x263c` | `FUN_0000263c` | C | `src/runtime_memory.c` | 10/10 |
| `0x2650` | `FUN_00002650` | C | `src/runtime_memory.c` | 7/7 |
| `0x2660` | `__gnu_thumb1_case_shi` | C | `target/runtime_arithmetic_abi.S` | 10/10 |
| `0x2678` | `FUN_00002678` | C | `src/fault_control.c` | 67/67 |
| `0x2738` | `FUN_00002738` | C | `src/flash_controller.c` | 33/33 |
| `0x27a8` | `FUN_000027a8` | C | `src/config.c` | 20/20 |
| `0x27dc` | `FUN_000027dc` | C | `src/config.c` | 25/25 |
| `0x2810` | `FUN_00002810` | C | `src/config.c` | 12/12 |
| `0x282c` | `FUN_0000282c` | C | `src/config.c` | 10/10 |
| `0x2840` | `FUN_00002840` | C | `src/config.c` | 60/60 |
| `0x28d4` | `FUN_000028d4` | C | `src/config.c` | 61/61 |
| `0x296c` | `FUN_0000296c` | C | `src/config.c` | 22/22 |
| `0x29a0` | `FUN_000029a0` | C | `src/config.c` | 119/119 |
| `0x2abc` | `FUN_00002abc` | C | `src/config.c` | 207/207 |
| `0x2cb8` | `FUN_00002cb8` | C | `src/config.c` | 32/32 |
| `0x2d08` | `FUN_00002d08` | C | `src/config.c` | 50/50 |
| `0x2d94` | `FUN_00002d94` | C | `src/config.c` | 42/42 |
| `0x2df8` | `FUN_00002df8` | C | `src/config.c` | 96/96 |
| `0x2f0c` | `FUN_00002f0c` | C | `src/config.c` | 52/57 |
| `0x2fa0` | `FUN_00002fa0` | C | `src/config.c` | 56/56 |
| `0x3048` | `FUN_00003048` | C | `target/config_helpers.c` | 32/32 |
| `0x3098` | `FUN_00003098` | C | `target/config_helpers.c` | 18/18 |
| `0x30c0` | `FUN_000030c0` | C | `target/config_helpers.c` | 18/18 |
| `0x30e8` | `FUN_000030e8` | C | `target/config_helpers.c` | 2/2 |
| `0x30ec` | `FUN_000030ec` | C | `target/config_helpers.c` | 2/2 |
| `0x30f0` | `FUN_000030f0` | C | `src/application_glue.c` | 11/11 |
| `0x3114` | `FUN_00003114` | C | `src/diagnostics.c` | 3/3 |
| `0x3120` | `FUN_00003120` | C | `src/diagnostics.c` | 3/3 |
| `0x312c` | `FUN_0000312c` | C | `src/diagnostics.c` | 3/3 |
| `0x3138` | `FUN_00003138` | C | `src/diagnostics.c` | 3/3 |
| `0x3144` | `FUN_00003144` | C | `src/diagnostics.c` | 3/3 |
| `0x3150` | `FUN_00003150` | C | `src/diagnostics.c` | 3/3 |
| `0x315c` | `FUN_0000315c` | C | `src/diagnostics.c` | 12/12 |
| `0x3178` | `FUN_00003178` | C | `src/diagnostics.c` | 12/12 |
| `0x3194` | `FUN_00003194` | C | `src/diagnostics.c` | 24/24 |
| `0x31d0` | `FUN_000031d0` | C | `target/config_helpers.c` | 57/57 |
| `0x3278` | `FUN_00003278` | C | `target/config_helpers.c` | 12/12 |
| `0x3298` | `FUN_00003298` | C | `target/config_helpers.c` | 8/8 |
| `0x32b0` | `FUN_000032b0` | C | `target/config_helpers.c` | 8/8 |
| `0x32c8` | `FUN_000032c8` | C | `src/config.c` | 82/82 |
| `0x339c` | `FUN_0000339c` | C | `target/config_helpers.c` | 8/8 |
| `0x33b4` | `FUN_000033b4` | C | `target/config_helpers.c` | 57/57 |
| `0x3464` | `FUN_00003464` | C | `target/config_helpers.c` | 8/8 |
| `0x347c` | `FUN_0000347c` | C | `src/diagnostics.c` | 3/3 |
| `0x3488` | `FUN_00003488` | C | `src/diagnostics.c` | 148/148 |
| `0x3610` | `FUN_00003610` | C | `src/application.c` | 5/5 |
| `0x3620` | `FUN_00003620` | C | `src/ioexpander.c` | 18/21 |
| `0x364e` | `FUN_0000364e` | C | `src/ioexpander.c` | 10/10 |
| `0x3668` | `FUN_00003668` | C | `src/ioexpander.c` | 31/33 |
| `0x36bc` | `FUN_000036bc` | C | `src/ioexpander.c` | 54/58 |
| `0x374c` | `FUN_0000374c` | C | `src/ioexpander.c` | 29/31 |
| `0x379c` | `FUN_0000379c` | C | `src/ioexpander.c` | 33/33 |
| `0x37e4` | `FUN_000037e4` | C | `src/ioexpander.c` | 12/12 |
| `0x3808` | `FUN_00003808` | C | `src/ioexpander.c` | 36/38 |
| `0x386c` | `FUN_0000386c` | C | `src/ioexpander.c` | 87/87 |
| `0x3940` | `FUN_00003940` | C | `src/ioexpander.c` | 63/63 |
| `0x39e8` | `FUN_000039e8` | C | `src/ioexpander.c` | 64/64 |
| `0x3a8c` | `FUN_00003a8c` | C | `src/application.c` | 27/27 |
| `0x3ad4` | `FUN_00003ad4` | C | `src/application.c` | 11/11 |
| `0x3af4` | `FUN_00003af4` | C | `src/application.c` | 10/10 |
| `0x3b0c` | `FUN_00003b0c` | C | `src/application.c` | 19/19 |
| `0x3b34` | `FUN_00003b34` | C | `src/application.c` | 306/306 |
| `0x3ec0` | `FUN_00003ec0` | C | `src/application.c` | 14/14 |
| `0x3ef0` | `cmd_VERSION` | C | `src/control_commands.c` | 7/7 |
| `0x3f08` | `FUN_00003f08` | C | `target/callback_helpers.c` | 11/11 |
| `0x3f24` | `cmd_HELP` | C | `src/control_commands.c` | 39/39 |
| `0x3f80` | `cmd_IOEXP_READ` | C | `src/control_commands.c` | 29/29 |
| `0x3fd0` | `cmd_PWRSTATUS` | C | `src/control_commands.c` | 5/5 |
| `0x3fdc` | `cmd_CONFIG_INTERNAL` | C | `src/config_commands.c` | 69/69 |
| `0x40a0` | `cmd_WAKE_AFTER` | C | `src/control_commands.c` | 33/33 |
| `0x40fc` | `cmd_MCU_SLEEP` | C | `src/control_commands.c` | 6/6 |
| `0x4110` | `cmd_MCU_REBOOT` | C | `src/control_commands.c` | 47/47 |
| `0x41a4` | `cmd_SHUTDOWN_REASON` | C | `src/control_commands.c` | 46/46 |
| `0x422c` | `cmd_560D_DIRECT` | C | `src/control_commands.c` | 15/15 |
| `0x4258` | `cmd_560D_ON` | C | `src/control_commands.c` | 37/37 |
| `0x42c8` | `cmd_LEDSTATUS` | C | `src/control_commands.c` | 37/37 |
| `0x4320` | `cmd_SET_PATTERN` | C | `src/control_commands.c` | 28/28 |
| `0x4364` | `cmd_SET_RGB` | C | `src/control_commands.c` | 77/77 |
| `0x4420` | `cmd_READ_PWR` | C | `src/control_commands.c` | 39/39 |
| `0x4490` | `cmd_CONFIG_ID_FIND` | C | `src/config_commands.c` | 28/28 |
| `0x44dc` | `cmd_CONFIG_FIND` | C | `src/config_commands.c` | 28/28 |
| `0x4528` | `FUN_00004528` | C | `src/config_commands.c` | 72/72 |
| `0x45e0` | `cmd_CONFIG_ID_DUMP` | C | `src/config_commands.c` | 5/5 |
| `0x45ec` | `cmd_CONFIG_DUMP` | C | `src/config_commands.c` | 5/5 |
| `0x45f8` | `cmd_CONFIG_ID_ERASE` | C | `src/config_commands.c` | 22/22 |
| `0x4638` | `cmd_CONFIG_ID_GET` | C | `src/config_commands.c` | 28/28 |
| `0x4684` | `cmd_CONFIG_ID_SET` | C | `src/config_commands.c` | 29/29 |
| `0x46d4` | `cmd_CONFIG_ERASE` | C | `src/config_commands.c` | 22/22 |
| `0x4714` | `cmd_CONFIG_GET` | C | `src/config_commands.c` | 28/28 |
| `0x4760` | `cmd_CONFIG_SET` | C | `src/config_commands.c` | 29/29 |
| `0x47b0` | `cmd_BATCHECK` | C | `src/control_commands.c` | 4/4 |
| `0x47bc` | `cmd_GPIO_READ` | C | `src/control_commands.c` | 23/23 |
| `0x47fc` | `cmd_560D_DBG` | C | `src/control_commands.c` | 27/27 |
| `0x4850` | `cmd_KEYS` | C | `src/control_commands.c` | 29/29 |
| `0x48a4` | `cmd_560D_OFF` | C | `src/control_commands.c` | 20/20 |
| `0x48e0` | `cmd_DIAG` | C | `src/control_commands.c` | 15/15 |
| `0x4904` | `cmd_ERROR` | C | `src/control_commands.c` | 38/38 |
| `0x4970` | `cmd_KEY_MODE` | C | `src/control_commands.c` | 20/20 |
| `0x49ac` | `cmd_LOG` | C | `src/control_commands.c` | 15/15 |
| `0x49d0` | `FUN_000049d0` | C | `src/protocol.c` | 243/243 |
| `0x4c14` | `FUN_00004c14` | C | `src/application.c` | 4/4 |
| `0x4c24` | `FUN_00004c24` | C | `src/application_glue.c` | 18/18 |
| `0x4c50` | `FUN_00004c50` | C | `src/power_manager.c` | 39/39 |
| `0x4ca8` | `FUN_00004ca8` | C | `src/power_manager.c` | 33/35 |
| `0x4d00` | `FUN_00004d00` | C | `src/power_manager.c` | 33/35 |
| `0x4d58` | `FUN_00004d58` | C | `src/power_manager.c` | 7/7 |
| `0x4d68` | `FUN_00004d68` | C | `src/power_manager.c` | 15/15 |
| `0x4d9c` | `FUN_00004d9c` | C | `src/power_manager.c` | 33/35 |
| `0x4df4` | `FUN_00004df4` | C | `src/power_manager.c` | 7/7 |
| `0x4e04` | `FUN_00004e04` | C | `src/power_manager.c` | 15/15 |
| `0x4e34` | `FUN_00004e34` | C | `src/power_manager.c` | 52/52 |
| `0x4ec4` | `FUN_00004ec4` | C | `src/power_manager.c` | 7/7 |
| `0x4ed4` | `FUN_00004ed4` | C | `src/power_manager.c` | 5/5 |
| `0x4ee0` | `FUN_00004ee0` | C | `src/power_manager.c` | 82/82 |
| `0x4fd0` | `FUN_00004fd0` | C | `src/power_manager.c` | 16/16 |
| `0x5004` | `FUN_00005004` | C | `src/power_manager.c` | 23/23 |
| `0x5048` | `FUN_00005048` | C | `src/power_manager.c` | 61/62 |
| `0x50f4` | `FUN_000050f4` | C | `src/power_manager.c` | 27/27 |
| `0x5148` | `FUN_00005148` | C | `src/power_manager.c` | 17/17 |
| `0x517c` | `FUN_0000517c` | C | `src/power_manager.c` | 28/28 |
| `0x51c0` | `FUN_000051c0` | C | `src/power_manager.c` | 57/57 |
| `0x5264` | `FUN_00005264` | C | `src/power_manager.c` | 7/7 |
| `0x5274` | `FUN_00005274` | C | `src/power_manager.c` | 70/78 |
| `0x5358` | `FUN_00005358` | C | `src/power_policy.c` | 110/110 |
| `0x54cc` | `FUN_000054cc` | C | `src/power_policy.c` | 83/83 |
| `0x559c` | `FUN_0000559c` | C | `src/power_policy.c` | 9/9 |
| `0x55b4` | `FUN_000055b4` | C | `src/power_policy.c` | 4/4 |
| `0x55c4` | `FUN_000055c4` | C | `src/power_policy.c` | 8/8 |
| `0x55dc` | `FUN_000055dc` | C | `src/power_policy.c` | 26/26 |
| `0x562c` | `FUN_0000562c` | C | `src/power_policy.c` | 3/3 |
| `0x5638` | `FUN_00005638` | C | `src/power_policy.c` | 24/24 |
| `0x5670` | `FUN_00005670` | C | `src/power_policy.c` | 3/3 |
| `0x567c` | `FUN_0000567c` | C | `src/power_policy.c` | 8/8 |
| `0x5694` | `FUN_00005694` | C | `src/power_policy.c` | 43/43 |
| `0x570c` | `FUN_0000570c` | C | `src/power_key.c` | 15/15 |
| `0x5740` | `FUN_00005740` | C | `src/power_key.c` | 101/101 |
| `0x5844` | `FUN_00005844` | C | `src/power_key.c` | 67/67 |
| `0x5908` | `FUN_00005908` | C | `src/power_key.c` | 6/6 |
| `0x591c` | `FUN_0000591c` | C | `src/power_key.c` | 22/22 |
| `0x5970` | `FUN_00005970` | C | `src/power_key.c` | 19/19 |
| `0x59a0` | `FUN_000059a0` | C | `src/retained.c` | 18/18 |
| `0x59d8` | `FUN_000059d8` | C | `src/retained.c` | 68/68 |
| `0x5a88` | `FUN_00005a88` | C | `src/retained.c` | 10/10 |
| `0x5aa8` | `FUN_00005aa8` | C | `src/retained.c` | 11/11 |
| `0x5ac4` | `FUN_00005ac4` | C | `src/retained.c` | 5/5 |
| `0x5ad4` | `FUN_00005ad4` | C | `src/retained.c` | 10/10 |
| `0x5af0` | `FUN_00005af0` | C | `src/retained.c` | 4/4 |
| `0x5afc` | `FUN_00005afc` | C | `src/retained.c` | 9/9 |
| `0x5b14` | `FUN_00005b14` | C | `src/retained.c` | 3/3 |
| `0x5b20` | `FUN_00005b20` | C | `src/rgb.c` | 16/16 |
| `0x5b48` | `FUN_00005b48` | C | `src/rgb.c` | 18/18 |
| `0x5b7c` | `FUN_00005b7c` | C | `src/rgb.c` | 28/28 |
| `0x5bd4` | `FUN_00005bd4` | C | `src/rgb.c` | 16/16 |
| `0x5bfc` | `FUN_00005bfc` | C | `src/rgb.c` | 27/27 |
| `0x5c38` | `FUN_00005c38` | C | `src/rgb.c` | 20/20 |
| `0x5c68` | `FUN_00005c68` | C | `src/rgb.c` | 23/23 |
| `0x5cac` | `FUN_00005cac` | C | `src/rgb.c` | 112/112 |
| `0x5dbc` | `FUN_00005dbc` | C | `src/rgb.c` | 3/3 |
| `0x5dc8` | `FUN_00005dc8` | C | `src/rgb.c` | 18/18 |
| `0x5df4` | `FUN_00005df4` | C | `src/rgb.c` | 8/8 |
| `0x5e0c` | `FUN_00005e0c` | C | `src/rgb.c` | 8/8 |
| `0x5e24` | `FUN_00005e24` | C | `src/rgb.c` | 5/5 |
| `0x5e30` | `FUN_00005e30` | C | `src/sg560d.c` | 48/63 |
| `0x5edc` | `FUN_00005edc` | C | `src/logging.c` | 34/34 |
| `0x5f30` | `FUN_00005f30` | C | `src/sg560d.c` | 185/185 |
| `0x614c` | `FUN_0000614c` | C | `src/sg560d.c` | 40/40 |
| `0x61b8` | `FUN_000061b8` | C | `src/sg560d.c` | 7/7 |
| `0x61d0` | `FUN_000061d0` | C | `src/sg560d.c` | 10/10 |
| `0x61f0` | `FUN_000061f0` | C | `src/sg560d.c` | 10/10 |
| `0x6210` | `FUN_00006210` | C | `src/sg560d.c` | 10/10 |
| `0x6230` | `FUN_00006230` | C | `src/sg560d.c` | 3/3 |
| `0x6238` | `FUN_00006238` | C | `src/sg560d.c` | 3/3 |
| `0x6240` | `FUN_00006240` | C | `src/sg560d.c` | 3/3 |
| `0x6248` | `FUN_00006248` | C | `src/sg560d.c` | 24/24 |
| `0x6282` | `FUN_00006282` | C | `src/sg560d.c` | 44/44 |
| `0x62ec` | `FUN_000062ec` | C | `src/sg560d.c` | 56/56 |
| `0x6384` | `FUN_00006384` | C | `src/sg560d.c` | 60/60 |
| `0x6428` | `FUN_00006428` | C | `src/sg560d.c` | 40/40 |
| `0x64a0` | `FUN_000064a0` | C | `src/sg560d.c` | 43/43 |
| `0x6520` | `FUN_00006520` | C | `src/sg560d.c` | 58/58 |
| `0x65d0` | `FUN_000065d0` | C | `src/sg560d.c` | 4/4 |
| `0x65da` | `FUN_000065da` | C | `src/sg560d.c` | 4/4 |
| `0x65e4` | `FUN_000065e4` | C | `src/sg560d.c` | 4/4 |
| `0x65f0` | `FUN_000065f0` | C | `src/sg560d.c` | 36/36 |
| `0x6650` | `FUN_00006650` | C | `src/sg560d.c` | 27/27 |
| `0x6690` | `FUN_00006690` | C | `src/sg560d.c` | 6/6 |
| `0x66a0` | `FUN_000066a0` | C | `src/sg560d.c` | 9/9 |
| `0x66bc` | `FUN_000066bc` | C | `src/sg560d.c` | 33/33 |
| `0x6720` | `FUN_00006720` | C | `src/sg560d.c` | 91/91 |
| `0x6838` | `FUN_00006838` | C | `src/sg560d.c` | 33/33 |
| `0x68a4` | `FUN_000068a4` | C | `src/sg560d.c` | 29/29 |
| `0x68fc` | `FUN_000068fc` | C | `src/sg560d.c` | 24/24 |
| `0x6948` | `FUN_00006948` | C | `src/sg560d.c` | 75/75 |
| `0x6a28` | `FUN_00006a28` | C | `src/sg560d.c` | 9/9 |
| `0x6a48` | `FUN_00006a48` | C | `src/sg560d.c` | 9/9 |
| `0x6a68` | `FUN_00006a68` | C | `src/sg560d.c` | 978/978 |
| `0x7468` | `FUN_00007468` | C | `src/sg560d.c` | 13/13 |
| `0x7488` | `FUN_00007488` | C | `src/sg560d.c` | 10/10 |
| `0x74a8` | `FUN_000074a8` | C | `src/sg560d.c` | 10/10 |
| `0x74c8` | `FUN_000074c8` | C | `src/sg560d.c` | 10/10 |
| `0x74e8` | `FUN_000074e8` | C | `src/application_glue.c` | 6/6 |
| `0x74f8` | `FUN_000074f8` | C | `target/core_helpers.c` | 24/24 |
| `0x7540` | `FUN_00007540` | C | `src/tasks.c` | 6/6 |
| `0x7554` | `FUN_00007554` | C | `src/tasks.c` | 52/52 |
| `0x75d8` | `FUN_000075d8` | C | `src/tasks.c` | 102/102 |
| `0x76d8` | `FUN_000076d8` | C | `src/tasks.c` | 9/9 |
| `0x76f0` | `FUN_000076f0` | C | `src/application_glue.c` | 3/3 |
| `0x76f8` | `vector_15` | C | `src/timers.c` | 53/53 |
| `0x776c` | `FUN_0000776c` | C | `src/timers.c` | 25/25 |
| `0x77b4` | `FUN_000077b4` | C | `src/timers.c` | 4/4 |
| `0x77c0` | `FUN_000077c0` | C | `src/timers.c` | 21/21 |
| `0x77fc` | `FUN_000077fc` | C | `src/timers.c` | 14/14 |
| `0x781c` | `FUN_0000781c` | C | `src/timers.c` | 45/45 |
| `0x7880` | `FUN_00007880` | C | `src/timers.c` | 19/19 |
| `0x78ac` | `FUN_000078ac` | C | `src/application.c` | 31/31 |
| `0x7910` | `FUN_00007910` | C | `src/application.c` | 10/10 |
| `0x7928` | `FUN_00007928` | C | `src/application.c` | 24/24 |
| `0x7974` | `FUN_00007974` | C | `src/application.c` | 9/9 |
| `0x798c` | `FUN_0000798c` | C | `src/mspm0_core.c` | 19/19 |
| `0x79d0` | `FUN_000079d0` | C | `src/mspm0_core.c` | 6/6 |
| `0x79e4` | `vector_11` | C | `target/fault_handlers.c` | 4/4 |
| `0x79f0` | `Reset_Handler` | C | `src/mspm0_core.c` | 28/28 |
| `0x7a50` | `FUN_00007a50` | C | `src/mspm0_core.c` | 1/1 |
| `0x7a54` | `FUN_00007a54` | C | `src/mspm0_core.c` | 8/8 |
| `0x7a68` | `FUN_00007a68` | C | `target/hal_helpers.c` | 17/17 |
| `0x7a90` | `FUN_00007a90` | C | `target/hal_helpers.c` | 21/21 |
| `0x7ac0` | `FUN_00007ac0` | C | `target/hal_helpers.c` | 8/8 |
| `0x7ad4` | `FUN_00007ad4` | C | `target/hal_helpers.c` | 7/7 |
| `0x7ae8` | `FUN_00007ae8` | C | `target/core_helpers.c` | 5/5 |
| `0x7af4` | `FUN_00007af4` | C | `src/flash_controller.c` | 10/10 |
| `0x7b10` | `FUN_00007b10` | C | `src/flash_controller.c` | 17/17 |
| `0x7b44` | `FUN_00007b44` | C | `src/flash_controller.c` | 8/8 |
| `0x7b60` | `FUN_00007b60` | C | `src/flash_controller.c` | 8/8 |
| `0x7b78` | `FUN_00007b78` | C | `src/fault_control.c` | 4/4 |
| `0x7b88` | `FUN_00007b88` | C | `src/fault_control.c` | 5/5 |
| `0x7b9c` | `FUN_00007b9c` | C | `src/fault_control.c` | 9/9 |
| `0x7bb8` | `vector_3` | C | `target/fault_handlers.c` | 5/5 |
| `0x7bcc` | `vector_2` | C | `target/fault_handlers.c` | 5/5 |
| `0x7be0` | `FUN_00007be0` | C | `src/fault_control.c` | 9/9 |
| `0x7bfc` | `FUN_00007bfc` | C | `src/fault_control.c` | 3/3 |
| `0x7c08` | `FUN_00007c08` | C | `src/mspm0_core.c` | 19/19 |
| `0x7c3c` | `FUN_00007c3c` | C | `src/mspm0_core.c` | 8/8 |
| `0x7c54` | `FUN_00007c54` | C | `src/adc.c` | 92/92 |
| `0x7d54` | `FUN_00007d54` | C | `src/adc.c` | 109/109 |
| `0x7e7c` | `FUN_00007e7c` | C | `src/adc.c` | 67/67 |
| `0x7f24` | `FUN_00007f24` | C | `src/adc.c` | 22/22 |
| `0x7f58` | `FUN_00007f58` | C | `src/mspm0_core.c` | 98/98 |
| `0x8054` | `FUN_00008054` | C | `src/mspm0_core.c` | 34/34 |
| `0x80ac` | `FUN_000080ac` | C | `src/mspm0_core.c` | 28/28 |
| `0x80f8` | `FUN_000080f8` | C | `src/mspm0_core.c` | 32/32 |
| `0x8148` | `FUN_00008148` | C | `src/mspm0_core.c` | 69/69 |
| `0x81f8` | `FUN_000081f8` | C | `src/mspm0_core.c` | 36/36 |
| `0x8258` | `vector_17` | C | `src/mspm0_core.c` | 37/37 |
| `0x82b4` | `FUN_000082b4` | C | `src/i2c.c` | 19/19 |
| `0x82f0` | `FUN_000082f0` | C | `src/i2c.c` | 134/134 |
| `0x844c` | `FUN_0000844c` | C | `src/i2c.c` | 180/180 |
| `0x860c` | `FUN_0000860c` | C | `src/i2c.c` | 157/157 |
| `0x8798` | `vector_40` | C | `src/i2c.c` | 23/23 |
| `0x87dc` | `FUN_000087dc` | C | `src/pwm.c` | 88/88 |
| `0x88c0` | `FUN_000088c0` | C | `src/pwm.c` | 34/34 |
| `0x891c` | `FUN_0000891c` | C | `src/uart_hal.c` | 9/9 |
| `0x8938` | `FUN_00008938` | C | `src/uart_hal.c` | 10/10 |
| `0x8954` | `FUN_00008954` | C | `src/uart_hal.c` | 192/192 |
| `0x8b50` | `FUN_00008b50` | C | `src/uart_hal.c` | 85/85 |
| `0x8c34` | `FUN_00008c34` | C | `src/uart.c` | 32/32 |
| `0x8c8c` | `FUN_00008c8c` | C | `src/uart.c` | 39/39 |
| `0x8cf0` | `FUN_00008cf0` | C | `src/uart.c` | 49/49 |
| `0x8d70` | `FUN_00008d70` | C | `src/uart.c` | 51/51 |
| `0x8de4` | `FUN_00008de4` | C | `src/uart.c` | 53/53 |
| `0x8e6c` | `vector_31` | C | `src/application_glue.c` | 4/4 |
| `0x8e7c` | `vector_29` | C | `src/application_glue.c` | 4/4 |
| `0x8e8c` | `FUN_00008e8c` | C | `src/logging.c` | 95/95 |
| `0x8f88` | `FUN_00008f88` | C | `target/format_wrappers.c` | 10/10 |
| `0x8fa0` | `FUN_00008fa0` | C | `target/format_wrappers.c` | 12/12 |
| `0x8fc0` | `FUN_00008fc0` | C | `src/application_glue.c` | 3/3 |
| `0x8fcc` | `FUN_00008fcc` | C | `src/format.c` | 34/34 |
| `0x9012` | `FUN_00009012` | C | `target/callback_helpers.c` | 10/10 |
| `0x9026` | `FUN_00009026` | C | `target/callback_helpers.c` | 1/1 |
| `0x9028` | `FUN_00009028` | C | `src/format.c` | 8/8 |
| `0x9038` | `FUN_00009038` | C | `src/format.c` | 277/277 |
| `0x92ac` | `FUN_000092ac` | C | `src/format.c` | 30/30 |
| `0x92f4` | `FUN_000092f4` | C | `target/format_wrappers.c` | 10/10 |
| `0x930c` | `FUN_0000930c` | C | `target/hal_helpers.c` | 26/26 |
| `0x934c` | `FUN_0000934c` | C | `target/hal_helpers.c` | 18/18 |
| `0x9374` | `FUN_00009374` | C | `target/hal_helpers.c` | 19/19 |
| `0x93a0` | `FUN_000093a0` | C | `target/hal_helpers.c` | 20/20 |
| `0x93d0` | `FUN_000093d0` | C | `target/hal_helpers.c` | 17/17 |
| `0x9400` | `FUN_00009400` | C | `src/pwm.c` | 10/10 |
| `0x941c` | `FUN_0000941c` | C | `src/pwm.c` | 6/6 |
| `0x942c` | `FUN_0000942c` | C | `src/pwm.c` | 13/13 |
| `0x9450` | `FUN_00009450` | C | `src/pwm.c` | 11/11 |
| `0x9470` | `FUN_00009470` | C | `src/pwm.c` | 14/14 |
| `0x948c` | `FUN_0000948c` | C | `src/pwm.c` | 144/144 |
| `0x95f0` | `FUN_000095f0` | C | `src/uart_hal.c` | 31/31 |
| `0x9638` | `FUN_00009638` | C | `src/uart_hal.c` | 7/7 |
| `0x964c` | `FUN_0000964c` | C | `target/hal_helpers.c` | 10/10 |
| `0x9664` | `FUN_00009664` | C | `target/hal_helpers.c` | 15/15 |
| `0x9688` | `FUN_00009688` | C | `target/hal_helpers.c` | 7/7 |
| `0x969c` | `FUN_0000969c` | C | `target/runtime_support.c` | 6/6 |
| `0x96aa` | `FUN_000096aa` | C | `target/runtime_support.c` | 5/5 |
| `0x96b8` | `FUN_000096b8` | C | `target/runtime_support.c` | 7/11 |
| `0x96d4` | `FUN_000096d4` | C | `src/application.c` | 22/27 |
| `0x971c` | `FUN_0000971c` | C | `target/runtime_support.c` | 6/6 |
| `0x972c` | `FUN_0000972c` | C | `src/runtime_memory.c` | 14/14 |
| `0x9748` | `FUN_00009748` | C | `src/runtime_memory.c` | 9/9 |
| `0x975a` | `FUN_0000975a` | C | `src/runtime_memory.c` | 8/8 |
| `0x976c` | `FUN_0000976c` | C | `target/runtime_scan_abi.S` | 49/49 |
| `0x97d4` | `FUN_000097d4` | C | `target/runtime_scan_wrappers.c` | 34/34 |
| `0x9824` | `__seofread` | C | `target/runtime_scan_wrappers.c` | 2/2 |
| `0x9828` | `FUN_00009828` | C | `src/runtime_memory.c` | 14/14 |
| `0x9844` | `FUN_00009844` | C | `target/runtime_scan_wrappers.c` | 35/35 |
| `0x9890` | `FUN_00009890` | C | `src/runtime_memory.c` | 18/18 |
| `0x98b4` | `FUN_000098b4` | C | `src/runtime_memory.c` | 20/20 |
| `0x98dc` | `FUN_000098dc` | C | `src/runtime_memory.c` | 17/17 |
| `0x9904` | `FUN_00009904` | C | `target/runtime_scan_wrappers.c` | 135/135 |
| `0x9a20` | `FUN_00009a20` | C | `target/runtime_scan_wrappers.c` | 3/3 |
| `0x9a28` | `FUN_00009a28` | C | `target/runtime_scan_wrappers.c` | 8/8 |
| `0x9a40` | `FUN_00009a40` | C | `target/runtime_support.c` | 8/8 |
| `0x9a54` | `FUN_00009a54` | C | `target/runtime_support.c` | 3/3 |
| `0x9a60` | `FUN_00009a60` | C | `target/runtime_stdio.c` | 90/90 |
| `0x9b24` | `FUN_00009b24` | C | `target/runtime_scan_abi.S` | 231/238 |
| `0x9d24` | `FUN_00009d24` | C | `target/runtime_stdio.c` | 59/59 |
| `0x9d9c` | `FUN_00009d9c` | C | `target/runtime_stdio.c` | 30/30 |
| `0x9ddc` | `FUN_00009ddc` | C | `target/runtime_scan.c` | 322/329 |
| `0xa0d4` | `FUN_0000a0d4` | C | `target/runtime_stdio.c` | 111/111 |
| `0xa1b4` | `FUN_0000a1b4` | C | `target/runtime_stdio.c` | 244/244 |
| `0xa3d8` | `FUN_0000a3d8` | C | `target/runtime_scan.c` | 92/92 |
| `0xa494` | `FUN_0000a494` | C | `target/runtime_scan.c` | 245/245 |
| `0xa69c` | `FUN_0000a69c` | C | `target/runtime_scan.c` | 60/60 |
| `0xa714` | `FUN_0000a714` | C | `target/runtime_stdio.c` | 133/133 |
| `0xa828` | `FUN_0000a828` | C | `target/runtime_support.c` | 3/3 |
| `0xa830` | `FUN_0000a830` | C | `target/runtime_stdio.c` | 53/53 |
| `0xa8ac` | `FUN_0000a8ac` | C | `target/runtime_support.c` | 1/1 |
| `0xa8ae` | `FUN_0000a8ae` | C | `target/runtime_support.c` | 1/1 |
| `0xa8b0` | `FUN_0000a8b0` | C | `src/runtime_memory.c` | 11/11 |
| `0xa8c6` | `FUN_0000a8c6` | C | `target/runtime_support.c` | 19/19 |
| `0xa8ec` | `FUN_0000a8ec` | C | `target/runtime_heap.c` | 69/69 |
| `0xa980` | `FUN_0000a980` | C | `target/runtime_heap.c` | 84/84 |
| `0xaa3c` | `FUN_0000aa3c` | C | `target/runtime_heap.c` | 32/32 |
| `0xaa88` | `FUN_0000aa88` | C | `target/runtime_heap.c` | 14/14 |
| `0xaaac` | `FUN_0000aaac` | C | `target/runtime_heap.c` | 4/4 |
| `0xaabc` | `FUN_0000aabc` | C | `target/runtime_heap.c` | 4/4 |
| `0xaacc` | `FUN_0000aacc` | C | `target/runtime_heap.c` | 8/8 |
| `0xaae0` | `FUN_0000aae0` | C | `src/flash_controller.c` | 5/5 |
