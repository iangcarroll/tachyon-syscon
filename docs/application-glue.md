# Application integration helpers

`tests/models/application_glue.c` reconstructs seven small entry points that previously
remained dependency boundaries despite their lower-level implementations existing.

| Original | Replacement | Behavior |
| --- | --- | --- |
| `0x30f0` | `syscon_configuration_init` | Initialize identity store, then runtime store, then reload packed runtime settings |
| `0x4c24` | `syscon_app_gpio_init` | Configure GPIO 10, 9, 24, in order, with the recovered 12-byte configuration |
| `0x74e8` | `syscon_sg560d_direct` | Forward bytes through UART1 buffer transmission |
| `0x76f0` | `syscon_default_action` | Return signed `-1` |
| `0x8e6c`, `0x8e7c` | `syscon_uart_vector` | Forward each UART vector to its configured receive IRQ body |
| `0x8fc0` | `syscon_log_enable` | Store the low input byte at RAM offset `0x80c` |

Six differential test cases in `tests/test_application_glue.py` passed. The
configuration scenarios compare both sectors, operation order and all packed
runtime bytes for success and failures during erase/program. Fatal configuration
failures stop initialization at the explicit host boundary. GPIO initialization
executes the actual original GPIO HAL and compares its full register trace with
the reconstructed HAL. UART tests exercise vector reception, raw forwarding,
empty buffers and binary payloads through the reconstructed UART module.

The store, GPIO and UART models retain their respective documented limits.
Configuration assertions are represented by a host sentinel, not an actual MCU
reset. UART status and GPIO registers are emulated; no electrical transport,
interrupt latency, complete boot sequence or physical power transitions are
validated. These context-taking interfaces are not the final linked target ABI.
