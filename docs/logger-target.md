# Original ARM logger frames and overreads

`target/logger_target.c` and `target/logger_target_abi.S` replace the bounded target adapter with a source-backed implementation of `0x8e8c` and its original variadic wrappers. The host adapter in `src/logging.c` still has its explicit `-2` overlong-prefix boundary; firmware target symbols no longer use that host adapter.

| Original entry | Rebuilt symbol | Existing link alias |
| --- | --- | --- |
| 8e8c | syscon_logger_target_vlog | — |
| 8f88 | syscon_logger_target | syscon_target_logger |
| 8fa0 | syscon_logger_target_mfg | syscon_target_mfg_logger |
| 5edc | syscon_logger_target_sg560d | syscon_target_sg560d_printf |
| 92ac | syscon_logger_target_vformat | — |
| 92f4 | syscon_logger_target_snprintf | syscon_target_snprintf |

C implements the logger control flow, message formatting, colors and truncation. Assembly reserves the original exposed frames and saved-register locations. It contains readable ABI operations and symbolic calls into rebuilt C; no original instruction bytes are embedded as an implementation.

## Why the frame matters

The original `0x8e8c` reserves 368 bytes, including saved r4–r7 and LR. From the bottom of that frame, the prefix begins at offset 24, the short message at 56, and the 256-byte message at 88. The original formats a prefix into only 32 bytes, but passes its **full formatted length** to UART. An overlong tag therefore sends the forced NUL followed by stale message buffers, saved registers, the variadic wrapper's saved arguments, caller memory, or eventually attempts an unmapped read. Clamping that length or returning an error changes original behavior.

The rebuilt target preserves those offsets and frame contents. Variadic wrappers retain their original saved argument placement and 64-bit alignment. The logger frame's saved return bytes reflect the original wrapper continuations (`0x8f97` and `0x8fb3`); only an unchanged continuation is mapped to the relocated rebuilt wrapper when returning. An externally corrupted saved return is honored, including invalid-target faults. This adapter keeps its actual relocated continuation below the exposed frame, rather than overwriting an observable slot. This is semantic ABI reconstruction, not binary identity.

The original logger writes time and tag at offsets 0, 4 and 8, records the argument pointer at offset 16 before each message-format attempt, and writes the ellipsis word at offset 20 only on large-message truncation. These effects are preserved. A positive message length up to 31 uses the short buffer. Other lengths trigger a second formatting pass; a signed nonpositive result sends no message. Larger positive lengths truncate to 255 bytes with `...`, followed by a possible color reset and CRLF. The SG560D wrapper keeps its distinct 128-byte cleared buffer and port 1 output.

## Native formatting and observable faults

The additive `syscon_vformat_target` API in `src/format.c` uses the same reconstructed formatter implementation with native volatile target-byte and target-word loads. Existing host callback APIs and structures are unchanged. This matters because the original loads a variadic argument as a 32-bit word; four byte callbacks produce different access widths and can change boundary faults. Target tests compare argument read order and widths, unaligned pointers and RAM-end accesses.

No output error is substituted for an invalid native pointer. CPU input faults propagate. The explicit UART test endpoint reads the requested bytes and records the partial stream and first unmapped address on an overread; it does not silently truncate the request. The actual UART peripheral transmission and timing remain separate dependencies.

## Validation and dependencies

`tools/logger_target_oracle.py` builds the target with reconstructed formatter, memory, arithmetic and runtime sources, without host libc or archive `libgcc` implementations. Original flash remains readable and non-executable in the candidate CPU. Both CPUs use the same caller SP, initialized private-frame bytes and caller register values. The return sentinel is a common external test address. Tests compare ordered time/color/UART events, complete output bytes and buffer addresses, preserved registers, stack restoration, input-fault address/width, and returned formatter counts. The initial callback-port tests did not compare void logger output registers. The later real-UART tests below explicitly compare R0–R3 because subsequent missing variadic arguments can observe them.

`tests/test_logger_target.py` covers prefix lengths from normal output through stale-frame exposure and the first RAM-boundary fault; signed time extremes; all color levels and changing color settings; message thresholds at 31/32 and 255/256; null destinations; embedded NUL; variadic alignment; overlapping buffers; callback changes to live format and argument bytes; changed saved registers and return addresses; disabled logging; malformed input pointers; native argument-load width/order; and a deliberately broken logger negative control. The fixed tests do not depend on a specific uninitialized stack pattern: both executions receive the same supplied pattern and compare its observed propagation.

`target/format_wrappers.c` now contains only three explicit dependencies: `syscon_target_uart_write`, `syscon_target_now`, and `syscon_target_color`. Its old implementation bodies were removed. The existing ARM image and configuration builders link the new target logger files; legacy target names resolve to assembly aliases. No host logger API was removed.

## Remaining limits

This closes the known target `prefix > 32` refusal and preserves the exposed logger/variadic-wrapper frame, including its unsafe overread behavior. It does not establish full firmware equivalence. The rebuilt formatter's and C body's deeper private frames are not byte-identical to the original. An arbitrary pointer deliberately targeting those deeper internal frames, or a callback corrupting them, can still distinguish the implementations. Relocated execution cannot interpret an arbitrary corrupted return into an unimplemented original-code address; tests cover unchanged mapped continuations and common invalid-address faults. A complete fixed-address image would need a separate audit of that control-flow boundary.

Unicorn's emulated memory/alignment faults are not a substitute for silicon fault/exception validation. Enabled UART output, clock/color queries and asynchronous hardware changes remain explicit environment boundaries. No hardware was contacted and these artifacts are not safe-to-flash evidence.

## Validation checkpoint

The final affected selection passed **64 tests in 21.26 seconds**:

```sh
SYSCON_COVERAGE_OUTPUT=analysis/logger-target-test-instruction-coverage.json \
.venv/bin/python -m pytest tests/test_logger_target.py tests/test_arm_rebuild.py \
  tests/test_format.py tests/test_format_callback.py tests/test_logging.py \
  tests/test_config_helpers.py -q
```

The same selection before the final controller negative-control case passed twice (63 tests in 21.34 and 21.46 seconds). All 191 discovered reference instructions across the six mapped logger/formatter entries were exercised; this is execution coverage, not a proof of every input or path. Mapping and exact input hashes are in `analysis/logger-target-mapping.json` and the scoped coverage report. Concurrent project work may make the report's global input-stability flag false; these are local test results rather than a frozen whole-project release gate.

The local configuration controller test now uses mutable, non-executable flash backing for emulator-API mutations applied during status reads. Its new negative control proves that a direct ARM store is detected and rejected by the test environment, and a separate attempt to execute original flash raises `UC_ERR_FETCH_PROT`. This mapping change is confined to `controller_pair` in `tests/test_config_helpers.py`. The repeated affected-suite passes followed this change; they do not establish the internal cause of the earlier native Unicorn crash. No physical hardware reads, writes or flashing were performed.

## Actual UART return-register preservation

The full-system SET_RGB counterexample exposed two independent differences: the C transmitter lost original R1–R3 outputs, and the logger's C epilogue and assembly LR-remapping cleanup clobbered outputs from its final UART call. The UART now uses its original frame/epilogue adapter. The logger C body prepares CRLF, and its existing assembly frame adapter performs the final UART call after that C body returns. Cleanup saves and restores the actual resulting R0–R3 while remapping only the unchanged saved return address. No SET_RGB token or output value is special-cased. The disabled logger path preserves original level/tag/format/zero outputs.

A new optional `real_uart=True` oracle build links the reconstructed UART ring, ABI adapter, descriptor lookup, and blocking transmitter. Clock/color remain explicit test ports; a small test-only transport binding supplies the diagnostic stage write. Original and reconstructed logger/vlog/MFG/SG calls execute UART MMIO and compare all output registers, transmitted bytes, and SYSCTL stage writes across logger enable, UART disable, and color combinations. Production still uses its concrete interface bindings; the parent's whole-image regression exercises those bindings without endpoint hooks.

The original outer logger/MFG/SG wrapper may replace R3 with its caller return address, exactly as its original epilogue does. Preserving arbitrary missing variadic arguments, every relocated code pointer, or the C body's deeper stack for all possible inputs remains unproven.

The affected UART/logger/ARM-wrapper/diagnostics/SG selection passed **61 tests in 128.63 seconds** after this correction. The separately selected real reset/UART SET_RGB regression and UART register/frame-alias regression passed **2 tests in 32.62 seconds**. These results precede the parent's new canonical-image and full-suite checkpoint.
