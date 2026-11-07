Before-fix ARM slot validation witness. See provenance.json for artifact identity and scope.
From the syscon-re workspace run:
PYTHONPATH=tools .venv/bin/python analysis/config-slot-read-order-counterexample/replay-preserved-elf.py
The replay verifies and uses the preserved ELF, never rebuilding it.
Original-build-and-run.py is historical only: rerunning it against current sources would replace its original build path with fixed code.
The recorded source hash was independently matched by the archived Git HEAD source, and the manifest ELF hash matches the preserved ELF.
This is a relocated test ELF with an explicit adversarial SRAM mutation, not the physical full-image ELF.
