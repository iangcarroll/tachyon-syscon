"""Full original and source main, bounded at loop boundaries without splitting it."""
import random
import re
import struct
import pytest
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE,UcError
from unicorn.arm_const import UC_ARM_REG_R1
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from application_target_oracle import build,DEPENDENCIES
Q=0x200002d8
class Boundary(Exception):pass

@pytest.fixture(scope='module')
def application_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('application'))

class Pair:
    def __init__(self,elf):
        self.cpus=[Oracle(),ArmRebuildOracle(elf)];self.events=[[],[]]
        self.responses={};self.mutations={};self.loops=[0,0];self.limit=None;self.inputs=[]
        for i,cpu in enumerate(self.cpus):
            for address,name,count in DEPENDENCIES:
                entry=address if i==0 else cpu.symbols['syscon_target_'+name]&~1
                cpu.hooks[entry]=lambda machine,i=i,name=name,count=count:self.endpoint(machine,i,name,count)
    def endpoint(self,cpu,i,name,count):
        args=tuple(cpu.arg(j) for j in range(count))
        if name=='fault_stage_set' and args==(2,) and self.limit is not None:
            if self.loops[i]>=self.limit:raise Boundary()
            index=self.loops[i];self.loops[i]+=1
            if index<len(self.inputs):self.inputs[index](cpu)
        if name=='uart_init':args=(args[0],bytes(cpu.cpu.mem_read(args[1],9)))
        if name=='gpio_config':args=(args[0],bytes(cpu.cpu.mem_read(args[1],12)))
        if name=='powerkey_callback':
            expected=0x3a8d if i==0 else cpu.symbols['syscon_target_queue_event']|1
            assert args[0]==expected
            args=('relocated:queue_event',args[1])
        if name=='gpio_attach':
            expected=0x78ad if i==0 else cpu.symbols['syscon_target_wakeup_irq']|1
            assert args[2]==expected
            args=(*args[:2],'relocated:wakeup_irq',args[3])
        if name=='logger':
            fmt=bytes(cpu.cpu.mem_read(args[2],200)).split(b'\0')[0]
            count=len(re.findall(rb'%(?!%)[-+ #0]*[0-9.*]*[hl]*[diuxXscp]',fmt))
            args+=tuple(cpu.arg(j) for j in range(3,3+count))
        self.events[i].append((name,args))
        mutation=self.mutations.get(name)
        if mutation:mutation(cpu,i,args)
        result=self.responses.get(name,0)
        if callable(result):result=result(cpu,i,args)
        if name=='now':cpu.cpu.reg_write(UC_ARM_REG_R1,result>>32)
        return result
    def put(self,address,data):
        for cpu in self.cpus:cpu.put(address,data)
    def equal(self,address,size):assert bytes(self.cpus[0].cpu.mem_read(address,size))==self.cpus[1].read(address,size)
    def call(self,address,symbol,*args,void=True):
        self.events=[[],[]]
        first=self.cpus[0].call(address,*args,count=1000000)
        second=self.cpus[1].call('syscon_target_'+symbol,*args,count=1000000)
        assert self.events[0]==self.events[1],self.events
        if not void:assert first==second,(first,second)
        return first
    def main(self,loops):
        self.events=[[],[]];self.loops=[0,0];self.limit=loops
        for i,cpu in enumerate(self.cpus):
            with pytest.raises(Boundary):cpu.call(0x3b34 if i==0 else 'syscon_target_main',count=1000000)
        assert self.events[0]==self.events[1],self.events
        self.equal(Q,24);self.equal(0x20000680,1);self.equal(0x2000080c,1)


def test_full_main_initialization_reset_modes_failures_and_logs(application_elf):
    p=Pair(application_elf)
    for reset in [0,1,2,6,0xffffffff]:
        for auto in [0,1]:
            for factory in [0,1]:
                for error in [0,1,0xffffffff,0x80000000]:
                    p.put(Q,bytes(24));p.put(0x20000680,b'\0')
                    p.responses=dict(reset_cause=reset,auto_boot=auto,factory_test=factory,
                        ioexpander_init=error,power_policy_init=error,modem_init=error,
                        fault_stage_get=0x1234,reset_cause_name=0xb554,cached_reason=0xf00d,
                        fault_stage_name=0xb539,retained_modem=3,modem_mode_name=0xd1a9,
                        retained_battery=1,retained_boots=123)
                    p.main(0)


def seed_event(event,off=0,pending=0):
    def seed(cpu):
        cpu.put(0x200002d1,bytes([event]));cpu.put(Q,struct.pack('<IIIIB',0x200002d1,4,1,0,0))
        cpu.put(0x200002ec,bytes([pending,off]))
    return seed


def test_full_main_all_key_events_and_shutdown_paths(application_elf):
    p=Pair(application_elf)
    for event in [*range(6),6,255]:
        for off in [0,1,255]:
            for alt in [0,1]:
                for shutdown in [0,1]:
                    p.responses=dict(reset_cause=2,modem_off=off,alt_powerkey=alt,
                        power_shutdown_request=shutdown,tasks_active=0)
                    p.inputs=[seed_event(event,off)];p.main(1)
    for pending in [0,1,255]:
        for active in [0,1,0xffffffff]:
            for factory in [0,1]:
                p.responses=dict(reset_cause=2,tasks_active=active,factory_test=factory)
                p.inputs=[seed_event(1,1,pending)];p.main(1)


def test_full_main_reads_key_state_on_correct_side_of_callbacks(application_elf):
    p=Pair(application_elf)
    for event in range(6):
        for before in [0,1]:
            p.responses=dict(reset_cause=2,alt_powerkey=1,modem_off=1)
            # Event3 must use the off state captured before the callback; events
            # 0/2/4 differ in their reload points. The full loop observes this.
            p.mutations={'alt_powerkey':lambda cpu,i,args:cpu.put(0x200002ed,bytes([1-before]))}
            p.inputs=[seed_event(event,before)];p.main(1)


def test_full_main_multiple_iterations_consume_queue_and_defer_shutdown(application_elf):
    # No re-entry/split tick: all iterations execute one source main invocation.
    p=Pair(application_elf)
    def fill(cpu):
        cpu.put(0x200002d1,bytes([0,1,2,3]));cpu.put(Q,struct.pack('<IIIIB',0x200002d1,4,0,0,1));cpu.put(0x200002ec,b'\0\0')
    p.inputs=[fill];p.responses=dict(reset_cause=2,modem_off=1,alt_powerkey=0,
        tasks_active=lambda cpu,i,args:int(p.loops[i]<4))
    p.main(6)
    p.equal(Q,24)


def test_queue_aliasing_wrap_and_mutable_count_read_order(application_elf):
    p=Pair(application_elf);rng=random.Random(0x3a8c)
    for _ in range(150):
        write=rng.getrandbits(32);read=rng.getrandbits(32);size=rng.choice([0,1,4,0xffffffff])
        for destination in [0x20000800,*range(Q,Q+17)]:
            p.put(Q,struct.pack('<IIIIB',(destination-write)&0xffffffff,size,write,read,0))
            p.call(0x3a8c,'queue_event',rng.getrandbits(32));p.equal(Q,20);p.equal(0x20000800,1)
        p.call(0x3b0c,'queue_count',Q,void=False)
    # Full queue returns before following an invalid buffer.
    p.put(Q,struct.pack('<IIIIB',0x30000000,4,0,0,1));p.call(0x3a8c,'queue_event',7)


def test_wakeup_irq_registration_and_glue_callbacks(application_elf):
    p=Pair(application_elf)
    for off in [0,1,0xffffffff]:
        for level in [0,1,0xffffffff]:
            p.responses=dict(modem_off=off,gpio_read=level)
            p.put(0x20000680,b'\0');p.call(0x78ac,'wakeup_irq',17,0);p.equal(0x20000680,1)
            p.call(0x7974,'wakeup_poll');p.equal(0x20000680,1)
    for enabled in [0,1,0xffffffff]:
        for configured in [0,1,0xffffffff]:
            p.responses=dict(wakeup_enabled=configured);p.call(0x7928,'wakeup_enable',enabled)
    p.call(0x7910,'wakeup_init');p.call(0x4c24,'application_gpio_init')
    p.call(0x4c14,'parser_poll');p.call(0x3af4,'diagnostic_write',0x20000800,7)
    p.responses=dict(now=0x123456789);p.call(0x3610,'timestamp_constructor');p.equal(0x200002cc,4)
    p.call(0x3ec0,'queue_constructor');p.equal(Q,17)


def test_queue_count_observes_repeated_reads_and_full_queue_short_circuit(application_elf):
    p=Pair(application_elf);events=[[],[]]
    for i,cpu in enumerate(p.cpus):
        def record(uc,kind,address,size,value,_,i=i):
            events[i].append((address,size))
            if len(events[i])==3:uc.mem_write(Q+8,struct.pack('<I',0xfffffff0))
        cpu.cpu.hook_add(UC_HOOK_MEM_READ,record,begin=Q,end=Q+16)
    for write,read,full in [(3,1,0),(1,3,0),(0xffffffff,0,0),(0,0,1)]:
        p.put(Q,struct.pack('<IIIIB',0,4,write,read,full));events[0].clear();events[1].clear()
        p.call(0x3b0c,'queue_count',Q,void=False);assert events[0]==events[1]


def test_full_main_queue_disappears_between_checks(application_elf):
    p=Pair(application_elf);counts=[0,0]
    for i,cpu in enumerate(p.cpus):
        def mutate(uc,kind,address,size,value,_,i=i):
            counts[i]+=1
            if counts[i]==2:uc.mem_write(Q+8,bytes(4))
        cpu.cpu.hook_add(UC_HOOK_MEM_READ,mutate,begin=Q+12,end=Q+12)
    p.inputs=[seed_event(0)];p.responses={'reset_cause':2};p.main(1)
    logs=[e for e in p.events[0] if e[0]=='logger']
    assert any(e[1][2]==0xb5d4 for e in logs)
    assert any(e[1][2]==0xb69f for e in logs)


def test_queue_unmapped_buffer_fault_preserves_identical_prior_state(application_elf):
    p=Pair(application_elf);p.put(Q,struct.pack('<IIIIB',0x30000000,4,0,0,0))
    errors=[]
    for i,cpu in enumerate(p.cpus):
        with pytest.raises(UcError) as error:cpu.call(0x3a8c if i==0 else 'syscon_target_queue_event',7)
        errors.append(error.value.errno)
    assert errors[0]==errors[1];p.equal(Q,20)


def test_main_comparison_rejects_changed_compiled_event_handler(application_elf):
    from unicorn import UC_PROT_ALL
    p=Pair(application_elf);p.responses=dict(reset_cause=2,modem_off=0)
    p.inputs=[seed_event(2,0)]
    candidate=p.cpus[1];candidate.cpu.mem_protect(candidate.CODE,0x100000,UC_PROT_ALL)
    # Replace the actual source request-off body by an early return. The full
    # loop must detect its missing shutdown request rather than just booting.
    candidate.put(candidate.symbols['syscon_target_request_off']&~1,b'\x70\x47')
    with pytest.raises(AssertionError):p.main(1)
