"""UART parser plus actual configuration handlers; only I/O is substituted."""
import re
from config_oracle import ConfigOracle
from oracle import ProtocolOracle

CONFIG_HANDLERS={0x4760,0x4714,0x44dc,0x46d4,0x45ec,0x4684,0x4638,0x4490,0x45f8,0x45e0,0x3fdc}

class ConfigProtocolOracle(ProtocolOracle,ConfigOracle):
    def __init__(self,config,identity,echo=False,fail=None):
        super().__init__(echo=echo)
        self.put(0xfc00,config)
        self.put(0xf800,identity)
        self.flash.fail=fail
        for address in CONFIG_HANDLERS:del self.hooks[address]

    def _print(self,o):
        fmt=o.cstring(o.arg(0)).decode('latin1')
        arg=iter(range(1,20))
        def render(match):
            value=o.arg(next(arg))
            if match[1]=='s':return o.cstring(value).decode('latin1')
            if match[1]=='d' and value>=0x80000000:value-=0x100000000
            return str(value)
        text=re.sub(r'%([sdu])',render,fmt)
        self.events.append(('print',text))
