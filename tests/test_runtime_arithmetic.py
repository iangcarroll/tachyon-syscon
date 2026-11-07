"""Direct comparisons execute independently rebuilt source, without libgcc.a."""
import itertools,random,struct
import pytest
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_APSR
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle
from build_runtime_arithmetic import build

REGS=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]
CALLEE=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
FLOATS=[0,0x80000000,1,0x80000001,0x007fffff,0x807fffff,0x00800000,0x80800000,0x3f000000,0x3f800000,0xbf800000,0x3f800001,0x3f7fffff,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00000,0x7f800001,0xffc12345,0xff800001,0x4f000000,0x4effffff,0x4f800000,0xcf000000]
DOUBLES=[0,0x8000000000000000,1,0x8000000000000001,0x000fffffffffffff,0x0010000000000000,0x3ff0000000000000,0xbff0000000000000,0x3fefffffffffffff,0x3ff0000000000001,0x7fefffffffffffff,0x7ff0000000000000,0xfff0000000000000,0x7ff8000000000000,0x7ff0000000000001,0xfff8000123456789,0xfff0000000000001,0x41dfffffffc00000,0x41e0000000000000,0x41f0000000000000,0xc1e0000000000000]

def words(value):return value&0xffffffff,value>>32

@pytest.fixture(scope='module')
def arithmetic_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('runtime-arithmetic'))

class Pair:
    def __init__(self,elf):self.original=Oracle();self.arm=ArmRebuildOracle(elf)
    def run(self,entry,symbol,*args,result_words=1):
        markers=[0x12345678+i*0x11111111 for i in range(8)]
        for cpu in (self.original.cpu,self.arm.cpu):
            for reg,val in zip(CALLEE,markers):cpu.reg_write(reg,val)
        self.original.call(entry,*args);self.arm.call(symbol,*args)
        expect=[self.original.cpu.reg_read(reg) for reg in REGS[:result_words]]
        actual=[self.arm.cpu.reg_read(reg) for reg in REGS[:result_words]]
        assert actual==expect,(hex(entry),symbol,[hex(x) for x in args],actual,expect)
        assert [self.arm.cpu.reg_read(reg) for reg in CALLEE]==markers
        return actual

@pytest.mark.parametrize('entry,symbol',[(0x6e8,'__aeabi_fadd'),(0xa24,'__aeabi_fdiv'),(0xdb4,'__aeabi_fmul'),(0x1000,'__aeabi_fsub')])
def test_float_arithmetic_nan_sign_rounding_subnormal_and_random(arithmetic_elf,entry,symbol):
    pair=Pair(arithmetic_elf);rng=random.Random(entry)
    cases=list(itertools.product(FLOATS,repeat=2))+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(900)]
    for a,b in cases:pair.run(entry,symbol,a,b)

@pytest.mark.parametrize('entry,symbol',[(0x14bc,'__aeabi_dadd'),(0x1b34,'__aeabi_dsub')])
def test_double_arithmetic_nan_sign_rounding_subnormal_and_random(arithmetic_elf,entry,symbol):
    pair=Pair(arithmetic_elf);rng=random.Random(entry)
    cases=list(itertools.product(DOUBLES,repeat=2))+[(rng.getrandbits(64),rng.getrandbits(64)) for _ in range(900)]
    for a,b in cases:pair.run(entry,symbol,*words(a),*words(b),result_words=2)

@pytest.mark.parametrize('entry,symbol,double_input,double_output',[(0x135c,'__aeabi_f2iz',False,False),(0x139c,'__aeabi_i2f',False,False),(0x1438,'__aeabi_ui2f',False,False),(0x2258,'__aeabi_d2iz',True,False),(0x22c4,'__aeabi_f2d',False,True),(0x4e4,'syscon_rt_f2u',False,False),(0x514,'syscon_rt_d2u',True,False)])
def test_conversions_boundary_saturation_and_nan(arithmetic_elf,entry,symbol,double_input,double_output):
    pair=Pair(arithmetic_elf);rng=random.Random(entry)
    values=(DOUBLES if double_input else FLOATS)+[rng.getrandbits(64 if double_input else 32) for _ in range(1000)]
    for value in values:pair.run(entry,symbol,*(words(value) if double_input else [value]),result_words=2 if double_output else 1)

@pytest.mark.parametrize('double_input', [False,True])
def test_compare_and_boolean_abi(arithmetic_elf,double_input):
    pair=Pair(arithmetic_elf);rng=random.Random(0xc54+double_input)
    entries=([(0x2424,'dne'),(0x24a8,'dcmp_low'),(0x2574,'dcmp_high'),(0x2374,'d_eq'),(0x2380,'d_lt'),(0x2394,'d_le'),(0x23a8,'d_gt'),(0x23bc,'d_ge')] if double_input else [(0xc54,'fne'),(0xca0,'fcmp_low'),(0xd2c,'fcmp_high'),(0x3ec,'f_eq'),(0x3f8,'f_lt'),(0x40c,'f_le'),(0x420,'f_gt'),(0x434,'f_ge')])
    values=DOUBLES if double_input else FLOATS
    cases=list(itertools.product(values,repeat=2))+[(rng.getrandbits(64 if double_input else 32),rng.getrandbits(64 if double_input else 32)) for _ in range(200)]
    for entry,name in entries:
        for a,b in cases:pair.run(entry,'syscon_rt_'+name,*(words(a)+words(b) if double_input else [a,b]))

@pytest.mark.parametrize('entry,symbol',[(0xe8,'syscon_rt_udiv32'),(0x1f4,'syscon_rt_udivmod32'),(0x1fc,'syscon_rt_idiv32'),(0x3c8,'syscon_rt_idivmod32')])
def test_integer_division_signed_unsigned_zero_and_overflow(arithmetic_elf,entry,symbol):
    pair=Pair(arithmetic_elf);rng=random.Random(entry)
    values=[0,1,2,3,7,255,65535,65536,0x7fffffff,0x80000000,0x80000001,0xfffffffe,0xffffffff]
    for a,b in list(itertools.product(values,repeat=2))+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(400)]:pair.run(entry,symbol,a,b,result_words=2)


def test_long_divide_remainder_pointer_and_multiply(arithmetic_elf):
    pair=Pair(arithmetic_elf);rng=random.Random(0x550)
    values=[0,1,2,3,0xffffffff,0x100000000,0x7fffffffffffffff,0x8000000000000000,0xffffffffffffffff]
    cases=list(itertools.product(values,repeat=2))+[(rng.getrandbits(64),rng.getrandbits(64)) for _ in range(500)]
    for a,b in cases:
        pair.run(0x488,'syscon_rt_mul64',*words(a),*words(b),result_words=2)
        for pointer in (0,0x20000900):
            pair.run(0x550,'syscon_rt_udiv64',*words(a),*words(b),pointer,result_words=2)
            assert pair.arm.read(0x20000900,8)==bytes(pair.original.cpu.mem_read(0x20000900,8))
        pair.run(0x448,'syscon_rt_uldivmod',*words(a),*words(b),result_words=4)


def test_clz_and_divzero_preserves_input(arithmetic_elf):
    pair=Pair(arithmetic_elf);rng=random.Random(0x23d0)
    for a in [0,0xffffffffffffffff,*[1<<i for i in range(64)],*[rng.getrandbits(64) for _ in range(100)]]:
        pair.run(0x23d0,'syscon_rt_clz32',a&0xffffffff)
        pair.run(0x240c,'syscon_rt_clz64',*words(a))
        pair.run(0x3d0,'syscon_rt_divzero',*words(a),0x55555555,0xaaaaaaaa,result_words=4)

@pytest.mark.parametrize('entry,symbol,double_input',[(0x3d4,'syscon_rt_frcmp_flags',False),(0x3dc,'syscon_rt_fcmp_flags',False),(0x2354,'syscon_rt_drcmp_flags',True),(0x2364,'syscon_rt_dcmp_flags',True)])
def test_comparison_condition_flags_and_preserved_registers(arithmetic_elf,entry,symbol,double_input):
    pair=Pair(arithmetic_elf)
    for a,b in itertools.product(DOUBLES if double_input else FLOATS,repeat=2):
        args=words(a)+words(b) if double_input else (a,b,0x98765432,0xabcdef00)
        pair.run(entry,symbol,*args,result_words=4)
        assert pair.arm.cpu.reg_read(UC_ARM_REG_APSR)&0xf0000000==pair.original.cpu.reg_read(UC_ARM_REG_APSR)&0xf0000000

@pytest.mark.parametrize('entry,symbol,width,signed',[(0xc0,'syscon_rt_case_sqi',1,True),(0xd4,'syscon_rt_case_uqi',1,False),(0x2660,'syscon_rt_case_shi',2,True)])
def test_switch_dispatch_table_signed_offsets_and_registers(arithmetic_elf,entry,symbol,width,signed):
    pair=Pair(arithmetic_elf)
    values=([-128,-1,1,17,127] if signed and width==1 else [-1024,-129,-1,1,128,1023] if signed else [1,17,127,128,255])
    for i,offset in enumerate(values):
        table=0x20000800;destination=table+2*offset
        data=b''.join(n.to_bytes(width,'little',signed=signed) for n in values)
        for obj,start in ((pair.original,entry),(pair.arm,pair.arm.symbols[symbol])):
            obj.put(table,data);obj.cpu.reg_write(UC_ARM_REG_R0,i);obj.cpu.reg_write(UC_ARM_REG_R1,0xdeadbeef)
            obj.cpu.reg_write(UC_ARM_REG_LR,table|1);obj.cpu.reg_write(UC_ARM_REG_SP,0x20000fc0)
            obj.cpu.emu_start(start|1,destination,count=100)
            assert obj.cpu.reg_read(UC_ARM_REG_PC)==destination
            assert obj.cpu.reg_read(UC_ARM_REG_R0)==i and obj.cpu.reg_read(UC_ARM_REG_R1)==0xdeadbeef


def test_structured_float_cancellation_rounding_and_exponent_gaps(arithmetic_elf):
    pair=Pair(arithmetic_elf)
    # Adjacent significands, half-way rounding and carry propagation are rare
    # in independent random bits, especially for 52-bit double significands.
    for bits,fracbits,expbits,entries in [
        (32,23,8,[(0x6e8,'__aeabi_fadd'),(0xa24,'__aeabi_fdiv'),(0xdb4,'__aeabi_fmul'),(0x1000,'__aeabi_fsub')]),
        (64,52,11,[(0x14bc,'__aeabi_dadd'),(0x1b34,'__aeabi_dsub')])]:
        bias=(1<<(expbits-1))-1;mask=(1<<fracbits)-1;sign=1<<(bits-1)
        fractions=[0,1,2,3,mask//2,mask//2+1,mask-2,mask-1,mask]
        exponents=[0,1,2,3,bias-2,bias-1,bias,bias+1,bias+2,(1<<expbits)-2]
        cases=set()
        for exp,frac in itertools.product(exponents,fractions):
            a=(exp<<fracbits)|frac
            for delta in (0,1,2,3,fracbits-1,fracbits,fracbits+1,fracbits+3,32,33):
                bexp=max(0,exp-delta)
                for bfrac in (0,1,mask-1,mask):
                    b=(bexp<<fracbits)|bfrac
                    for asign,bsign in itertools.product((0,sign),repeat=2):cases.add((a|asign,b|bsign))
        for entry,name in entries:
            for a,b in sorted(cases):pair.run(entry,name,*(words(a)+words(b) if bits==64 else [a,b]),result_words=2 if bits==64 else 1)
    for a in (0xffffff7f,0xffffff80,0xffffff81,0xffffffff):pair.run(0x1438,'__aeabi_ui2f',a)
    for a,b in [(0xbff0000000000001,0xbff0000000000002),(0xbff0000100000000,0xbff0000200000000)]:
        for entry,name in [(0x24a8,'syscon_rt_dcmp_low'),(0x2574,'syscon_rt_dcmp_high')]:pair.run(entry,name,*words(a),*words(b))


def test_halfway_subnormal_rounds_up_to_minimum_normal(arithmetic_elf):
    pair=Pair(arithmetic_elf)
    for sign in (0,0x80000000):
        pair.run(0xa24,'__aeabi_fdiv',0x00ffffff|sign,0x40000000)
        pair.run(0xdb4,'__aeabi_fmul',0x00ffffff|sign,0x3f000000)


def test_five_relocation_free_bodies_match_original_bytes(arithmetic_elf):
    from verify_runtime_arithmetic_binary import compare
    for row in compare(arithmetic_elf)['functions']:assert row['exact_bytes'],row


def test_linkable_eabi_entry_names_preserve_return_registers(arithmetic_elf):
    pair=Pair(arithmetic_elf)
    for entry,symbol in [(0xe8,'__aeabi_uidiv'),(0x1f4,'__aeabi_uidivmod'),(0x1fc,'__aeabi_idiv'),(0x3c8,'__aeabi_idivmod')]:
        for a,b in itertools.product((0,1,0x80000000,0x7fffffff,0xffffffff),repeat=2):pair.run(entry,symbol,a,b,result_words=2)
    for a,b in itertools.product((0,1,0x100000001,0xffffffffffffffff),repeat=2):
        pair.run(0x448,'__aeabi_uldivmod',*words(a),*words(b),result_words=4)
        pair.run(0x488,'__aeabi_lmul',*words(a),*words(b),result_words=2)
