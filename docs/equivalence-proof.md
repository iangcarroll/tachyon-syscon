# Equivalence proof boundary and first solver-checked module

The workspace contains differential tests and an MCU emulator that boots both
the original firmware and a complete source-built image in the physical flash
and 4 KiB SRAM layout. These finite executions are not a universal equivalence
proof. The current integration evidence and remaining obligations are detailed
below.

The first theorem below concerns a separately compiled host adapter. The newer
[physical checksum proof](physical-checksum-proof.md) binds the actual linked
symbol and compares all register/flag states and arbitrary ordered byte reads.
Its broader function contract still requires separate caller and environment
proofs.

## First scoped theorem

`tools/proof_checksum.py` proves a narrow machine-code property for original
`0x282c` and freshly compiled `syscon_checksum31` from `src/config.c`.
The candidate is compiled with `-O2`, producing different register allocation
and different bytes from the original; no original bytes enter the candidate.
The captured C source, candidate ELF, compiler arguments and hashes are retained.

Under the following explicit input contract, Z3 reports **UNSAT** for the
existence of an observable difference:

- The function runs in Thumb state, sequentially, with no interrupt, DMA or
  concurrent memory mutation during the call.
- R0 points to 31 readable bytes wholly inside physical SRAM. The pointer is
  symbolic over `0x20000000..0x20000fe1`; all memory byte values are symbolic.
- LR is an ordinary odd Thumb return address within main flash
  (`0x101..0xfff7`), not an exception-return token. Other incoming general
  registers and NZCV are symbolic.
- Observations are the full R0 return value, return target, preservation of
  R4–R11/SP/LR, and the ordered byte-read addresses and values. Memory is
  unchanged. Caller-saved R1–R3/R12 and output APSR flags are not ABI observations.

This covers every input byte combination and every pointer within that
contract, rather than an input sample. It does **not** cover all actual firmware
calls: flash-resident inputs, call-site preconditions and asynchronous execution
are not established by this theorem.

The interpreter independently decodes the small Thumb instruction subset used
by this module into 32-bit bitvector operations and a symbolic byte-addressed
array. It does not lift a host C implementation or assume that original and
candidate instructions are identical. Loads receive explicit SRAM-safety
obligations; therefore this theorem has no unmodeled MMIO accesses. Stores and
unsupported opcodes are rejected rather than approximated.

Every conditional branch must have exactly one satisfiable direction under the
input contract. Both directions are queried. Thus the loop is not assumed to
run 31 times: the solver establishes each branch, and both executions reach
BX LR after 160 modeled instructions and 31 reads. A symbolic fork, undecided
solver response, escaped control flow or resource limit stops proof generation.
No instruction-limit result is reported as a termination proof.

The proof includes an initial satisfiability check on its contract, 62 memory
safety checks, 124 branch-direction checks, and the final difference query:
188 solver obligations. `equivalence.smt2` reproduces the final query;
`obligations.smt2` and `obligations.json` reproduce every recorded decision.
The report records solver, interpreter, input source, project header and ELF
hashes. Solver version used here is the already-installed Z3 4.16 CLI; no
symbolic-analysis packages were installed.

The formalism follows the Z3 project's documentation for
[fixed-width bitvectors](https://microsoft.github.io/z3guide/docs/theories/Bitvectors/)
and [array select semantics](https://microsoft.github.io/z3guide/docs/theories/Arrays/).
The instruction rules are a small manually audited ARMv6-M model; its trusted
boundary remains explicit. A Z3 UNSAT result proves the generated formula, not
that an arbitrary handwritten ISA model is certified against silicon.

## Deliberate failure and independent execution checks

The negative control changes the captured candidate C operation from XOR to OR
and recompiles it. Its difference query is **SAT**. The solver supplies a
concrete SRAM pointer and 31 bytes, and the test replays those exact values
against the original ARM instructions and the separately compiled candidate
ELF in Unicorn. Both results must match the solver's prediction and differ.
This checks that the pipeline can reject incorrect rebuilt source, rather
than merely emit successful reports.

`tools/tests/test_proof_checksum.py` also compares the subset's general-register and
NZCV semantics with independent Unicorn execution for MOVS, ADDS, EORS, ORRS,
CMP and LDRB, including overflow/sign boundaries. These semantic checks are
finite validation of the trusted interpreter, not a separate universal ISA
proof. Unknown-opcode and data-dependent-branch negative tests require explicit
failure. The four test groups pass; generated test artifacts live in pytest's
temporary directory, while the commands below regenerate persistent evidence.

```sh
.venv/bin/python tools/proof_checksum.py
.venv/bin/python tools/proof_checksum.py --mutant --output analysis/proof-checksum-negative
z3 analysis/proof-checksum/equivalence.smt2
z3 analysis/proof-checksum/obligations.smt2
PYTHONPATH=tools .venv/bin/python -m pytest -q tools/tests/test_proof_checksum.py
```

This is a scoped, solver-checked ABI-function theorem under an explicit model
and contract. It is not an independently certified proof of the complete ARM
ISA, all firmware inputs, physical timing, or whole-image equivalence.

## Target integration and remaining proof obligations

The source-only physical image now links with zero unresolved symbols. It uses
source reset/vector code, constructor calls, fixed-layout initialized data,
source command descriptors and relocated callback tables. Its copied SRAM flash
executor is compiled source. No original executable payload, installed runtime
archive or Python firmware-function replacement enters this image.

The complete image reaches its application loop in the strict 64 KiB flash /
4 KiB SRAM emulator. VERSION, configuration set/get, and configuration readback
after a fresh boot match the original after logger timestamps are normalized;
the persistent sectors match byte-for-byte. This is finite, synthetic-board
execution evidence. The named environment supplies factory/NONMAIN and
write-only register assumptions; it is not an identified board readback.

| Boundary | Current evidence | Remaining proof obligation |
| --- | --- | --- |
| Physical image | Strict layout audit, real reset and IRQ execution, protected config sectors | Full reachability and stack/heap/state separation under every allowed interrupt interleaving |
| Dependency dispatch | All linked application, modem, power, peripheral and runtime dependencies resolve to source | Discharge each call contract and terminal/fault path for the declared input domain |
| ABI and state | Direct target signatures, fixed data layout, ordered memory/MMIO comparisons | Full observable register, pointer, private stack and aliasing relation |
| Code/data references | Audited callback relocations and source command table; only declared original data retained | Arbitrary data reads of old code addresses, corrupted function pointers and exposed return addresses |
| Unsafe input domains | Target logger preserves its exposed frame; config ABI preserves the historical omitted argument; actual assertion paths execute | Missing variadic arguments, corrupted private frames, arbitrary formats and fault continuations beyond tested examples |
| Runtime binding | Single source runtime, no external libc/libgcc fallback; cross-unit type audit | Universal memory, arithmetic, formatting, stream and allocator contracts |
| Observable timing | Real IRQ/exception handling and deterministic instruction-quanta clock | A justified timing relation between different compiled schedules; physical-cycle correspondence is not established |

Historical host-analysis implementations under `src/` still have their own
explicit scope restrictions. They are separate from the direct target modules
used in the physical link. Their status codes and guarded unsupported inputs
must not be mistaken for the current target's terminal behavior.

Relocating functions changes raw pointers and may change printed values or
unsafe continuations. Mapping callback identities in a test is not proof that
those values are always unobservable. Original-address veneers for every entry
have not been implemented. In particular, preserving an exposed numeric saved
return in the logger does not prove arbitrary corrupt returns land in equivalent
code in the physical image.

## What a whole-image proof still needs

A universal claim needs a precise transition-system relation between the final
candidate and original, including initial-state correspondence and permitted
external inputs. Module contracts must be discharged at every reachable call
site. All terminal faults, nonreturning paths, aliasing, invalid-input behavior,
interrupt interleavings and persistent writes must be included or explicitly
excluded from the claim. Path coverage alone cannot discharge these obligations.

The next practical proof extension is a mechanically checked loop invariant or
complete finite path split for a small arithmetic routine, followed by a
memory-writing routine with explicit aliasing and access-trace semantics.
Independent validation of the instruction model must grow with that scope;
unsupported operations must continue to stop the prover. The current checksum
proof cannot be reused to justify unrelated arithmetic, MMIO or concurrency.

The existing MCU model uses deterministic instruction quanta, not physical
cycles. Different compiled instruction schedules can change timer/interrupt
interaction. A proof must either establish the required timing correspondence
or define and justify an observation relation that permits such differences;
silently treating each rebuilt instruction as equivalent elapsed time is not
sufficient. Synthetic factory data and peripheral fixtures also cannot stand
in for an established universal hardware model.

No hardware was accessed, no firmware was flashed, and no whole-image proof is
claimed by these artifacts. The integrated candidate exists; its universal
proof remains outstanding work.

## Approved behavior correction: literal legacy configuration

Historical whole-image testing found that the original interprets a stored `%s` value as a printf format with missing arguments. A numeric saved-return value (`0x2919`) then becomes a data pointer, so relocating code changes the corrupted persisted value. The historical witness remains in `analysis/physical-legacy-percent-s-counterexample.json`.

The maintainable implementation no longer reproduces this bug. It copies legacy keys and values literally, using the existing slot size, padding and checksums. Normal configuration commands still reject `%`. This approved difference removes the assembly argument-frame adapter and reserved compatibility byte; no numerical return address participates in slot serialization. The former compatibility reports are historical, not proofs of the current implementation.

`tests/test_rebuilt_system.py` exercises actual UART compaction and readback, then boots a fresh CPU from the persisted candidate sector. It checks the literal result and keeps the original corruption as a differential witness. Ordinary-value cases still compare original and rebuilt behavior. Neither this correction nor those cases constitute a universal whole-image proof.

## Fixed register-output counterexample

The real UART command `SET_RGB %u:2:3:4:0:` exposed another mismatch that a
fixture printer had hidden: the reference printed `0`, while the source image
printed `47355` (the address of the `R: ` label). `%s` printed an empty string
on the reference and `R: ` on the source. Both completed with PASS. The command
passes its token as a format without arguments, making the previous printer's
caller-saved register outputs observable. Evidence is retained in
`analysis/set-rgb-format-counterexample.json` and
`analysis/set-rgb-register-counterexample.json`.

The root cause spans the UART buffer-write epilogue and logger frame cleanup;
it is not a parsing difference. The original UART writer returns R0=0,
R1=port and R2/R3=length, despite its nominal scalar return signature. Correcting
only the nominal C return value does not preserve this whole-program behavior.
The source UART wrapper now preserves the original 32-byte frame and register
outputs. Logger cleanup preserves the final UART outputs as well. The real UART
regression passes for %u, %s, %p, %d, %x, %c and %3u; direct ABI tests also cover
UART disabled, zero-length, transmitting, and frame-alias cases. No SET_RGB-
specific substitute argument was introduced. This fixes the observed witness;
arbitrary private-frame and corrupted-return behavior is still unproved.
