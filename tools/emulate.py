"""Run syscon at its physical addresses with explicit MCU/board inputs.

No physical connection or flash write is performed. The named synthetic fixture
is reproducible but cannot establish correspondence with a particular board.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from inventory import ROOT,load_image
from unicorn.arm_const import UC_ARM_REG_PC
from mspm0.core import MCU
from mspm0.profile import PROFILE,SVD


def from_scenario(path,image=None):
    path=Path(path);scenario=json.loads(path.read_text())
    def contents(key,length):
        if key+'_image' in scenario:return (path.parent/scenario[key+'_image']).read_bytes()
        if key+'_hex' in scenario:return bytes.fromhex(scenario[key+'_hex'])
        if key+'_fill' in scenario:return bytes([scenario[key+'_fill']])*length
        return None
    m=MCU(load_image() if image is None else image,factory=contents('factory',128),nonmain=contents('nonmain',512),sram=contents('sram',4096))
    m.device.gpio_inputs=int(scenario.get('gpio_inputs',0))
    if 'adc_default_sample' in scenario:m.device.adc_inputs=dict.fromkeys(range(32),scenario['adc_default_sample'])
    m.device.adc_inputs.update({int(k,0):v for k,v in scenario.get('adc_inputs',{}).items()})
    m.device.writeonly_read_fixtures.update({int(k,0):v for k,v in scenario.get('writeonly_read_fixtures',{}).items()})
    if 'reset_cause' in scenario:m.registers[0x400b0220]=scenario['reset_cause']
    if 'i2c_failures' in scenario:m.device.expander.failures.extend(scenario['i2c_failures'])
    if 'adc_stuck' in scenario:m.device.adc_stuck=bool(scenario['adc_stuck'])
    return m,scenario


def send_command(m,command,port=0,interval=100000,settle=300000):
    before=len(m.device.tx[port])
    for byte in command.encode('utf-8')+b'\n':
        m.device.inject_uart(port,bytes([byte]));m.run(interval)
    m.run(settle)
    return bytes(m.device.tx[port][before:])


def report(m,scenario,initial_image,error=None):
    return dict(profile=PROFILE,scenario=scenario,reference_sha256=hashlib.sha256(initial_image).hexdigest(),
        svd_sha256=hashlib.sha256(SVD.read_bytes()).hexdigest(),instructions=m.instructions,
        virtual_ticks=m.cycles,physical_cycle_accuracy=False,pc=hex(m.cpu.reg_read(UC_ARM_REG_PC)),
        stop_reason=m.stop_reason,error=error,application_loop_reached=0x3c9a in m.executed or m.cpu.reg_read(UC_ARM_REG_PC)==0x3c9a,
        executed_original_addresses=[hex(a) for a in sorted(m.executed)],
        exception_events=m.events,uart_hex={str(k):bytes(v).hex() for k,v in m.device.tx.items()},
        recent_mmio=list(m.trace),recent_mmio_capacity=m.trace.maxlen,
        flash_after_sha256=hashlib.sha256(m.flash).hexdigest(),sram_sha256=hashlib.sha256(m.cpu.mem_read(0x20000000,4096)).hexdigest(),
        copied_sram_executor_executed=any(0x20000000<=a<0x2000002c for a in m.executed),
        original_function_hooks=[],physical_hardware_accessed=False,complete_mcu_emulation=False,
        flash_candidate=False,limitations=['Exact board part/silicon revision is not yet verified.',
          'Starts at application reset, not the unavailable factory boot ROM.',
          'Virtual ticks are deterministic instruction quanta, not cycle-accurate execution.',
          'Only documented modeled peripherals and explicitly supplied external inputs are supported.',
          'Passing synthetic scenarios does not prove electrical behavior or physical board safety.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',type=Path,required=True)
    parser.add_argument('--firmware',type=Path)
    parser.add_argument('--instructions',type=int,default=1000000)
    parser.add_argument('--stop-at',type=lambda x:int(x,0))
    parser.add_argument('--command',action='append',default=[])
    parser.add_argument('--report',type=Path,default=ROOT/'analysis/emulation-latest.json')
    args=parser.parse_args();image=args.firmware.read_bytes() if args.firmware else load_image()
    m,scenario=from_scenario(args.scenario,image);error=None
    try:
        m.run(args.instructions,until=args.stop_at)
        for command in args.command:send_command(m,command)
    except Exception as exc:error=dict(type=type(exc).__name__,message=str(exc))
    result=report(m,scenario,image,error);args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    for port,data in m.device.tx.items():args.report.with_suffix(f'.uart{port}.bin').write_bytes(data)
    print(json.dumps({k:result[k] for k in ('instructions','virtual_ticks','pc','stop_reason','error','application_loop_reached','copied_sram_executor_executed')},indent=2))
    print(bytes(m.device.tx[0]).decode('utf-8','replace'))
    print(f'Report: {args.report}')
    if error:raise SystemExit(1)

if __name__=='__main__':main()
