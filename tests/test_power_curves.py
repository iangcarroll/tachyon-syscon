"""Time-sequenced power subsystem comparisons, not boot or battery chemistry.

Real SG560D, power-manager, policy, ADC conversion, logger and runtime bodies
execute in original/rebuilt ARM. Explicit ports model clock, GPIO/expander,
UART, retained battery state and task submission; ADC samples are constructed.
Private subsystem state is initialized directly where a prior ON state is needed.
"""
import gc
import struct

import pytest
from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_READ

import build_runtime_scan_image as runtime
from sg560d_target_oracle import Pair as ModemPair, ENTRIES as MODEM_ENTRIES, DEPENDENCIES, AssertionBoundary
from power_manager_target_oracle import ENTRIES as POWER_ENTRIES
from power_policy_target_oracle import MAPPINGS as POLICY_ENTRIES

# All these formerly abstract SG dependencies execute their real target bodies.
INTEGRATED = {a for a in DEPENDENCIES if a in POWER_ENTRIES or a in POLICY_ENTRIES or a == 0x7d54}
EXTRA_PORTS = {
    0x3620: ('syscon_target_pin_read', 1),
    0x5ad4: ('syscon_target_retained_set_battery', 1),
    0x5af0: ('syscon_target_retained_battery', 0),
    0x7ae8: ('syscon_cycle_delay', 1),
}
ADC_CHANNEL = {12: 5, 13: 3, 14: 2, 15: 9, 16: 1, 23: 8}
SCALE = {12: 3, 13: 3, 14: 3, 15: 2, 16: 8, 23: 1}


@pytest.fixture(scope='module')
def curve_elf(tmp_path_factory):
    out = tmp_path_factory.mktemp('power-curves')
    ports = {address: spec for address, spec in DEPENDENCIES.items() if address not in INTEGRATED}
    ports.update(EXTRA_PORTS)
    traps = out/'curve_ports.S'
    traps.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global {name}\n.type {name},%function\n.thumb_func\n{name}:\n bkpt #0\n bx lr\n'
        for name, _ in ports.values()))
    old = runtime.SOURCES
    try:
        runtime.SOURCES = old + ['src/runtime/format.c', 'src/logging/logger_target.c','src/logging/logger_state.c', 'src/logging/logger_target_abi.S',
            'src/drivers/hal_helpers.c', 'src/modem/sg560d_target.c','src/modem/modem_state.c', 'src/power/power_manager_target.c',
            'src/power/power_policy_target.c','src/power/power_state.c', 'src/drivers/adc_target.c', str(traps)]
        return runtime.build(out)
    finally:
        runtime.SOURCES = old


@pytest.fixture(scope='module', autouse=True)
def retain_engines():
    gc.collect()
    owners = []
    CurvePair.owners = owners
    yield
    CurvePair.owners = None
    owners.clear()
    gc.collect()


class CurvePair(ModemPair):
    def __init__(self, elf):
        super().__init__(elf, self.environment)
        self.now = 1000
        self.samples = {channel: 0 for channel in range(32)}
        self.samples[11] = 2000
        self.gpio = [{pin: 0 for pin in range(256)} for _ in range(2)]
        self.battery = [0, 0]
        self.automatic = 0
        self.new_revision = 1
        self.stuck = set()
        for i, machine in enumerate(self.cpus):
            for address in INTEGRATED:
                symbol = DEPENDENCIES[address][0]
                del machine.hooks[address if not i else machine.symbols[symbol]&~1]
            for address, (symbol, count) in EXTRA_PORTS.items():
                machine.hooks[address if not i else machine.symbols[symbol]&~1] = (
                    lambda o, index=i, a=address, n=count: self.dependency(index, a, n))
            for base, size in [(0x40004000,0x2000), (0x40030000,0x2000),
                               (0x40401000,0x1000), (0x4055a000,0x1000), (0x41c40000,0x1000)]:
                machine.cpu.mem_map(base,size)
            machine.put(0x40031104,struct.pack('<I',1))
            machine.put(0x41c4003c,struct.pack('<I',2000))
            machine.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.register_access(i))
        # Actual production policy initializes the ADC scale and cold GPIO ports.
        self.call(0x54cc,1)

    def register_access(self, index):
        def access(uc, kind, address, size, value, _):
            if not 0x40000000 <= address < 0x42000000:
                return
            if kind == UC_MEM_READ:
                if address == 0x4055a280:
                    channel = int.from_bytes(uc.mem_read(0x40005180,4),'little') & 31
                    uc.mem_write(address,struct.pack('<I',self.samples[channel]))
                    self.events[index].append(('adc-sample',channel,self.samples[channel]))
                value = int.from_bytes(uc.mem_read(address,size),'little')
            self.events[index].append(('register',kind,address,size,value))
        return access

    def environment(self, address, args):
        i = self.active_cpu
        if address == 0x77b4:return self.now
        if address == 0x3114:return self.automatic
        if address == 0x3194:return self.new_revision
        if address == 0x3620:return self.gpio[i][args[0]]
        if address == 0x364e:
            if args[0] not in self.stuck:self.gpio[i][args[0]]=args[1]
        if address == 0x386c:
            machine=self.cpus[i]
            config=bytes(machine.cpu.mem_read(machine.arg(1),3))
            if config[0]:self.gpio[i][args[0]+25]=config[1]
        if address == 0x5ad4:self.battery[i]=args[0]
        if address == 0x5af0:return self.battery[i]
        return 0

    def call(self, entry, *args, check_return=None):
        self.events=[[],[]]
        if entry in MODEM_ENTRIES:
            result=super().call(entry,*args,check_return=check_return)
        else:
            if entry in POWER_ENTRIES:symbol='syscon_target_power_'+POWER_ENTRIES[entry]
            elif entry in POLICY_ENTRIES:symbol='syscon_target_'+POLICY_ENTRIES[entry]
            elif entry==0x7d54:symbol='syscon_target_adc_temperature'
            else:raise AssertionError(hex(entry))
            self.active_cpu=0;original=self.cpus[0].call(entry,*args,count=2000000)
            self.active_cpu=1;result=self.cpus[1].call(symbol,*args,count=2000000)
            if check_return is None:
                check_return=entry not in (0x559c,0x55b4,0x55dc,0x5694,0x5358)
            if check_return:assert result==original,(hex(entry),result,original)
            assert bytes(self.cpus[0].cpu.mem_read(0x20000000,0x800))==self.normalized_memory(0x20000000,self.cpus[1].read(0x20000000,0x800))
            assert self.events[0]==self.events[1],(hex(entry),self.events)
        assert self.gpio[0]==self.gpio[1]
        assert self.battery[0]==self.battery[1]
        return result

    def curve(self, time, **raw_by_pin):
        self.now=time
        for pin,raw in raw_by_pin.items():self.samples[ADC_CHANNEL[int(pin[1:])]]=raw

    def state(self, offset, size=1):
        return int.from_bytes(self.cpus[0].cpu.mem_read(0x20000000+offset,size),'little')

    def route(self, kind):
        first,second={'battery':(33,34),'header':(40,25),'vbus':(35,26)}[kind]
        a,b=self.gpio[0][first],self.gpio[0][second]
        assert (a,b)!=(1,1)
        return a+2*b

    def writes(self):
        return [event[1] for event in self.events[0] if event[0]==0x364e]


def test_presence_curve_reclassifies_low_battery_through_real_adc_and_ntc_window(curve_elf):
    p=CurvePair(curve_elf)
    rows=[(0,3000,0,1),(100,2275,910,2),(200,2275,911,1),
          (300,1517,2732,1),(400,1517,2733,2),(500,2276,0,1)]
    observed=[]
    for elapsed,battery_raw,ntc_raw,expected in rows:
        p.curve(1000+elapsed,p14=battery_raw,p23=ntc_raw)
        assert p.call(0x5274)==expected
        observed.append(p.battery[0])
        assert p.gpio[0][36]==0  # Real battery NTC restored after every detection.
        sampled=[event[1] for event in p.events[0] if event[0]=='adc-sample']
        assert (8 in sampled)==(battery_raw<2276)
        if battery_raw<2276:
            assert p.route('battery')==0 and p.gpio[0][27]==1
            assert (27,0) in p.writes() and (27,1) in p.writes()
    assert observed==[1,2,1,1,2,1]


def test_header_usb_battery_source_changes_and_low_voltage_diagnostic(curve_elf):
    p=CurvePair(curve_elf)
    # Repeated controlled OFF-state startup checks retain actual routing history.
    # USB -> header external with battery -> generated header output -> no battery.
    rows=[(1000,1282,0,3000,0,(1,2,1)),
          (2000,1281,3416,3000,0,(1,1,2)),
          (3000,1282,3416,3000,0,(1,1,1)),
          (4000,1281,3415,3000,0,(1,2,1)),
          (5000,1282,0,0,0,(2,2,1))]
    for time,usb,header,battery,ntc,expected in rows:
        p.curve(time,p16=usb,p13=header,p14=battery,p23=ntc,p15=0)
        # A disconnected header at detection represents external cable reconfiguration.
        p.call(0x4ee0,0)
        p.call(0x5f30)
        assert (p.route('battery'),p.route('header'),p.route('vbus'))==expected
    assert p.gpio[0][38]==1 and p.gpio[0][36]==1  # DC-DC fake battery/NTC.
    p.curve(6000,p13=3000)
    p.call(0x4ee0,1)  # Low measured voltage logs an error but still routes INPUT.
    assert p.route('header')==1
    assert any(event[0]==0x3af4 and b'voltage' in event[2].lower() for event in p.events[0])


@pytest.mark.parametrize('floor_raw,reason,delay',[(1897,6,10000),(1898,0,30000)])
def test_vph_dip_recovers_then_v18_loss_uses_remembered_minimum(curve_elf,floor_raw,reason,delay):
    p=CurvePair(curve_elf)
    # Prior ON state is an explicit subsystem fixture, not a claimed boot.
    p.put(0x200004f1,b'\x02\x02')
    p.put(0x200004e0,struct.pack('<Q',1000))
    p.call(0x55b4)
    p.curve(1100,p12=3000,p15=2100,p14=3000,p16=1282)
    p.call(0x6a68)
    p.curve(1200,p12=floor_raw)
    p.call(0x6a68)
    assert p.state(0x4f1)==2 and p.call(0x562c)==0
    p.curve(1300,p12=3000)
    p.call(0x6a68)
    assert p.call(0x55c4)==floor_raw*1800//4096*3
    p.curve(1400,p15=1934)
    p.call(0x6a68)
    assert p.call(0x562c)==reason
    assert p.state(0x4f1)==0 and p.state(0x4f2)==1
    assert p.state(0x518,8)==1650 and p.state(0x500,8)==1400+delay
    assert p.state(0x508)==1 and p.state(0x528)==reason


def test_thermal_curve_changes_retry_backoff_and_invalid_calibration_behavior(curve_elf):
    p=CurvePair(curve_elf)
    observed=[]
    for time,raw,temperature,delay in [(1000,2000,300,10000),(2000,1898,499,10000),
                                      (3000,1897,501,120000),(4000,2000,300,10000)]:
        p.now=time;p.samples[11]=raw
        assert p.call(0x7d54)==temperature
        assert p.call(0x62ec,6,0)==delay
        p.call(0x6384,6)
        observed.append(p.state(0x500,8)-time)
        assert p.state(0x508)==1  # Hot temperature delays, not disables, retry.
    assert observed==[10000,10000,120000,10000]
    for machine in p.cpus:machine.put(0x41c4003c,b'\0'*4)
    assert p.call(0x7d54)==0x80000000
    assert p.call(0x62ec,6,0)==10000  # Existing invalid-sensor behavior, not a safety claim.


def test_header_handover_stuck_output_faults_before_claiming_requested_route(curve_elf):
    p=CurvePair(curve_elf)
    p.curve(1000,p13=3500)
    p.call(0x4ee0,0)
    p.stuck={40}
    p.terminal_assert=True
    p.events=[[],[]]
    for i,machine in enumerate(p.cpus):
        p.active_cpu=i
        with pytest.raises(AssertionBoundary):
            machine.call(0x4ee0 if i==0 else 'syscon_target_power_header_route_set',1)
    assert p.events[0]==p.events[1]
    assert p.gpio[0]==p.gpio[1]
    assert p.route('header')==0
    assert (40,1) in p.writes()
    assert [event[1][1] for event in p.events[0] if event[0]==0x2678]==[0x1e6]


def test_usb_insertion_curve_bounce_restarts_five_second_boot_window(curve_elf):
    p=CurvePair(curve_elf)
    p.automatic=1
    observations=[]
    for time,usb_raw,pending,submissions in [
        (1000,1281,0,0), (2000,1282,1,0), (6999,1281,0,0),
        (7000,1282,1,0), (11999,1282,1,0), (12000,1282,0,1),
    ]:
        p.curve(time,p16=usb_raw,p15=0)
        p.call(0x6a68)
        submitted=[event for event in p.events[0] if event[0]==0x7554]
        observations.append(len(submitted))
        assert p.state(0x509)==pending
        assert len(submitted)==submissions
        if submitted:
            # The real poweron routine submitted its real three-action sequence;
            # the external task executor is intentionally outside this test.
            assert submitted[0][1]==(3,)
            assert struct.unpack_from('<II',submitted[0][2])==(0,0x68fd)
    assert observations==[0,0,0,0,0,1]


def test_battery_low_retry_waits_for_external_supply_after_deadline(curve_elf):
    p=CurvePair(curve_elf)
    p.automatic=1
    p.call(0x55dc,3)  # External SoC shutdown-reason delivery is this boundary.
    p.call(0x6384,3)
    assert p.state(0x500,8)==6000
    for time,usb_raw,expected_submissions in [(5999,1281,0),(6000,1281,0),(6500,1282,1)]:
        p.curve(time,p16=usb_raw,p13=0,p15=0)
        p.call(0x6a68)
        assert sum(event[0]==0x7554 for event in p.events[0])==expected_submissions
    assert p.state(0x4f4,4)==1
    assert p.state(0x500,8)==16500  # Next battery-low backoff is10 seconds.
    assert p.state(0x528)==3 and p.state(0x508)==1


def test_depleted_battery_startup_restores_real_battery_fifty_ms_after_v18_rise(curve_elf):
    p=CurvePair(curve_elf)
    p.curve(1000,p14=1517,p23=1800,p16=1282,p13=0,p15=0,p12=3000)
    p.call(0x5f30)
    assert p.battery[0]==1 and p.route('battery')==2
    assert p.state(0x4f8)==1
    p.curve(1100,p15=2100)
    p.call(0x6a68)
    assert p.state(0x4f1)==2 and p.route('battery')==2
    assert p.state(0x4e8,8)==1150
    p.curve(1149)
    p.call(0x6a68)
    assert p.route('battery')==2
    p.curve(1150)
    p.call(0x6a68)
    assert p.route('battery')==1 and p.state(0x4e8,8)==0 and p.state(0x4f8)==0
    switching=[args for args in p.writes() if args[0] in (33,34,36,38)]
    assert switching==[(33,0),(34,0),(36,0),(38,0),(33,1)]
    assert p.gpio[0][36]==p.gpio[0][38]==0
