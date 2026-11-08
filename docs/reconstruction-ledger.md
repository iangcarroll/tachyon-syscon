# Firmware source inventory

Run `make ledger` to generate `build/ledger/reconstruction-ledger.md` and its JSON companion. The table maps each statically identified original function to its current production source, test entry points and proof status. Legacy host models are recorded separately; they are never presented as firmware build inputs. Generated reports stay out of Git.

The index checks mappings against the physical builder's source list and rejects missing source or test files. It does not prove that every function is linked, exercised or equivalent, or that the original static inventory is exhaustive. Test mappings identify where to validate behavior; they do not imply a passing run. Formal proof and hardware results require their own scoped evidence.

To attach one test invocation's result, use:

```sh
.venv/bin/python tools/reconstruction_ledger.py --checkpoint build/quick-test-coverage.json
```

The report compares the invocation's input hashes with the current tree. Changed inputs are marked `stale`, absent hashes are `unverified_inputs`, and a failed test invocation remains `failed`. A passing quick-test or partial invocation is never promoted to full-suite coverage. Without `--checkpoint`, no current test result is claimed.

CI uploads this inventory in the `local-emulation-evidence-core` artifact, with the core suite's checkpoint explicitly identified. The other suites have their own artifacts. See [MCU validation](mcu-emulator.md), the [source guide](../src/README.md), and the [hardware record](debug-probe.md#controlled-replacement-round-trip) for their distinct scopes.
