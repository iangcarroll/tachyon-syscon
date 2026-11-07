# Power-key behavior

Reconstructed six routines: edge callback `0x570c`, periodic sampling `0x5740`,
debounce callback `0x5844`, callback registration `0x5908`, and mode selection
`0x591c`, and outer GPIO/timer initialization `0x5970`. Source:
`src/power_key.c`; tests: `tests/test_power_key.py`.

The state preserves the three 12-byte threshold records at original RAM
`0x200000b4`, mode/event bytes at `0x200000d8`, and counter/callback/pin state
at `0x20000390`. The host representation joins those two regions explicitly;
it is not yet linked at the target firmware's RAM addresses.

The edge callback disables GPIO edge notification and schedules a 10 ms debounce
callback. The debounce callback selects the long-press threshold from EDL or
shutdown configuration, adds a second boundary 5 seconds later, and starts the
10 ms sampler. Depending on mode, it also forwards the button level to SG560D
control. Sampling tracks press duration, emits threshold events, and treats a
release as finished only after more than 200 ms. In mode zero, holding the key
for more than 5,999 ms forces the release operation once. These are literal
compatibility behaviors, including uint32 counter wrap and byte event wrap.

Differential tests execute the original Thumb routines and compare both complete
state regions and ordered environment-call traces. They cover short/long holds,
release boundaries, configuration-dependent thresholds, irregular threshold
tables, non-boolean modes/levels, integer wrap, and callback-driven state mutation.

Dependencies remain explicit hooks: GPIO read/interrupt configuration, timer
registration, SG560D button forwarding, configuration getters and diagnostics.
The tests do not validate electrical debounce, actual interrupt timing, or SG560D
power-state effects. Initialization compares the 12-byte GPIO configuration and
call order through mode selection and timer initialization. The callback dispatch mechanism uses original 32-bit addresses
through a host adapter; native ARM linking and exact machine-code reproduction
are still pending. Initial validation: two differential tests passed.
