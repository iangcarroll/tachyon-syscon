"""Target parser + descriptors/runtime, with explicit not-yet-linked handlers."""
from pathlib import Path
import json
import build_runtime_scan_image as runtime
ROOT=Path(__file__).resolve().parents[1]
COMMANDS={int(a,16):n for a,n in json.loads((ROOT/'analysis/command-target-symbols.json').read_text()).items()}
DEPENDENCIES={0x8cf0:'syscon_target_uart_available',0x8de4:'syscon_target_uart_read',
              0x8c34:'syscon_target_uart_put',0x8f88:'syscon_target_logger',0x8fa0:'syscon_target_mfg_logger',
              0x2678:'syscon_target_assert'}
def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    trap=destination/'protocol_endpoints.S';trap.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global {name}\n.type {name},%function\n.thumb_func\n{name}:\n bkpt #0\n bx lr\n'
        for name in [*COMMANDS.values(),*DEPENDENCIES.values()]))
    old=runtime.SOURCES
    try:
        runtime.SOURCES=old+['target/protocol_target.c','target/protocol_state.c','target/command_table_target.c','target/callback_helpers.c',str(trap)]
        return runtime.build(destination)
    finally:runtime.SOURCES=old
