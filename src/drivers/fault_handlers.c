/* Target-only, never call these functions in the host process. */
#include <stdint.h>

static _Noreturn void fault_stop(uint32_t stage)
{
    *(volatile uint32_t *)(uintptr_t)0x400b040c = stage;
    for (;;) {
    }
}

_Noreturn void syscon_default_exception(void)
{
    fault_stop(20);
}
_Noreturn void syscon_hardfault(void)
{
    fault_stop(18);
}
_Noreturn void syscon_nmi(void)
{
    fault_stop(19);
}
