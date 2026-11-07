"""Fixed-layout policy compares logs, callbacks, pointer wrap and live state."""
import random
import struct
import re
import pytest
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ,UcError
from unicorn.arm_const import UC_ARM_REG_R1
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from power_policy_target_oracle import build,MAPPINGS,DEPENDENCIES

@pytest.fixture(scope='module')
def policy_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('power-policy'))

class Pair:
    def __init__(self,elf):
        self.cpus=[Oracle(),ArmRebuildOracle(elf)];self.events=[[],[]];self.trace=[[],[]]
        self.responses={};self.mutations={}
        for i,cpu in enumerate(self.cpus):
            for addr,(name,count) in DEPENDENCIES.items():
                entry=addr if i==0 else cpu.symbols['syscon_target_'+name]&~1
                cpu.hooks[entry]=lambda machine,i=i,name=name,count=count:self.endpoint(machine,i,name,count)
            def record(uc,kind,address,size,value,_,i=i):
                if (0x2000005c<=address<0x200000ac or address==0x2000036f or 0x20000380<=address<0x20000390):
                    if kind==UC_MEM_READ:value=int.from_bytes(uc.mem_read(address,size),'little')
                    self.trace[i].append((kind,address,size,value&((1<<(8*size))-1)))
            cpu.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,record)
    def endpoint(self,cpu,i,name,count):
        args=tuple(cpu.arg(j) for j in range(count))
        if name in ['adc_init','ioexpander_configure']:
            args=(args[0],bytes(cpu.cpu.mem_read(args[1],7 if name=='adc_init' else 3)))
        if name in ['logger','mfg_logger','output']:
            start=2 if name=='logger' else 0
            fmt=bytes(cpu.cpu.mem_read(cpu.arg(start),180)).split(b'\0')[0]
            n=len(re.findall(rb'%(?!%)[-+ #0]*[0-9.*]*[hl]*[diuxXscp]',fmt))
            args=tuple(cpu.arg(j) for j in range(start+1+n))
        self.events[i].append((name,args))
        if name in self.mutations:self.mutations[name](cpu,i,args)
        result=self.responses.get(name,0)
        if callable(result):result=result(cpu,i,args)
        if name in ['now','adc_init']:cpu.cpu.reg_write(UC_ARM_REG_R1,result>>32)
        return result
    def put(self,address,data):
        for cpu in self.cpus:cpu.put(address,data)
    def call(self,address,*args):
        self.events=[[],[]];self.trace=[[],[]];results=[]
        for i,cpu in enumerate(self.cpus):
            passed=args
            if address==0x5358:
                if i==0:
                    pointer=0x10041;cpu.hooks[pointer&~1]=lambda machine:self.endpoint(machine,0,'output',1)
                else:pointer=cpu.callback(lambda machine:self.endpoint(machine,1,'output',1))
                passed=(pointer,)
            result=cpu.call(address if i==0 else 'syscon_target_'+MAPPINGS[address],*passed,count=1000000)
            if address==0x5638:result|=cpu.cpu.reg_read(UC_ARM_REG_R1)<<32
            results.append(result)
        if address in [0x54cc,0x55c4,0x562c,0x5638,0x5670,0x567c]:assert results[0]==results[1]
        assert self.events[0]==self.events[1],(hex(address),self.events)
        assert self.trace[0]==self.trace[1],(hex(address),self.trace)
        for start,length in [(0x2000005c,4),(0x2000036f,1),(0x20000380,16)]:
            assert bytes(self.cpus[0].cpu.mem_read(start,length))==self.cpus[1].read(start,length)
        return results[0]


def test_power_report_signed_thresholds_tables_and_callback_mutation(policy_elf):
    p=Pair(policy_elf);rng=random.Random(0x5358)
    for measured in [0,1700,1701,3000,3001,4499,4500,0x7fffffff,0x80000000,0xffffffff]:
        for index in [0,1,2,3,0x3ffffff0,0x40000000]:
            p.responses=dict(power_measure=measured,power_battery_route=index,power_vbus_route=index,
                power_header_route=index,retained_battery=index,power_ntc=index,
                power_battery_id=rng.choice([0,1,2]),power_boost=rng.choice([0,1,255]),pin_read=rng.choice([0,1]))
            p.call(0x5358)
    def mutate(cpu,i,args):cpu.put(0x20000090,struct.pack('<I',0x12345678))
    p.responses={};p.mutations={'output':mutate};p.call(0x5358)


def test_policy_initialization_reuses_mutable_configs_and_warm_report(policy_elf):
    p=Pair(policy_elf)
    for cold in [0,1,0xffffffff]:
        for result in [0,0xffffffff,0x123456789abcdef0]:
            p.responses={'adc_init':result,'ioexpander_configure':result&0xffffffff};p.call(0x54cc,cold)
    def mutate_adc(cpu,i,args):cpu.put(cpu.arg(1)+2,bytes([(args[0]+31)&255]))
    def mutate_pin(cpu,i,args):cpu.put(cpu.arg(1)+2,bytes([(args[0]+47)&255]))
    p.mutations={'adc_init':mutate_adc,'ioexpander_configure':mutate_pin};p.call(0x54cc,1)


def test_minimum_signed_comparison_sentinel_and_full_bit_results(policy_elf):
    p=Pair(policy_elf)
    values=[0,1,0x7ffffffe,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    for current in values:
        for measured in values:
            p.put(0x2000005c,struct.pack('<I',current));p.responses={'power_measure':measured}
            p.call(0x559c);p.call(0x55c4)
    p.call(0x55b4);assert p.call(0x55c4)==0xffffffff


def test_shutdown_reason_logging_wrap_byte_truncation_and_clock_zero(policy_elf):
    p=Pair(policy_elf)
    for reason in [0,1,2,3,255,256,0x3ffffff0,0x40000000,0xffffffff]:
        for now in [0,1,0xffffffff,0x100000001,0xffffffffffffffff]:
            p.put(0x20000380,b'\xff');p.responses={'now':now};p.call(0x55dc,reason)
            p.call(0x562c);p.call(0x5670);p.call(0x567c)


def test_shutdown_elapsed_reloads_timestamp_after_time_callback(policy_elf):
    p=Pair(policy_elf)
    for initial in [0,1,0xffffffff,0x100000000,0xffffffffffffffff]:
        for changed in [0,1,0xffffffffffffffff]:
            for now in [0,1,0xffffffff,0x100000000,0xffffffffffffffff]:
                p.put(0x20000388,struct.pack('<Q',initial));p.responses={'now':now}
                p.mutations={'now':lambda cpu,i,args:cpu.put(0x20000388,struct.pack('<Q',changed))}
                p.call(0x5638)


def test_shutdown_expiry_clock_wrap_and_pre_post_callback_reads(policy_elf):
    p=Pair(policy_elf)
    for reason in [0,1,255]:
        for stale in [0,1,255]:
            for start in [0,1,0xffffffff,0xffffffffffffffff]:
                for delta in [0,299999,300000,0xffffffffffffffff]:
                    p.put(0x2000036f,bytes([reason]));p.put(0x20000380,bytes([stale]));p.put(0x20000388,struct.pack('<Q',start))
                    p.responses={'now':(start+delta)&0xffffffffffffffff};p.call(0x5694)
    def mutate(cpu,i,args):cpu.put(0x2000036f,b'\x02');cpu.put(0x20000388,bytes(8))
    p.mutations={'now':mutate};p.responses={'now':300001}
    p.put(0x2000036f,b'\x01');p.put(0x20000380,b'\0');p.put(0x20000388,struct.pack('<Q',1));p.call(0x5694)


def test_invalid_reason_table_fault_precedes_state_write(policy_elf):
    p=Pair(policy_elf);p.put(0x2000036f,b'\xa5');errors=[]
    for i,cpu in enumerate(p.cpus):
        with pytest.raises(UcError) as error:cpu.call(0x55dc if i==0 else 'syscon_target_shutdown_set',0x04000000)
        errors.append(error.value.errno)
        assert bytes(cpu.cpu.mem_read(0x2000036f,1))==b'\xa5'
    assert errors[0]==errors[1]
