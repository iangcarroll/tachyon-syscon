# Original-ABI power manager

`target/power_manager_target.c` implements 21 entries from `0x4c50` through `0x5274` with the public target interfaces in `include/power_manager_target.h`. It uses direct fixed-layout RAM, callable target dependencies, source-backed callback addresses, and the original logging/assertion contracts. It does not invoke the older host power-manager adapter.

| Original | Symbol suffix after `syscon_target_power_` |
|---|---|
| `0x4c50` | `measure` |
| `0x4ca8`, `0x4d00`, `0x4d9c` | `battery_route`, `vbus_route`, `header_route` |
| `0x4d58`, `0x4df4`, `0x4ec4` | `battery_id`, `ntc`, `boost` |
| `0x4d68`, `0x4e04`, `0x4ed4`, `0x5264` | `battery_id_set`, `ntc_set`, `boost_set`, `battery_sense_set` |
| `0x4e34`, `0x5048`, `0x4ee0` | `battery_route_set`, `vbus_route_set`, `header_route_set` |
| `0x4fd0`, `0x5004` | `header_default`, `usb_isolate` |
| `0x50f4`, `0x5148` | `usb_release_callback`, `usb_assert_callback` |
| `0x517c`, `0x51c0` | `shutdown_busy`, `shutdown_request` |
| `0x5274` | `battery_detect` |

Measurement truncates the ADC argument to 16 bits but compares the full original pin argument to select the scale byte from ROM table `0xcd6f`. A zero sample is retried once. The product wraps at 32 bits. Routing getters read both GPIOs in order, return the original three states, and assert on contradictory or nonboolean combinations. Boolean getters normalize any nonzero GPIO result, including negative status bits.

Simple setters preserve the underlying GPIO write status, even where the decompiler inferred `void`. This matters to battery detection and USB callback logging. USB isolation performs both writes and returns their wrapped sum. Boost passes the complete input value; other simple controls normalize it to boolean.

The NTC/route diagnostic name tables are real target RAM at `0x20000090`, `0x20000078`, and `0x20000084`. Input indices are not prevalidated. Address calculation wraps, pointer reads can fault, and invalid selector values retain the original switching/fallthrough/assertion behavior. Tests exercise indices that wrap back into mapped memory, read nearby memory, or fault. GPIO and logger dependency callbacks may change tables/state; the source retains the subsequent original reload order.

Route setters preserve defined R0/R1 return pairs. Battery and VBUS setters return R0 zero with R1 equal to the incoming selector on the unchanged path, or the target-name pointer on the changed path. Header routing returns R0 zero and R1 equal to its input selector. These interfaces use `uint64_t`; ordinary callers may explicitly use the low word. Header routing keeps voltage diagnostics, two versus three selector rereads, and final assertion order.

USB recovery state lives at active byte `0x20000370` and low/high timestamp words `0x20000378`/`0x2000037c`. The busy check returns a nonzero active byte unchanged. Otherwise it reads both timestamp words, calls the clock, rereads both words, and performs wrapped 64-bit elapsed-time comparison against 2000. The release callback writes low then high time, clears active, and logs the cooldown. The request validates busy state, signed voltage and boost state, sets active/clears the timestamp, then submits three actions: assert USB isolation, delay 250 ms, release USB isolation. The C action array contains addresses of the reconstructed callbacks; comparison normalizes those addresses to original `0x5149`/`0x50f5`. Submission rejection logs before clearing active and returns -1.

Battery detection preserves signed voltage comparisons, the wrapped `ntc - 400` range test, ordered route/NTC/sense changes, GPIO failure diagnostics, retained battery update, final NTC restoration and return type.

## Dependencies and evidence

Dependencies are the source-reconstructed pin wrappers `syscon_target_pin_read/write`, ADC millivolts, timer/clock, scheduler, retained battery setter, logger, assertion and string helper. `tools/power_manager_target_oracle.py` compiles these manager bodies and `src/runtime_memory.c` for Cortex-M0+, without an installed runtime library or original executable fallback. Unit comparisons place explicit result/error/mutation boundaries at hardware-facing dependencies. They compare ordered RAM access, ABI return values, logger arguments including stack variadic arguments, assertions, state and effects. ROM strings and scale bytes remain fixed original-data dependencies in this relocated harness.

The integrated build additionally links `target/tasks_target.c` and `target/retained_target.c`. Original and replacement scheduler submission/polling, callback dispatch, recovery callbacks, battery retention and retained-register writes all execute actual ARM instructions. Callback pointer locations are the only normalized state/trace values; external clocks, ADC samples, pin effects, logger and assertion remain explicit comparison boundaries. The tests run ordinary and 32-bit-wrap timestamps, all task-slot occupancy combinations, exhaustion rollback, cooldowns, voltage thresholds, stuck outputs, invalid table indices, dependency mutations and terminal interruption before each observable effect in the battery-detection path.

This integration exposed two corrected differences in the shared scheduler: a redundant second read of slot zero's active byte during submission, and an omitted interval argument in the delay-completion `%d` log. The integrated read-order and variadic logger checks regress both defects. Existing scheduling and power-key target suites were rerun after the corrections.

The checkpoint passed **63 groups in 8.79 seconds**, comprising **12 manager groups plus scheduling/power-key regressions**. The manager comparisons exercised **634/649 identified original instructions**. Fifteen missing instructions are explicitly accounted for:

- Seven instructions at `0x4ce8`, `0x4cea`, `0x4d40`, `0x4d42`, `0x4ddc`, `0x4dde`, and `0x50be` follow calls to the nonreturning assertion body.
- Eight instructions at `0x5290..0x5296` and `0x52d2..0x52d8` log negative returns from `0x4e34`. That internal function always returns R0 zero on every returning path, so those two guards cannot be entered through its actual implementation. The C retains the conditional checks; tests do not fabricate an internal return to inflate instruction counts.

`analysis/power-manager-target-reference-coverage.json` records the combined run; `analysis/power-manager-target-mapping.json` supplies per-entry mapping. Global input stability is false because the unrelated `tools/config_target_counterexample.py` changed concurrently; manager/scheduler sources and their test inputs were unchanged. The report's aggregate hook set includes dependencies from the scheduling and power-key regression suites, not only this manager harness.

This evidence does not establish exhaustive formal equivalence, exact emitted bytes, private stack-alias equivalence, physical voltage settling, electrical routing safety, or a flash-ready firmware image. The integrated run proves behavior under its declared dependency inputs, not physical board behavior.
