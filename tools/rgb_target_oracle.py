"""Original-ABI RGB build with source arithmetic and explicit external sinks."""
from pathlib import Path
import build_arm_test_image as runtime
MAPPINGS={0x5b20:'scale',0x5b48:'flush',0x5b7c:'init',0x5bd4:'brightness',0x5bfc:'pattern',
          0x5c38:'configure',0x5c68:'preset',0x5cac:'tick',0x5dbc:'state',0x5dc8:'get_config',
          0x5df4:'state_name',0x5e0c:'pattern_name',0x5e24:'key_feedback'}
DEPENDENCIES={0x87dc:('pwm_init',1),0x88c0:('pwm_write',2),0x781c:('timer_register',4),
              0x776c:('timer_init',0),0x8f88:('logger',4)}
def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    stubs=destination/'rgb_endpoints.S'
    stubs.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global syscon_target_{name}\n.type syscon_target_{name},%function\n.thumb_func\nsyscon_target_{name}:\n bkpt #0\n bx lr\n'
        for name,_ in DEPENDENCIES.values()))
    old=runtime.SOURCES
    try:
        runtime.SOURCES=['target/rgb_target.c','src/runtime_memory.c',str(stubs)]
        return runtime.build(destination)
    finally:runtime.SOURCES=old
