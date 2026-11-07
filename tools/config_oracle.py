"""Original configuration code with an explicit flash-controller test boundary."""
from oracle import Oracle


class FirmwareAssertion(Exception):
    pass


class FlashModel:
    """Atomic 8-byte program, 1 KiB sector erase; injected errors do no mutation.

    This does not model electrical power loss during an individual flash pulse.
    Command addresses remain visible, including repeated same-sector erases.
    """
    def __init__(self, read, write, fail=None):
        self.read, self.write = read, write
        self.events = []
        self.counts = {}
        self.fail = fail

    def operation(self, kind, offset, data=b''):
        self.counts[kind] = self.counts.get(kind, 0) + 1
        status = 3
        if self.fail == (kind, self.counts[kind]):
            status = 1
        elif kind == 'blank':
            if self.read(offset, 8) != b'\xff' * 8: status = 1
        elif kind == 'program':
            previous = self.read(offset, 8)
            if any((old & new) != new for old, new in zip(previous, data)): status = 1
            else: self.write(offset, data)
        elif kind == 'erase':
            self.write(offset & ~1023, b'\xff' * 1024)
        else:
            raise ValueError(kind)
        self.events.append((kind, offset, bytes(data), status))
        return status


class ConfigOracle(Oracle):
    KEY = 0x20000800
    VALUE = 0x20000840
    OUTPUT = 0x20000880

    def call(self, address, *args, count=2000000):
        # Full update includes ten legacy scans and their diagnostic formatting.
        return super().call(address, *args, count=count)

    def __init__(self, initial=None, base=0xfc00, count=15, fail=None):
        super().__init__()
        self.base, self.count = base, count
        self.put(base, initial if initial is not None else b'\xff'*1024)
        self.flash = FlashModel(lambda off,n: bytes(self.cpu.mem_read(base+off,n)),
                                lambda off,data: self.put(base+off,data), fail)
        self.hooks[0x8f88] = lambda _: None  # Diagnostic UART only.
        self.hooks[0x79d0] = lambda _: None  # Watchdog feeding.
        self.hooks[0x7b44] = lambda _: None  # Unprotect MAIN via CMDWEPROTA/B/C.
        self.hooks[0x2738] = lambda _: None  # Log peripheral status on error.
        self.hooks[0x7b60] = lambda o: self.flash.operation('blank', o.arg(1)-base)
        self.hooks[0x7b10] = lambda o: self.flash.operation('program',o.arg(1)-base,bytes(o.cpu.mem_read(o.arg(2),8)))
        self.hooks[0x7af4] = lambda o: self.flash.operation('erase',o.arg(1)-base)
        self.hooks[0x2678] = self.assertion

    def assertion(self, o):
        raise FirmwareAssertion((self.cstring(o.arg(0)), o.arg(1)))

    def invoke(self, op, key=b'', value=b''):
        self.put(self.KEY, key+b'\0')
        self.put(self.VALUE, value+b'\0')
        if op == 'append': return self.call(0x2f0c, self.base,self.count*64,self.KEY,self.VALUE)
        if op == 'compact': return self.call(0x2abc, self.base,self.KEY,self.VALUE)
        if op == 'set': return self.call(0x32c8, self.KEY,self.VALUE)
        if op == 'erase': return self.call(0x27a8,self.base,self.count*64)
        if op == 'init':
            self.call(0x2fa0,self.base,self.count*64)
            return 1
        if op == 'load':
            self.call(0x2df8)
            return bytes(self.cpu.mem_read(0x20000030,22))
        if op == 'get':
            self.put(self.OUTPUT,b'\x5a'*32)
            result=self.call(0x2cb8,self.base,self.count*64,self.KEY,self.OUTPUT)
            return result,bytes(self.cpu.mem_read(self.OUTPUT,32))
        raise ValueError(op)

    def contents(self):
        return bytes(self.cpu.mem_read(self.base,1024))
