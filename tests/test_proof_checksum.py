import json,random,struct,subprocess
import pytest
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS
from unicorn.arm_const import *
from proof_checksum import Problem,Thumb,ProofError,prove,bv,sexpr,number
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle


@pytest.fixture(scope='module')
def proofs(tmp_path_factory):
    root=tmp_path_factory.mktemp('checksum-proof')
    return root,prove(root/'correct'),prove(root/'negative',mutant=True)


def test_universal_checksum_model_proof_and_replayable_smt(proofs):
    root,correct,_=proofs
    assert correct['status']=='unsat' and correct['contract_satisfiable']
    assert correct['binaries_differ']
    assert correct['read_count']==31 and correct['branch_directions_proved']==62
    replay=subprocess.check_output(['z3',str(root/'correct/equivalence.smt2')],text=True)
    assert replay.strip()=='unsat'
    obligations=json.loads((root/'correct/obligations.json').read_text())
    decisions=subprocess.check_output(['z3',str(root/'correct/obligations.smt2')],text=True).splitlines()
    assert decisions==[item['status'] for item in obligations]


def test_negative_control_solver_counterexample_replays_on_original_and_rebuilt_arm(proofs):
    _,_,negative=proofs
    assert negative['status']=='sat' and not negative['universal_equivalence_under_model']
    witness=negative['witness'];data=bytes.fromhex(witness['bytes_hex']);address=witness['pointer']
    original=Oracle();candidate=ArmRebuildOracle(negative['candidate_elf'])
    original.put(address,data);candidate.put(address,data)
    left=original.call(0x282c,address);right=candidate.call('syscon_checksum31',address)
    assert left==witness['original_result'] and right==witness['candidate_result'] and left!=right


def test_unknown_opcode_and_data_dependent_branch_fail_closed():
    with pytest.raises(ProofError,match='Unsupported opcode'):Thumb(Problem(),b'\x00\xbe',0x100).run()
    # Initial Z is unconstrained. Both paths are feasible; this subset cannot
    # silently pick one branch or turn an instruction limit into a theorem.
    with pytest.raises(ProofError,match='Symbolic branch'):Thumb(Problem(),b'\x00\xd1\x70\x47',0x100).run()


def test_thumb_subset_registers_and_nzcv_agree_with_independent_unicorn_execution():
    rng=random.Random(0x282c)
    regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,
          UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,
          UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR]
    opcodes=[0x000c,0x24a5,0x34f7,0x404c,0x430c,0x428c,0x795c]
    edge=[0,1,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    for opcode in opcodes:
        for case in range(8):
            values=[rng.getrandbits(32) for _ in regs]
            values[0]=0x20000100;values[3]=0x20000200;values[13]=0x20000f00;values[14]=0x301
            values[4]=edge[case] if case<len(edge) else rng.getrandbits(32)
            flags=rng.getrandbits(4);byte=rng.randrange(256)
            p=Problem();p.lines.append(f'(assert (= pointer {bv(values[0])}))')
            for i in range(1,15):p.lines.append(f'(assert (= initial_r{i} {bv(values[i])}))')
            for i,flag in enumerate('NZCV'):p.lines.append(f'(assert (= initial_{flag} {"true" if flags&(8>>i) else "false"}))')
            p.lines.append(f'(assert (= (select memory {bv(values[3]+5)}) (_ bv{byte} 8)))')
            state=Thumb(p,struct.pack('<HH',opcode,0x4770),0x100).run()
            names=[p.bind(expr) for expr in state.r]+[p.bind(state.f[flag],'Bool') for flag in 'NZCV']
            status,answer=p.query('true',names);assert status=='sat'
            model={key:value for key,value in sexpr('\n'.join(answer.splitlines()[1:]))}
            expected=[number(model[name]) for name in names[:15]]
            expected_flags=sum((8>>i) for i,name in enumerate(names[15:]) if model[name]=='true')
            cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
            cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
            cpu.mem_map(0,4096);cpu.mem_map(0x20000000,4096)
            cpu.mem_write(0x100,struct.pack('<HH',opcode,0x4770));cpu.mem_write(values[3]+5,bytes([byte]))
            for register,value in zip(regs,values):cpu.reg_write(register,value)
            cpu.reg_write(UC_ARM_REG_XPSR,(1<<24)|(flags<<28))
            cpu.emu_start(0x101,0x102,count=1)
            assert [cpu.reg_read(register) for register in regs]==expected,(hex(opcode),values)
            assert cpu.reg_read(UC_ARM_REG_APSR)>>28==expected_flags,(hex(opcode),values)
