"""Original assertion body and retained fault breadcrumbs, stopping on reset/halt."""
from collections import deque
import struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
from oracle import Oracle

class TerminalFault(Exception):
    def __init__(self,value):self.value=value

class FaultOracle(Oracle):
    def __init__(self,buttons=(),registers=None):
        super().__init__()
        self.buttons=deque(buttons)
        self.registers=dict(registers or {})
        self.events=[]
        for base in (0xe000e000,0x400b0000):
            self.cpu.mem_map(base,0x1000)
            self.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self._mmio,begin=base,end=base+0xfff)
        for address,value in self.registers.items():self.put(address,struct.pack('<I',value))
        self.cpu.hook_add(UC_HOOK_CODE,self._instructions)
        self.hooks.update({0x8f88:self._log,0x7f58:self._configure,0x80ac:self._toggle,
                           0x7ae8:self._delay,0x79d0:self._watchdog,0x80f8:self._button})

    def _mmio(self,uc,access,address,size,value,_):
        if access==UC_MEM_WRITE:
            self.events.append(('write',address,value))
            self.registers[address]=value
            if address==0xe000ed0c:raise TerminalFault(-1)
        else:self.events.append(('read',address,int.from_bytes(uc.mem_read(address,size),'little')))

    def _instructions(self,uc,address,size,_):
        if address==0x2690:self.events.append(('disable-interrupts',))
        if address in (0x26f0,0x270a):self.events.append(('barrier',))
        if address in (0x7bc0,0x7bd4):raise TerminalFault(-2)

    def _log(self,o):
        self.events.append(('log-assert',o.arg(0),o.cstring(o.arg(1)),o.cstring(o.arg(2)),
                            o.cstring(o.arg(3)),o.cstring(o.arg(4)),o.arg(5),o.arg(6)))
    def _configure(self,o):self.events.append(('gpio-configure',o.arg(0),bytes(o.cpu.mem_read(o.arg(1),12))))
    def _toggle(self,o):self.events.append(('gpio-toggle',o.arg(0)))
    def _delay(self,o):self.events.append(('delay-cycles',o.arg(0)))
    def _watchdog(self,o):self.events.append(('watchdog',))
    def _button(self,o):
        value=self.buttons.popleft() if self.buttons else 1
        self.events.append(('gpio-read',o.arg(0),value));return value

    def invoke(self,address,*args):
        try:return self.call(address,*args)
        except TerminalFault as event:return event.value
