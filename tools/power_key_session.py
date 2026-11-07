"""Synthetic whole-image button input with read-only event/output observers."""
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0
from functional_scenarios import PowerTransitions
from rebuilt_system import normalized_log


def exercise_short_press(machine, queue_entry):
    """Release, press for about 120 virtual ticks, then debounce the release.

    Advancing the external clock by one SysTick period between instruction
    slices keeps this bounded. It does not claim physical instruction timing.
    All GPIO handlers, timers, callbacks and main-loop consumers execute their
    own instructions. The queue-entry observer only reads the argument.
    """
    events=[]
    def observe(cpu,address,size,unused):
        if address==queue_entry&~1:
            events.append(cpu.reg_read(UC_ARM_REG_R0))
    hook=machine.cpu.hook_add(UC_HOOK_CODE,observe)
    power=PowerTransitions()
    power_hook=power.attach(machine,None)
    before=len(machine.device.tx[0])
    def settle(ticks):
        for _ in range(ticks):
            assert machine.systick_ctrl&3==3 and machine.systick_load
            machine.advance(machine.systick_load+1)
            machine.run(2000)
    try:
        machine.device.set_gpio_inputs(1<<12,1<<12)
        settle(30)
        machine.device.set_gpio_inputs(0,1<<12)
        settle(120)
        machine.device.set_gpio_inputs(1<<12,1<<12)
        settle(300)
    finally:
        machine.cpu.hook_del(hook)
        machine.cpu.hook_del(power_hook)
    output=normalized_log(bytes(machine.device.tx[0][before:]))
    # Equality alone is insufficient: two broken images emitting no event must
    # fail, and the application must actually consume both queued events.
    assert events==[0,1],events
    assert b'Quick press seen' in output and b'Quick press confirmed' in output
    assert b'PWR-KEY pressed' in output and b'PWR-KEY released' in output
    return dict(events=events,uart=output,power=power.events)
