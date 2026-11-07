/* Original 0x96d4 for this pinned image: empty preinit, noop init, two ctors. */
#include "application_target.h"
#include "mspm0_core_target.h"
void syscon_target_runtime_init(void){
    syscon_target_hal_noop();
    syscon_target_timestamp_constructor();
    syscon_target_queue_constructor();
}
