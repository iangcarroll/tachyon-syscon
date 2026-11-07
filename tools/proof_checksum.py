"""Scoped ARM checksum equivalence using independently decoded Thumb + SMT-LIB.

No original bytes are copied into the candidate. Every branch must be forced
by the input contract; symbolic forks/unknown instructions fail closed. This
is NOT an ISA-certified or whole-firmware equivalence prover.
"""
import hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
from elftools.elf.elffile import ELFFile
from inventory import ROOT,load_image,EXPECTED

class ProofError(RuntimeError):pass

def bv(n):return f'(_ bv{n&0xffffffff} 32)'
def eq(a,b):return f'(= {a} {b})'
def op(name,*args):return '('+name+' '+' '.join(args)+')'

class Problem:
    def __init__(self):
        self.lines=['(set-logic QF_AUFBV)','(set-option :produce-models true)',
                    '(set-option :timeout 15000)','(declare-const memory (Array (_ BitVec 32) (_ BitVec 8)))',
                    '(declare-const pointer (_ BitVec 32))',
                    f'(assert (and (bvuge pointer {bv(0x20000000)}) (bvule pointer {bv(0x20000fe1)})))']
        for i in range(1,15):self.lines.append(f'(declare-const initial_r{i} (_ BitVec 32))')
        for flag in 'NZCV':self.lines.append(f'(declare-const initial_{flag} Bool)')
        self.lines.append(f'(assert (and (= (bvand initial_r14 {bv(1)}) {bv(1)}) (bvuge initial_r14 {bv(0x101)}) (bvult initial_r14 {bv(0xfff8)})))')
        self.counter=0;self.queries=[]
    def bind(self,expression,sort='(_ BitVec 32)'):
        name=f's{self.counter}';self.counter+=1
        self.lines.append(f'(define-fun {name} () {sort} {expression})');return name
    def script(self,condition,values=()):
        text='\n'.join(self.lines)+f'\n(assert {condition})\n(check-sat)\n'
        if values:text+='(get-value ('+' '.join(values)+'))\n'
        return text
    def query(self,condition,values=()):
        script=self.script(condition,values)
        result=subprocess.run(['z3','-in','-smt2'],input=script,text=True,capture_output=True,timeout=20,check=True)
        status=result.stdout.splitlines()[0] if result.stdout else ''
        if status not in ('sat','unsat'):raise ProofError('Solver did not decide: '+result.stdout+result.stderr)
        self.queries.append({'condition':condition,'status':status})
        return status,result.stdout
    def require(self,condition,label):
        status,_=self.query(f'(not {condition})')
        if status!='unsat':raise ProofError('Unproved obligation: '+label)

class Thumb:
    """Small fail-closed ARMv6-M subset, only the instructions observed here."""
    def __init__(self,problem,code,base):
        self.p=problem;self.code=code;self.base=base;self.pc=base
        self.r=['pointer']+[f'initial_r{i}' for i in range(1,15)]
        self.f={k:'initial_'+k for k in 'NZCV'};self.reads=[];self.steps=0;self.branches=[]
        self.return_target=None
    def nz(self,value):
        self.f['N']=self.p.bind(eq(f'((_ extract 31 31) {value})','#b1'),'Bool')
        self.f['Z']=self.p.bind(eq(value,bv(0)),'Bool')
    def addsub(self,a,b,subtract=False):
        value=self.p.bind(op('bvsub' if subtract else 'bvadd',a,b));self.nz(value)
        self.f['C']=self.p.bind(op('bvuge',a,b) if subtract else
            eq(f'((_ extract 32 32) (bvadd ((_ zero_extend 1) {a}) ((_ zero_extend 1) {b})))','#b1'),'Bool')
        sa=f'((_ extract 31 31) {a})';sb=f'((_ extract 31 31) {b})';sr=f'((_ extract 31 31) {value})'
        self.f['V']=self.p.bind(f'(and {"(not "+eq(sa,sb)+")" if subtract else eq(sa,sb)} (not {eq(sa,sr)}))','Bool')
        return value
    def run(self):
        for _ in range(1000):
            if not self.base<=self.pc<=self.base+len(self.code)-2:raise ProofError('Control escaped audited function')
            h=struct.unpack_from('<H',self.code,self.pc-self.base)[0];address=self.pc;self.pc+=2;self.steps+=1
            if h&0xffc0==0: # LSLS #0, disassembler alias MOVS Rd,Rm; C/V unchanged.
                rd=h&7;rm=(h>>3)&7;self.r[rd]=self.p.bind(self.r[rm]);self.nz(self.r[rd])
            elif h&0xf800==0x2000: # MOVS immediate, C/V unchanged.
                rd=(h>>8)&7;self.r[rd]=self.p.bind(bv(h&255));self.nz(self.r[rd])
            elif h&0xf800==0x3000: # ADDS Rd,#imm8
                rd=(h>>8)&7;self.r[rd]=self.addsub(self.r[rd],bv(h&255))
            elif h&0xf800==0x7800: # LDRB immediate
                rd=h&7;rn=(h>>3)&7;offset=(h>>6)&31
                at=self.p.bind(op('bvadd',self.r[rn],bv(offset)))
                self.p.require(f'(and (bvuge {at} {bv(0x20000000)}) (bvult {at} {bv(0x20001000)}))','read remains in physical SRAM')
                value=self.p.bind(f'((_ zero_extend 24) (select memory {at}))')
                self.reads.append((at,value));self.r[rd]=value
            elif h&0xffc0 in (0x4040,0x4300): # EORS / ORRS register
                rd=h&7;rm=(h>>3)&7
                self.r[rd]=self.p.bind(op('bvxor' if h&0xffc0==0x4040 else 'bvor',self.r[rd],self.r[rm]));self.nz(self.r[rd])
            elif h&0xffc0==0x4280: # CMP register
                self.addsub(self.r[h&7],self.r[(h>>3)&7],subtract=True)
            elif h&0xff00==0xd100: # BNE, determine direction without assuming it.
                condition=f'(not {self.f["Z"]})'
                taken,_=self.p.query(condition);not_taken,_=self.p.query(f'(not {condition})')
                if (taken,not_taken) not in (('sat','unsat'),('unsat','sat')):
                    raise ProofError('Symbolic branch requires path splitting; refusing bounded proof')
                self.branches.append((address,taken=='sat'))
                if taken=='sat':self.pc=address+4+2*struct.unpack('b',bytes([h&255]))[0]
            elif h==0x4770: # BX LR, function-boundary observation.
                self.return_target=self.p.bind(op('bvand',self.r[14],bv(0xfffffffe)));return self
            else:raise ProofError(f'Unsupported opcode {h:04x} at {address:#x}')
        raise ProofError('Termination not established within interpreter resource budget')


def compile_candidate(output,mutant=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/config.c').read_text()
    if mutant:
        old='checksum ^= field[i]';assert source.count(old)==1
        source=source.replace(old,'checksum |= field[i]')
    # Compile the exact snapshotted source whose hash is recorded, even if a
    # collaborator edits the workspace copy while this proof is running.
    path=output/'candidate-source.c';path.write_text(source)
    header=(ROOT/'include/syscon.h').read_bytes()
    snapshot_include=output/'candidate-include';snapshot_include.mkdir(exist_ok=True)
    (snapshot_include/'syscon.h').write_bytes(header)
    obj=output/'candidate.o';elf_path=output/'candidate.elf'
    flags=['-std=c11','-mcpu=cortex-m0plus','-mthumb','-mfloat-abi=soft','-O2','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-I'+str(snapshot_include)]
    subprocess.run(['arm-none-eabi-gcc',*flags,'-c',str(path),'-o',str(obj)],check=True)
    script=output/'test.ld';script.write_text('ENTRY(syscon_checksum31)\nSECTIONS { . = 0x01000000; .text : { *(.text.syscon_checksum31) } /DISCARD/ : { *(.ARM.exidx*) *(.comment*) } }\n')
    subprocess.run(['arm-none-eabi-gcc','-nostdlib','-Wl,--gc-sections','-Wl,-T,'+str(script),str(obj),'-o',str(elf_path)],check=True)
    with elf_path.open('rb') as stream:
        elf=ELFFile(stream);sym=elf.get_section_by_name('.symtab').get_symbol_by_name('syscon_checksum31')[0]
        section=elf.get_section(sym['st_shndx']);base=sym['st_value']&~1;offset=base-section['sh_addr']
        code=section.data()[offset:offset+sym['st_size']]
    return code,base,elf_path,source,flags,header


def sexpr(text):
    tokens=re.findall(r'\(|\)|[^\s()]+',text);position=0
    def parse():
        nonlocal position
        token=tokens[position];position+=1
        if token!='(':return token
        result=[]
        while tokens[position]!=')':result.append(parse())
        position+=1;return result
    return parse()

def number(node):
    if isinstance(node,str):
        if node.startswith('#x'):return int(node[2:],16)
        if node.startswith('#b'):return int(node[2:],2)
        return int(node)
    if len(node)==3 and node[0]=='_' and node[1].startswith('bv'):return int(node[1][2:])
    raise ProofError('Unexpected solver value '+repr(node))


def prove(output,mutant=False):
    if not shutil.which('z3'):raise ProofError('z3 CLI is required')
    output=Path(output);code,base,elf,source,flags,header=compile_candidate(output,mutant)
    original=load_image()[0x282c:0x2840];p=Problem()
    # Establish satisfiable assumptions, so an impossible contract cannot prove anything.
    if p.query('true')[0]!='sat':raise ProofError('Input contract is inconsistent')
    reference=Thumb(p,original,0x282c).run();candidate=Thumb(p,code,base).run()
    differences=[f'(not {eq(reference.r[0],candidate.r[0])})',f'(not {eq(reference.return_target,candidate.return_target)})']
    for i in range(4,15):
        if i==12:continue # AAPCS permits R12 and R1..R3 to be clobbered.
        for state in (reference,candidate):differences.append(f'(not {eq(state.r[i],f"initial_r{i}")})')
    if len(reference.reads)!=len(candidate.reads):differences.append('true')
    else:
        for left,right in zip(reference.reads,candidate.reads):
            differences.extend(f'(not {eq(a,b)})' for a,b in zip(left,right))
    mismatch='(or '+' '.join(differences)+')'
    status,_=p.query(mismatch)
    (output/'equivalence.smt2').write_text(p.script(mismatch))
    witness=None
    if status=='sat':
        names=['pointer']
        for i in range(31):
            name=f'byte{i}';p.lines.append(f'(define-fun {name} () (_ BitVec 8) (select memory (bvadd pointer {bv(i)})))');names.append(name)
        names.extend([reference.r[0],candidate.r[0]])
        _,answer=p.query(mismatch,names);pairs=sexpr('\n'.join(answer.splitlines()[1:]))
        values={key:number(value) for key,value in pairs}
        witness={'pointer':values['pointer'],'bytes_hex':bytes(values[f'byte{i}'] for i in range(31)).hex(),
                 'original_result':values[reference.r[0]],'candidate_result':values[candidate.r[0]]}
        (output/'counterexample.smt2').write_text(p.script(mismatch,names))
    obligations='\n'.join(p.lines)+'\n'
    for query in p.queries:
        obligations+='(push 1)\n(assert '+query['condition']+')\n(check-sat)\n(pop 1)\n'
    (output/'obligations.smt2').write_text(obligations)
    (output/'obligations.json').write_text(json.dumps(p.queries,indent=2)+'\n')
    result=dict(scope='checksum31 ABI function; readable SRAM; ordinary Thumb return into flash; no interrupts/concurrent mutation',
        status=status,universal_equivalence_under_model=status=='unsat',mutant=mutant,
        contract_satisfiable=True,proof_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        project_header_sha256=hashlib.sha256(header).hexdigest(),
        solver_binary_sha256=hashlib.sha256(Path(shutil.which('z3')).read_bytes()).hexdigest(),reference_sha256=EXPECTED,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        candidate_elf=str(elf),candidate_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
        original_bytes=original.hex(),candidate_bytes=code.hex(),binaries_differ=original!=code,
        compiler=subprocess.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],compiler_flags=flags,
        solver=subprocess.check_output(['z3','-version'],text=True).strip(),
        reference_steps=reference.steps,candidate_steps=candidate.steps,read_count=len(reference.reads),
        branch_directions_proved=len(reference.branches)+len(candidate.branches),solver_obligations=len(p.queries),
        witness=witness,full_firmware_equivalence=False,physical_cycle_equivalence=False,
        trusted_components=['SMT solver','audited Thumb subset interpreter','ELF extraction and compiler provenance','input contract'],
        limitations=['No interrupts, DMA, concurrent mutation, MMIO or invalid-pointer behavior is in this theorem.',
                    'Caller-saved R1-R3/R12 and APSR flags are outside the compared ABI observation.',
                    'This is a solver-checked model theorem, not an independently certified ARM ISA proof.'])
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'analysis/proof-checksum');parser.add_argument('--mutant',action='store_true');args=parser.parse_args()
    print(json.dumps(prove(args.output,args.mutant),indent=2))
