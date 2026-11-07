import gc
import random
import struct
import pytest
from sg560d_target_oracle import build,Pair,ENTRIES

@pytest.fixture(scope='module',autouse=True)
def own_engines():
    gc.collect();Pair.owners=[]
    yield
    Pair.owners=None;gc.collect()
@pytest.fixture(scope='module')
def elf(tmp_path_factory):return build(tmp_path_factory.mktemp('sg-target'))

def responses(values=None):
    values=values or {}
    def respond(address,args):
        return values.get((address,args),values.get(address,0))&0xffffffffffffffff
    return respond


def test_helper_modes_callbacks_uart_and_pin_config(elf):
    for entry in [0x5e30,0x614c,0x6248,0x6282,0x61b8,0x61d0,0x61f0,0x6210,0x6230,0x6238,0x6240,0x6a28,0x6a48,0x7488,0x74a8,0x74c8]:
        for enabled in [0,1,255]:
            p=Pair(elf);p.put(0x200000ed,bytes([enabled]));p.call(entry)
    p=Pair(elf)
    for mode in list(range(8))+[255,256,257,0xffffffff]:p.call(0x66a0,mode);p.call(0x66bc,mode)
    for pin,value in [(0,0),(8,1),(39,0),(255,0xffffffff),(256,2)]:p.call(0x7468,pin,value)
    p.put(0x20000500,b'raw\0bytes');p.call(0x74e8,0x20000500,9)


def test_retry_temperature_delay_wake_and_schedule(elf):
    for temperature in [-100,499,500,1100]:
        p=Pair(elf,responses({0x7d54:temperature,0x77b4:0xfffffffffffffff0}))
        for reason in range(10):
            for attempts in [0,1,2,3,10,0xffffffff]:p.call(0x62ec,reason,attempts)
        for reason in range(9):p.call(0x6384,reason)
        for seconds in [0,1,0xffffffff,0]:p.call(0x65f0,seconds);p.call(0x6650)


def test_boot_modes_real_internal_calls_and_task_callbacks(elf):
    for entry,args in [(0x6428,()),(0x64a0,()),(0x6520,(0,)),(0x6520,(1,)),(0x65d0,()),(0x65da,()),(0x65e4,())]:
        for busy in [0,1,2,255]:
            for task_result in [-1,0,1]:
                p=Pair(elf,responses({0x7554:task_result}));p.put(0x200004f1,bytes([busy]));p.call(entry,*args)


def test_power_check_source_selection_and_driver_failures(elf):
    rng=random.Random(0x5f30)
    for _ in range(150):
        v={0x5274:rng.choice([0,1,2]),0x4ca8:rng.choice([0,1,2]),0x3194:rng.randrange(2),0x4d9c:rng.randrange(3),
           (0x4c50,(15,)):rng.choice([1699,1700]),(0x4c50,(13,)):rng.choice([4499,4500,4501]),(0x4c50,(14,)):rng.choice([1999,2000,4000]),(0x4c50,(16,)):rng.choice([4499,4500]),
           0x4ee0:rng.choice([0,-1]),0x4e34:rng.choice([0,-1]),0x77b4:10000}
        p=Pair(elf,responses(v));p.call(0x5f30)

@pytest.mark.parametrize('scenario_name',[
    'test_sg560d_power_off_dependency_failures_and_busy_gate',
    'test_sg560d_poll_differential_branch_combinations',
    'test_sg560d_poll_rare_recovery_and_debounce_paths',
    'test_sg560d_poll_multistep_usb_restore_and_rgb_debounce'])
def test_original_scenario_corpus_with_real_internal_calls_and_logger(elf,scenario_name):
    # Reuse input scenarios only; neither implementation nor expected results
    # come from the host adapter. Both paths execute ARM code and actual logger.
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('sg_scenarios',Path(__file__).with_name('test_sg560d.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    p=Pair(elf)
    def bridge(_lib,entry,a=0,b=0,*,initial=None,responses=None,check_return=True):
        p.respond=globals()['responses'](responses)
        p.put(0x20000000,bytes(initial or bytes(4096)));p.put(0x2000080c,b'\1')
        p.events=[[],[]]
        p.call(entry,a,b,check_return=check_return)
        return bytes(p.cpus[0].cpu.mem_read(0x20000000,4096)),p.events[0]
    module.run_comparison=bridge
    getattr(module,scenario_name)(None)


def test_init_and_preparation_with_real_power_check(elf):
    for mode in list(range(7))+[255,256,0xffffffff]:
        for voltage in [0,1699,1700]:
            for keep in [0,1]:
                p=Pair(elf,responses({0x4c50:voltage,0x3150:keep,0x77b4:0x100000001,0x4fd0:-1}))
                p.call(0x6948,mode)
    for entry in [0x6838,0x68a4,0x68fc]:
        for target in [3,5]:
            for voltage in [1699,1700]:
                p=Pair(elf,responses({(0x4c50,(15,)):voltage,0x77b4:0x100000001}))
                p.put(0x200003c4,bytes([target]));p.put(0x200003c8,struct.pack('<I',0xd324 if target==5 else 0xd328))
                p.call(entry)


def test_clock_changes_at_each_read_across_real_modem_calls(elf):
    for base in [0,10000,0xfffffff0,0xfffffffffffffff0]:
        for entry,args in [(0x5f30,()),(0x6384,(3,)),(0x65f0,(2,)),(0x6720,(1,)),(0x6948,(2,)),(0x6a68,())]:
            p=Pair(elf);counts=[0,0]
            values={0x3114:1,0x7d54:499,(0x4c50,(16,)):4500}
            def respond(address,args):
                if address==0x77b4:
                    index=p.active_cpu;counts[index]+=1
                    return (base+counts[index]*17)&0xffffffffffffffff
                return responses(values)(address,args)
            p.respond=respond
            p.put(0x200004f1,b'\0\1');p.put(0x2000050a,b'\1')
            p.put(0x200004e8,struct.pack('<Q',1));p.put(0x20000518,struct.pack('<Q',1))
            p.put(0x20000458,struct.pack('<Q',1));p.put(0x20000530,struct.pack('<I',1))
            p.call(entry,*args)
            assert counts[0]==counts[1]


def test_submitted_boot_actions_execute_reconstructed_callbacks(elf):
    for entry in [0x6428,0x64a0,0x65d0,0x65e4]:
        p=Pair(elf,responses({0x77b4:10000,(0x4c50,(16,)):5000}))
        p.call(entry)
        submitted=[event[2] for event in p.events[0] if event[0]==0x7554][-1]
        for offset in range(0,len(submitted),8):
            kind,argument=struct.unpack_from('<II',submitted,offset)
            if kind==0:p.call(argument&~1)
        assert any(event[0]==0x8054 for event in p.events[0])


def test_logger_suppression_and_uart_error_assertion_ports(elf):
    for enabled in [False,True]:
        for entry,port in [(0x5e30,0x8b50),(0x614c,0x8954)]:
            p=Pair(elf,responses({port:-1}),logging=enabled)
            p.put(0x200000ed,bytes([entry==0x5e30]));p.call(entry)
            assert any(event[0]==0x2678 for event in p.events[0])
        p=Pair(elf,logging=enabled);p.call(0x66bc,5)
        assert any(event[0]==0x3af4 for event in p.events[0])==enabled


def test_negative_control_rejects_incorrect_rebuilt_result(elf):
    p=Pair(elf)
    # Replace rebuilt off() only with `return 0`; original off state returns 1.
    p.cpus[1].cpu.mem_write(p.cpus[1].symbols['syscon_target_modem_off']&~1,b'\0\x20\x70\x47')
    with pytest.raises(AssertionError,match='0x6690'):p.call(0x6690)


def test_future_wake_deadlines_and_unsigned_seconds_truncation(elf):
    p=Pair(elf)
    for now in [0,1,0xffffffff,0xfffffffffffffff0]:
        p.respond=responses({0x77b4:now})
        for deadline in [0,now,(now+1)&0xffffffffffffffff,(now+999)&0xffffffffffffffff,(now+1000)&0xffffffffffffffff,0xffffffffffffffff]:
            p.put(0x20000458,struct.pack('<Q',deadline));p.call(0x6650)


def test_fatal_assertion_stops_both_paths_before_later_actions(elf):
    from sg560d_target_oracle import AssertionBoundary
    for entry,values,enabled in [(0x5e30,{0x8b50:-1},1),(0x614c,{0x8954:-1},0),(0x5f30,{(0x4c50,(15,)):1700},0),(0x5f30,{0x4ca8:1,0x3194:0},0)]:
        p=Pair(elf,responses(values));p.terminal_assert=True;p.put(0x200000ed,bytes([enabled]))
        with pytest.raises(AssertionBoundary):p.cpus[0].call(entry)
        with pytest.raises(AssertionBoundary):p.cpus[1].call('syscon_target_modem_'+ENTRIES[entry])
        assert p.events[0]==p.events[1]
        assert bytes(p.cpus[0].cpu.mem_read(0x20000000,0x800))==p.cpus[1].read(0x20000000,0x800)
        assert p.events[0][-1][0]==0x2678
