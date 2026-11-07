# Physical checksum callsite and composition audit

Audited original SHA-256:
`5bf027f9655bdabb4870eccee5a39e005a08ce70b8337613672081feecef03f6`.
Audited pre-fix physical ELF SHA-256:
`eb47c94142e5eb6eabeec2ba6c4161cb725753a1747828583db8541b7382eb97`.
Source checksum: `syscon_cfg_checksum` in `target/config_read.c`, physical
entry `0x3a6`, size20. The original `0x282c` body and physical symbol are the
same20 bytes. This identity concerns the actual target function, not the
separate native `src/config.c` helper.

## Six original direct calls and physical counterparts

| Original call | Original caller | Physical call before caller fix | Input memory | Use of result |
|---|---|---|---|---|
| `0x2890` | slot_valid `0x2840` | `0x3da` | slot key31bytes | Compare with previously sampled key checksum |
| `0x28aa` | slot_valid `0x2840` | `0x3f2` | slot+32 value31bytes | Compare with previously sampled value checksum; failure logger receives calculated checksum and a live reread of slot+63 |
| `0x2924` | write_slot `0x28d4` | `0x6bc`, finish_slot | Original-shaped64-byte SRAM stack buffer | Store result byte at slot+31 |
| `0x292e` | write_slot `0x28d4` | `0x6c6`, finish_slot | Stack buffer+32 | Store result byte at slot+63 |
| `0x2b3a` | compact `0x2abc` | `0x51f2` | MAIN slot key | Compare with slot+31 read after checksum |
| `0x2b46` | compact `0x2abc` | `0x5204` | MAIN slot value | Compare with slot+63 read after checksum |

No other direct branch/call to0x282c appears in the original instruction
listing. This is a direct-call inventory; it does not prove absence of arbitrary
computed/corrupted jumps or prove discovery of all original executable bytes.

The two slot_valid calls serve several contexts:

- write_slot calls slot_valid at0x293a on its SRAM buffer before programming;
- write_slot calls it at0x2960 on MAIN flash after all eight programming
  operations complete; a programming failure returns before this readback;
- read_slot calls it at0x2972, ordinarily on an identity/runtime MAIN slot;
- find_slot calls it at0x2a06 (key search) and0x2a3e (indexed lookup).

Normal identity slots are0xf800..0xfbff (16x64); runtime slots are
0xfc00..0xffbf (15x64). The final64-byte runtime-sector tail is excluded by
normal count15. Compaction scans runtime slots14 down through0. Generic entry
arguments permit other addresses; valid SRAM/MAIN provenance must be a caller
precondition, not inferred from the checksum function itself.

## Registers, flags, access contract

For31 successful byte reads yielding values b0..b30 at addresses
`p+i mod2^32`, the checksum's observable exit state is:

- R0 is `b0 xor ... xor b30` (zero-extended byte).
- R1 is b30, R2 and R3 are `p+31 mod2^32`.
- R4..R12, SP and LR are unchanged; PC returns through LR.
- The final CMP compares equal values: N=0,Z=1,C=1,V=0.
- No data writes or stack accesses occur. Exactly31 byte loads occur in order.

The six immediate callers use R0. All conditional branches after the call
are preceded by a new caller CMP; none consumes the checksum's final NZCV.
Original0x2890 overwritesR3 and subsequently replacesR1/R2 before a relevant
use.0x28aa overwritesR2/R3 while preparing its comparison/log; R1 can survive
as caller-visible incidental state on a successful slot_valid return.
0x2924/292e overwriteR3 for their byte stores; later helper calls overwrite
other scratch registers.0x2b3a/2b46 overwriteR3 with the stored checksum and
then replace argument registers for subsequent string processing.

Do not replace the whole-state checksum theorem with an ABI claim that scratch
registers are irrelevant. Original slot_valid and reconstructed slot_valid
have different surrounding prologues/epilogues and can expose different
incidental registers; the checksum theorem alone does not prove those callers
or their missing-variadic-argument consumers equivalent. LR/PC values and
stack-object addresses also need an explicit relocation/composition relation
when comparing different callers, not blanket numeric equality.

## Concrete caller gap found and repaired

Original slot_valid reads both stored checksum bytes before either31-byte
checksum loop. The initial reconstructed C instead read slot+63 after computing
the value checksum. `analysis/config-slot-read-order-counterexample/original-witness.json` records an actual
ARM witness: when slot+63 is changed during the first key checksum data read,
the original returns1 and the old candidate returns0. The complete ordered
read traces differ before that change too.

The authorized fix in `target/config_read.c` uses ordered volatile byte loads
for slot+31 and slot+63 before either checksum. On value-check failure it
preserves the original separate live reread of slot+63 for the diagnostic.
It does not change the checksum body or stable-slot semantics.
`tests/test_config_slot_read_order.py` compares actual original/rebuilt ARM
read traces on SRAM/MAIN, mutations of both stored bytes, changing the live
error byte, every one of68 normal-slot read-fault boundaries, and the final
error-reread boundary. These failures are explicit model endpoints, not claims
about a full hardware HardFault/reset implementation.

Further composition obligations remain: successful readable byte accesses (or
an explicit fault-prefix theorem), correct live slot pointer, controller-ready
MAIN flash, absence or a model of intervening writes/interrupts, and consistent
ordering of other caller loads/stores. The checksum's arbitrary ordered-input
byte theorem can support these obligations but does not discharge them alone.
