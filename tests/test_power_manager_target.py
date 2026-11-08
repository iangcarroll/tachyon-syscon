import pytest,struct,itertools,random
from power_manager_target_oracle import Pair,build
@pytest.fixture(scope='module')
def elf(tmp_path_factory):return build(tmp_path_factory.mktemp('power-manager-target'))
def both(p,key,value):
    for e in p.envs:setattr(e,key,value.copy() if isinstance(value,(dict,set)) else value)
def route(p,pins,value):
    for e in p.envs:e.gpio[pins[0]]=int(value==1);e.gpio[pins[1]]=int(value==2)

def test_measure_all_channels_retry_truncation_and_wrapping(elf):
    for pin in list(range(25))+[0x1000c,0xffffffff]:
        for samples in [[0,0],[0,1000],[0xffffffff],[0x80000000],[1234]]:
            p=Pair(elf)
            for e in p.envs:e.adc[pin&65535]=samples.copy()
            p.run(0x4c50,pin)

def test_selector_truth_tables_and_boolean_getters(elf):
    for entry,pins in [(0x4ca8,(33,34)),(0x4d00,(35,26)),(0x4d9c,(40,25))]:
        for a,b in itertools.product([0,1,2,255,0xffffffff],repeat=2):
            p=Pair(elf)
            for e in p.envs:e.gpio[pins[0]]=a;e.gpio[pins[1]]=b
            p.run(entry)
    for entry,pin in [(0x4d58,38),(0x4df4,36),(0x4ec4,37)]:
        p=Pair(elf)
        for value in [0,1,255,0x80000000,0xffffffff]:
            for e in p.envs:e.gpio[pin]=value
            p.run(entry)

def test_setters_status_and_unvalidated_name_indices(elf):
    for entry in [0x4d68,0x4e04,0x4ed4,0x5264,0x5004]:
        for value in [0,1,2,15,0x40000000,0xffffffff,0x10000000]:
            for status in [0,1,0xffffffff,0x80000000]:
                p=Pair(elf);both(p,'write_result',status);p.run(entry,value)

def test_routes_all_transitions_invalid_indices_and_stuck_outputs(elf):
    for entry,pins in [(0x4e34,(33,34)),(0x5048,(35,26)),(0x4ee0,(40,25))]:
        for old,new in itertools.product(range(3),[0,1,2,3,0x40000000,0x10000000,0xffffffff]):
            p=Pair(elf);route(p,pins,old);p.run(entry,new)
        for stuck in [{pins[0]},{pins[1]},set(pins)]:
            p=Pair(elf);route(p,pins,0);both(p,'stuck',stuck);p.run(entry,1);p.run(entry,2)

def test_header_default_and_voltage_logs(elf):
    for old in range(3):
        p=Pair(elf);route(p,(40,25),old);p.run(0x4fd0)
    for sample in [0,1499,1500,0x80000000,0xffffffff]:
        p=Pair(elf)
        for e in p.envs:e.adc[13]=[sample]
        p.run(0x4ee0,1)

def test_usb_reattach_callbacks_cooldown_wrap_and_timestamp_reload(elf):
    for status in [0,1,0xffffffff,0x80000000,0x40000000]:
        p=Pair(elf);both(p,'write_result',status);both(p,'now',0x123456789abcdef0);p.run(0x5148);p.run(0x50f4)
    for active in [0,1,255]:
        for stamp in [0,1,0xffffffff,0xffffffffffffffff]:
            for delta in [0,1999,2000,0xffffffff,0x100000000,0xffffffffffffffff]:
                p=Pair(elf);p.put(0x20000370,bytes([active]));p.put(0x20000378,struct.pack('<Q',stamp));both(p,'now',(stamp+delta)&0xffffffffffffffff);p.run(0x517c)
    p=Pair(elf);p.word(0x20000378,1);both(p,'now',2001)
    def change(o,e,address,args):
        if address==0x77b4:o.put(0x20000378,struct.pack('<Q',2000))
    p.on_call=change;p.run(0x517c)

def test_usb_reattach_request_rejections_success_and_task_failure(elf):
    for active,adc,boost,result in itertools.product([0,1],[562,563,0xffffffff],[0,1],[0,-1]):
        p=Pair(elf);p.put(0x20000370,bytes([active]));both(p,'task_result',result)
        for e in p.envs:e.adc[16]=[adc];e.gpio[37]=boost
        p.run(0x51c0)

def test_battery_probe_thresholds_and_gpio_failures(elf):
    for battery,ntc,status in itertools.product([999,1000,0xffffffff],[0,399,400,1200,1201,0xffffffff],[0,0xffffffff]):
        p=Pair(elf);both(p,'write_result',status)
        for e in p.envs:e.adc[14]=[battery];e.adc[23]=[ntc]
        p.run(0x5274)

@pytest.fixture(scope='module')
def integrated_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('power-manager-integrated'),integrated=True)

def test_usb_recovery_actual_scheduler_callbacks_and_retained_commit(integrated_elf):
    for start in [100,0xffffff80,0x100000080]:
        p=Pair(integrated_elf,integrated=True);p.run(0x7540)
        for e in p.envs:e.gpio[37]=1;e.adc[16]=[1000]
        both(p,'now',start);assert p.run(0x51c0)==('return',0)
        p.run(0x75d8);assert p.envs[0].gpio[32]==1 and p.envs[0].gpio[28]==0
        p.run(0x75d8)
        for elapsed in [249,250,251,2250,2251]:
            both(p,'now',start+elapsed);p.run(0x75d8);p.run(0x517c)
        assert p.envs[0].gpio[32]==0 and p.envs[0].gpio[28]==1
        assert p.candidate.read(0x20000370,1)==b'\0'
    for battery,ntc in [(1000,0),(999,800),(999,1300)]:
        p=Pair(integrated_elf,integrated=True)
        for e in p.envs:e.adc[14]=[battery];e.adc[23]=[ntc]
        p.run(0x5274)
        assert p.candidate.u32(0x400b0404)==p.candidate.read(0x200000db,1)[0]

def test_terminal_dependency_stops_all_later_power_effects(elf):
    p=Pair(elf)
    for e in p.envs:e.adc[14]=[999]
    p.run(0x5274);count=len(p.events[0])
    for cutoff in range(count):
        q=Pair(elf);q.fail_at=cutoff
        for e in q.envs:e.adc[14]=[999]
        assert q.run(0x5274)[0]=='boundary'

def test_task_slot_selection_reads_and_submission_rejection(integrated_elf):
    for first,second in itertools.product([0,1,255],repeat=2):
        p=Pair(integrated_elf,integrated=True);p.run(0x7540)
        p.put(0x2000059c,bytes([first]));p.put(0x20000608,bytes([second]))
        for e in p.envs:e.gpio[37]=1;e.adc[16]=[1000]
        outcome=p.run(0x51c0)
        assert outcome==('return',0xffffffff if first and second else 0)
        reads=[event for event in p.events[0] if event[:2]==('memory',16) and event[2] in (0x2000059c,0x20000608)]
        assert [e[2] for e in reads]==([0x2000059c,0x20000608] if first else [0x2000059c])

def test_callback_mutation_preserves_table_reload_and_gpio_order(elf):
    p=Pair(elf)
    def mutate(o,e,address,args):
        if address==0x364e and args==[34,1]:o.put(0x20000080,struct.pack('<I',0x12345678))
    p.on_call=mutate
    assert p.run(0x4e34,2)==('return',0x12345678<<32)
    p=Pair(elf)
    def change_after_log(o,e,address,args):
        if address==0x8f88 and args[2]==b'Set 5V output':e.stuck.add(25)
    p.on_call=change_after_log
    assert p.run(0x4ee0,2)[0]=='assert'


def test_power_manager_has_no_original_rom_dependency(elf):
    for entry,args in [(0x4c50,(12,)),(0x4e34,(2,)),(0x5048,(2,)),(0x4ee0,(2,)),(0x5274,())]:
        p=Pair(elf)
        p.candidate.put(0xc61f,b'\xa5'*(0xcd7c-0xc61f))
        p.candidate.put(0xae64,b'\xa5'*6)
        for environment in p.envs:
            environment.adc[12]=[1000]
            environment.adc[13]=[1800]
            environment.adc[14]=[900]
            environment.adc[23]=[800]
        p.run(entry,*args)


def test_editing_voltage_scale_changes_only_the_selected_channel(tmp_path,monkeypatch):
    import shutil
    import power_manager_target_oracle as builder
    tree=tmp_path/'source'
    for directory in ('src','include','tests/fixtures/target'):
        shutil.copytree(builder.ROOT/directory,tree/directory)
    source=tree/'src/power/power_manager_target.c'
    text=source.read_text()
    assert text.count('scale[] = {3, 3, 3, 2, 8, 1}')==1
    source.write_text(text.replace('scale[] = {3, 3, 3, 2, 8, 1}',
                                   'scale[] = {4, 3, 3, 2, 8, 1}'))
    monkeypatch.setattr(builder,'ROOT',tree)
    p=Pair(builder.build(tmp_path/'variant'))
    for pin in (12,13,14,15,16,23):
        for environment in p.envs:environment.adc[pin]=[1234]
        original=p.execute(0,0x4c50,(pin,))
        candidate=p.execute(1,0x4c50,(pin,))
        if pin==12:
            assert candidate[0]==original[0]=='return'
            assert candidate[1]>original[1]
        else:assert candidate==original


@pytest.mark.parametrize('initial_route', [1, 2])
@pytest.mark.parametrize('battery_sample', [999, 1000])
def test_battery_probe_routes_are_active_and_not_restored(elf, initial_route, battery_sample):
    p = Pair(elf)
    route(p, (33, 34), initial_route)
    for environment in p.envs:
        # The real measurement code multiplies this ADC reading by three.
        environment.adc[14] = [battery_sample]
        environment.adc[23] = [800]
    assert p.run(0x5274) == ('return', 1)
    for environment in p.envs:
        writes = [(a, b) for address, a, b, _ in environment.trace if address == 0x364e]
        rail_writes = [(pin, value) for pin, value in writes if pin in (33, 34)]
        if battery_sample < 1000:
            # Even a previously connected battery is left disconnected.
            assert (environment.gpio[33], environment.gpio[34]) == (0, 0)
            assert rail_writes[-2:] == [(33, 0), (34, 0)]
            assert environment.gpio[27] == 1  # NTC detector disabled afterward.
        else:
            assert (environment.gpio[33], environment.gpio[34]) == (int(initial_route == 1), int(initial_route == 2))
            assert not rail_writes
        assert environment.gpio[36] == 0  # Battery NTC source restored.


def test_battery_route_failure_reports_success_without_confirming_pins(elf):
    for requested in [0, 2]:
        p = Pair(elf)
        route(p, (33, 34), 1)
        both(p, 'stuck', {33, 34})
        both(p, 'write_result', 0xffffffff)
        outcome, result = p.run(0x4e34, requested)
        assert outcome == 'return' and result & 0xffffffff == 0
        # A fresh getter exposes the actual unchanged route despite success.
        assert p.run(0x4ca8) == ('return', 1)
