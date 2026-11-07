"""Source parser executes real memory/scan helpers; handlers remain named sinks."""
import collections
import random
import struct
import pytest
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from inventory import load_image,command_table
from protocol_target_oracle import build,COMMANDS,DEPENDENCIES
CTX=0x20000800;BUFFER=0x20000900
class AssertionBoundary(Exception):pass

@pytest.fixture(scope='module')
def parser_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('protocol-target'))

def string(cpu,address):
    if not address:return None
    result=bytearray()
    for offset in range(2048):
        b=cpu.cpu.mem_read(address+offset,1)[0]
        if not b:return bytes(result)
        result.append(b)
    raise AssertionError('unterminated test text')

class Pair:
    def __init__(self,elf,default_printer=False):
        self.cpus=[Oracle(),ArmRebuildOracle(elf)];self.events=[[],[]];self.queues=[collections.deque(),collections.deque()]
        self.handler_result=1;self.mutation=None;self.traces=[[],[]]
        self.printers=[0x8fa1 if default_printer else 0x10041,None]
        self.printers[1]=(self.cpus[1].symbols['syscon_target_mfg_logger']|1) if default_printer else self.cpus[1].callback(lambda cpu:self.print(cpu,1))
        for i,cpu in enumerate(self.cpus):
            cpu.hooks[self.printers[i]&~1]=lambda machine,i=i:self.print(machine,i)
            for address,symbol in DEPENDENCIES.items():
                if address==0x8fa0:continue
                entry=address if i==0 else cpu.symbols[symbol]&~1
                cpu.hooks[entry]=lambda machine,i=i,address=address:self.dep(machine,i,address)
            for address,symbol in COMMANDS.items():
                entry=address if i==0 else cpu.symbols[symbol]&~1
                cpu.hooks[entry]=lambda machine,i=i,address=address:self.handler(machine,i,address)
            cpu.put(CTX,struct.pack('<B3xIIBB2xI',0,BUFFER,0,0,1,self.printers[i]))
            def trace(uc,kind,address,size,value,_,i=i):
                if CTX<=address<CTX+16 or BUFFER<=address<BUFFER+128:
                    if kind==UC_MEM_READ:value=int.from_bytes(uc.mem_read(address,size),'little')
                    self.traces[i].append((kind,address,size,value&((1<<(size*8))-1)))
            cpu.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,trace)
    def print(self,cpu,i):
        self.events[i].append(('print',string(cpu,cpu.arg(0))));return 0
    def handler(self,cpu,i,address):
        assert cpu.arg(1)==self.printers[i]
        self.events[i].append(('handler',address,string(cpu,cpu.arg(0))))
        if self.mutation:self.mutation(cpu,i,'handler')
        return self.handler_result
    def dep(self,cpu,i,address):
        if address==0x8cf0:self.events[i].append(('available',cpu.arg(0)));return len(self.queues[i])
        if address==0x8de4:self.events[i].append(('read',cpu.arg(0)));return self.queues[i].popleft()
        if address==0x8c34:self.events[i].append(('echo',cpu.arg(0),cpu.arg(1)))
        if address==0x8f88:
            args=tuple(cpu.arg(j) for j in range(5 if cpu.arg(2)==0xbab8 else 3))
            self.events[i].append(('log',args))
        if address==0x2678:
            self.events[i].append(('assert',string(cpu,cpu.arg(0)),cpu.arg(1),string(cpu,cpu.arg(2))))
            raise AssertionBoundary()
        if self.mutation:self.mutation(cpu,i,address)
        return 0
    def put(self,address,data):
        for cpu in self.cpus:cpu.put(address,data)
    def feed(self,data,assertion=False,trace=True):
        self.events=[[],[]];self.traces=[[],[]]
        for i,cpu in enumerate(self.cpus):
            self.queues[i].extend(data)
            if assertion:
                with pytest.raises(AssertionBoundary):cpu.call(0x49d0 if i==0 else 'syscon_target_protocol_poll',CTX,count=2000000)
            else:cpu.call(0x49d0 if i==0 else 'syscon_target_protocol_poll',CTX,count=2000000)
        assert self.events[0]==self.events[1],self.events
        if trace:assert self.traces[0]==self.traces[1],next(((n,x,y) for n,(x,y) in enumerate(zip(*self.traces)) if x!=y),None)
        assert bytes(self.cpus[0].cpu.mem_read(CTX,16))==self.cpus[1].read(CTX,16)
        assert bytes(self.cpus[0].cpu.mem_read(BUFFER,128))==self.cpus[1].read(BUFFER,128)


def test_parser_every_command_policy_case_prefix_and_uppercase_arguments(parser_elf):
    p=Pair(parser_elf)
    for command in command_table(load_image()):
        for suffix in [b'',b':;',b':abc:;',b' abc',b'extra:123:;']:
            for result in [0,1,0xffffffff]:
                p.handler_result=result;p.feed(command['name'].lower().encode()+suffix+b'\r\n')


def test_parser_byte_filter_raw_uart_values_echo_and_disabled_consumption(parser_elf):
    p=Pair(parser_elf)
    for enabled in [0,1,255]:
        for echo in [0,1,255]:
            p.put(CTX+12,bytes([echo,enabled]));p.put(CTX+8,bytes(4))
            p.feed(list(range(256))+[0x7fffff0a,0x12340041])
    p.feed([0xffffffff],assertion=True)


def test_parser_debug_logging_default_printer_relation_and_live_echo_change(parser_elf):
    for default in [False,True]:
        p=Pair(parser_elf,default);p.put(0x200002ee,b'\x01');p.feed(b'VERSION\n')
        p.mutation=lambda cpu,i,entry:cpu.put(CTX+12,b'\x01') if entry==0x8f88 else None
        p.feed(b'HELP\n')


def test_parser_overflow_suffix_edge_cases_and_random_chunk_boundaries(parser_elf):
    p=Pair(parser_elf);rng=random.Random(0x49d0)
    for data in [b'\n',b';\n',b':\n',b' :;\n',b'VERSION\0bad\n',b'x'*124+b'\n',
                 b'x'*125+b'\n',b'x'*126+b'\nHELP\n',b'ERROR:'+b'a'*117+b':;\n']:
        p.feed(data)
    for _ in range(100):
        text=rng.choice([b'HELP',b'POWER:ON:;',b'LOG:1',b'unknown'])+b'\r\n'
        at=rng.randrange(len(text)+1);p.feed(text[:at]);p.feed(text[at:])


def test_parser_callback_mutation_reloads_used_and_buffer_before_next_byte(parser_elf):
    p=Pair(parser_elf)
    def change(cpu,i,entry):
        if entry=='handler':cpu.put(CTX+8,struct.pack('<I',90));cpu.put(CTX+12,b'\x01')
    p.mutation=change;p.feed(b'HELP\nVERSION\n')
    assert p.cpus[0].u32(CTX+8)==0


def test_parser_aliasing_append_count_store_precedes_buffer_store(parser_elf):
    for offset in [0,1,4,8,9,12,13]:
        p=Pair(parser_elf);p.put(CTX+4,struct.pack('<I',CTX+offset));p.feed(b'A')
