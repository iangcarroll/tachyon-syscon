# Static instruction ownership gaps

The refreshed inventory contains 389 identified function entries. Static listing
and ownership accounting is reproduced by `tools/static_inventory_gaps.py` and
recorded with input hashes in `analysis/static-inventory-gaps.json`. Executing an
address, assigning it to a function, and reconstructing its behavior are separate
claims. None of these counts proves exhaustive discovery of the image.

## Corrected boundaries

The previous 378-entry inventory omitted ten small arithmetic ABI entry points.
Direct ARM comparisons and instruction review now identify those separately.
The float-multiply body at `0xdb4` also had a computed jump table that Ghidra did
not fully recover. The literal at `0xff8` points to the table at `0xac74`, whose
entries target internal blocks including `0xe2c`. Original executions reached
seven previously unowned instruction addresses at `0xe2c..0xe3a`.

`tools/AnnotateSyscon.java` now explicitly defines the float-multiply body through
`0xff7`, before its literal pool, and registers the ten additional runtime
entries. These changes were applied by rerunning analysis. The arithmetic
reconstruction is independently documented and tested; the correction is no
longer merely a guessed owner in a report. The earlier missing formatter `%p`
block at `0x9256..0x9268` is also assigned to `0x9038`.

The complete runtime comparison suite also reached `0xbc0`, which Ghidra had
incorrectly decoded as a 32-bit ARM instruction. Independent Thumb decoding,
the two 16-entry jump tables at `0xabf4` and `0xac34`, and branches to the
shared return block identify the omitted float-divide code at `0xa94..0xab7`,
`0xae0..0xae1`, and `0xbc0..0xbf7`. Both tables target `0xbc0` for canonical NaN
results. The annotator now clears the bad decoding, explicitly sets Thumb mode,
and includes these 47 instructions in the `0xa24..0xc45` body. The padding at
`0xc46` and literal pool at `0xc48..0xc53` remain outside its code extent.

The refreshed listing has 17,838 instruction addresses, of which 17,745 have a
function owner. The remaining 93 are string data misdecoded as instructions, as
classified in `analysis/static-discovery-audit.json`. The audit also recovered
the four-byte string EOF callback at `0x9824` and registered its two instructions.
The JSON report separately lists unowned addresses exercised by the current
full-suite checkpoint. This closes that listing gap; it does not prove exhaustive
indirect-target or function discovery elsewhere in the image.

## Reproduce

From `/Users/ian/tachyon`:

```sh
syscon-re/.venv/bin/python syscon-re/tools/static_inventory_gaps.py
syscon-re/.venv/bin/python syscon-re/tools/reconstruction_ledger.py
```

The reports hash the static listing/ranges and the exact successful coverage
checkpoint. Original instructions copied into SRAM are tracked separately;
they do not become extra flash entry points in the inventory.
