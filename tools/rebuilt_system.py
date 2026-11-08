"""Compare reset and UART sessions at physical addresses, without firmware stubs.

The board inputs are synthetic and the clock uses instruction quanta. Execution
observers never replace a firmware function or alter a register/memory value.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_MSP
from emulate import from_scenario
from inventory import ROOT, load_image

SCENARIO=ROOT/'fixtures/emulator/tachyon-synthetic.json'


def boot(image,scenario=SCENARIO,budget=2000000,observer=None,stack_floor=0x20000820):
    machine,inputs=from_scenario(scenario,image)
    if observer is not None:
        observer(machine)  # Install read-only observers before the first instruction.
    def check_stack(cpu):
        pointer=cpu.reg_read(UC_ARM_REG_MSP)
        if not stack_floor<=pointer<=0x20001000:
            raise AssertionError(f'Stack overlaps allocated state or leaves physical SRAM: {pointer:#x} (floor {stack_floor:#x})')
        return pointer
    observation={'minimum_msp':0x20001000,'main_loop_reached':False}
    pending=False
    def memory(cpu,kind,address,size,value,unused):
        nonlocal pending
        if address==0x400b040c and size==4 and value==2:
            pending=True
    def instruction(cpu,address,size,unused):
        observation['minimum_msp']=min(observation['minimum_msp'],check_stack(cpu))
        if pending:
            observation['main_loop_reached']=True
            machine.stop_reason=('application-loop-stage',2)
            cpu.emu_stop()
    memory_hook=machine.cpu.hook_add(UC_HOOK_MEM_WRITE,memory)
    code_hook=machine.cpu.hook_add(UC_HOOK_CODE,instruction)
    try:machine.run(budget)
    finally:
        machine.cpu.hook_del(memory_hook);machine.cpu.hook_del(code_hook)
    if not observation['main_loop_reached']:
        raise AssertionError(f'Reset did not reach application loop: {machine.stop_reason}')
    machine.boot_observation=observation
    machine.minimum_msp=observation['minimum_msp']
    def stack_guard(cpu,address,size,unused):
        pointer=check_stack(cpu)
        machine.minimum_msp=min(machine.minimum_msp,pointer)
    machine.cpu.hook_add(UC_HOOK_CODE,stack_guard)
    return machine,inputs


def normalized_log(data):
    # Instruction counts differ between binaries; the emulator explicitly does
    # not model physical cycle timings. Normalize only the logger timestamp.
    return re.sub(rb'(?m)^\[\d+\]',b'[TIME]',data)


def command_reply(machine,command,budget=2000000):
    """Pace real UART input and wait for its actual protocol status response."""
    before=len(machine.device.tx[0]);limit=machine.instructions+budget
    for byte in command.encode()+b'\n':
        machine.device.inject_uart(0,bytes([byte]));machine.run(5000)
    while machine.instructions<limit:
        output=bytes(machine.device.tx[0][before:])
        if re.search(rb'(?m)^\[\d+\] \[MFGD\] (PASS|FAIL)\r$',output):return output
        machine.run(min(10000,limit-machine.instructions))
    raise AssertionError(f'UART command did not complete within instruction budget: {command!r}')


def snapshot(machine,image):
    return dict(image_sha256=hashlib.sha256(image).hexdigest(),
        instructions=machine.instructions,boot_observation=machine.boot_observation,
        minimum_msp_during_session=machine.minimum_msp,
        exception_events=machine.events,
        executed_addresses=[hex(a) for a in sorted(machine.executed)],
        uart_hex={str(port):bytes(data).hex() for port,data in machine.device.tx.items()},
        persistent_flash_sha256=hashlib.sha256(machine.flash[0xf800:]).hexdigest(),
        sram_sha256=hashlib.sha256(machine.cpu.mem_read(0x20000000,4096)).hexdigest())


def compare(candidate_image,scenario=SCENARIO,stack_floor=0x20000820):
    images=[load_image(),candidate_image]
    machines=[boot(image,scenario,stack_floor=stack_floor if i else 0x20000820)[0]
              for i,image in enumerate(images)]
    sessions=[]
    for command in ['VERSION','CONFIG_SET emu.key alpha','CONFIG_GET emu.key']:
        outputs=[command_reply(machine,command) for machine in machines]
        if command=='VERSION':
            for output in outputs:assert b'Version=1.0.52\r\n' in output and b'PASS\r\n' in output
        elif command.startswith('CONFIG_GET'):
            for output in outputs:assert b'alpha' in output and b'PASS\r\n' in output
        else:
            for output in outputs:assert b'PASS\r\n' in output
        sessions.append(dict(command=command,original_hex=outputs[0].hex(),rebuilt_hex=outputs[1].hex(),
            equal_after_timestamp_normalization=normalized_log(outputs[0])==normalized_log(outputs[1])))
        assert sessions[-1]['equal_after_timestamp_normalization'],command
    assert machines[0].flash[0xf800:]==machines[1].flash[0xf800:]
    cold=[boot(bytes(machine.flash),scenario,stack_floor=stack_floor if i else 0x20000820)[0]
          for i,machine in enumerate(machines)]
    restored=[command_reply(machine,'CONFIG_GET emu.key') for machine in cold]
    for output in restored:assert b'alpha' in output and b'PASS\r\n' in output
    assert normalized_log(restored[0])==normalized_log(restored[1])
    for before,after in zip(machines,cold):assert before.flash[:0xf800]==after.flash[:0xf800]
    return dict(scenario=json.loads(Path(scenario).read_text()),
        original=snapshot(machines[0],images[0]),rebuilt=snapshot(machines[1],images[1]),
        sessions=sessions,persistent_flash_equal=True,fresh_boot_readback_hex=[output.hex() for output in restored],
        firmware_function_replacements=[],physical_hardware_accessed=False,
        whole_firmware_equivalence=False,physical_cycle_accuracy=False,
        note='Complete source image reset, IRQ/UART commands and fresh-boot persistence in the explicit synthetic MCU environment; finite scenarios, not universal equivalence.')


def candidate_stack_floor(path):
    """Trust a layout bound only when its manifest matches these image bytes."""
    path=Path(path)
    manifest=json.loads(path.with_name('manifest.json').read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['binary_sha256']:
        raise ValueError('Firmware does not match the layout manifest')
    floor=manifest['layout_audit']['stack_floor_address']
    if not isinstance(floor,int) or not 0x20000000<floor<0x20001000:
        raise ValueError('Layout manifest has an invalid SRAM stack floor')
    return floor


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware',type=Path,default=ROOT/'build/physical-firmware/firmware.bin')
    parser.add_argument('--report',type=Path,default=ROOT/'build/rebuilt-system-session.json')
    parser.add_argument('--stack-floor',type=lambda value:int(value,0),
                        help='Explicit SRAM allocation end for an image without a matching build manifest')
    args=parser.parse_args()
    floor=args.stack_floor if args.stack_floor is not None else candidate_stack_floor(args.firmware)
    result=compare(args.firmware.read_bytes(),stack_floor=floor)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(args.report),'persistent_flash_equal':result['persistent_flash_equal'],
        'sessions':[{k:row[k] for k in ('command','equal_after_timestamp_normalization')} for row in result['sessions']]},indent=2))
