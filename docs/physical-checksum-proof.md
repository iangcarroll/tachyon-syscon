# Linked checksum proof and caller read ordering

`make proof-physical-checksum` rebuilds the complete physical image and extracts
its actual `syscon_cfg_checksum` symbol. It verifies that the ELF and binary
agree with the build manifest, that the symbol bytes occur at the same address
in the flash image, and that source/build/proof inputs remain unchanged. The
proof is tied to that artifact, rather than a separately optimized host adapter.

The physical function is byte-identical to original entry `0x282c`, although its
entry address is relocated. An independently decoded Thumb interpreter and Z3
compare both executions. They establish termination and every branch direction,
then compare all R0–R14 and NZCV values at every instruction boundary, relative
PC offsets, ordered byte-read addresses and values, and the ordinary return
target. No caller-saved register is silently omitted.

The pointer ranges over every 32-bit value, including wraparound. Each read has
an independent symbolic byte response. Both executions receive the same response
stream, but address equality is a proof obligation, not an assumption. This
covers changing responses without assuming stable SRAM. Under a shared bus
environment, equal request traces and pre-read register states also establish
the relation at every possible first failed read. No load after that failure
is needed to justify the prefix result.

This theorem requires immutable, successfully fetched function instructions,
ordinary Thumb execution outside an IT block, and no asynchronous exceptions.
The return address is an odd LR in `0x101 <= LR < 0xfff8`, matching the existing
ordinary-return contract; arbitrary or exception-return LR values are excluded.
It proves a relation at function boundaries and instruction prefixes. It does
**not** prove that arbitrary pointers see equal bytes in the two complete flash
images, that callers meet the environment relation, that literal saved PCs
match, or that fault handlers, interrupts and physical timing are equivalent.
Exception entry is deliberately not part of the first-read-failure theorem.
The instruction semantics and SMT solver remain trusted components.

`analysis/proof-physical-checksum/` retains the report and physical build
manifest. The commands below regenerate the replayable SMT obligations.
The captured solver files and coverage archives are preserved in the
[complete evidence checkpoint](https://github.com/iangcarroll/tachyon-syscon/tree/b569b1f4f83eb6aec85deddb136d29dd8127ae7b),
also retained by branch `evidence/checksum-proof-b569b1f`. Keeping generated bulk
there lets automated review inspect the source change. Intermediate image
objects remain local.

```sh
make proof-physical-checksum
z3 analysis/proof-physical-checksum/equivalence.smt2
z3 analysis/proof-physical-checksum/obligations.smt2
.venv/bin/python -m pytest -q tests/test_proof_physical_checksum.py
```

## Independent checks and counterexamples

The regression suite executes actual original and rebuilt instructions in
Unicorn with changing byte responses, boundary and wrapping pointers, arbitrary
registers/flags, and every first-read-failure prefix. These are finite checks of
the model and artifact plumbing, separate from the symbolic theorem.

Three negative controls require SAT and replay the witness in Unicorn:

- Increasing the byte-load address by one leaves the checksum unchanged under
  the common response stream, but violates the ordered address trace.
- The earlier `src/config.c` host adapter compiled at `-O2` returns the same
  checksum but leaves different R1–R3 values. Its narrower AAPCS theorem cannot
  substitute for the physical function's full-register theorem.
- Swapping two initial register moves preserves the final registers, flags and
  read trace but changes an intermediate state, which the proof must reject.

Separate negative controls replace the ELF, binary or manifest during proof
generation. Each must invalidate the physical binding. A failed rebuild also
removes any previous successful report, so stale evidence cannot appear current.

## Concrete caller fix

Auditing the six original direct callsites found a separate composition defect.
Original slot validation snapshots the stored key and value checksum bytes, in
that order, before either checksum loop. The reconstructed validator previously
loaded the stored value checksum after the second loop. Mutating that byte at
the first checksum data read made the original accept the slot while the rebuilt
validator rejected it.

The [callsite audit](checksum-callsite-audit.md) records all six original calls
and their memory contexts. The exact pre-fix test ELF, source hash, mutation
trace and verified replay are retained in
`analysis/config-slot-read-order-counterexample/`. That artifact is explicitly
a relocated function-test image, not the separate physical firmware build.

`target/config_read.c` now performs both ordered byte snapshots before the loops.
On a value-checksum failure, the original diagnostic rereads the live stored
value byte; that distinct read is also preserved. Tests compare actual ARM read
traces for SRAM and MAIN slots, mutation of either stored checksum, the live
diagnostic argument, every valid-slot first-read-failure prefix, and a failure
on the diagnostic reread. These function tests do not establish whole-program
interrupt schedules or fault-handler equivalence.

The callable checksum is used by slot validation, slot writing and runtime
compaction. Its inputs include SRAM scratch slots, persistent MAIN sectors and
post-programming readback. To compose the theorem, these callers still need
their own memory/state relation, pointer bounds or failure relation, and
interrupt/timing contracts. The full-firmware equivalence goal remains open.
