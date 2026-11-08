"""Isolated fixture normalization of the modem's two linked boot labels."""
import struct

class ModemStateComparison:
    FIELD=0x200003c8
    def __init__(self,original,candidate):
        self.mapping={}
        if 'syscon_modem_boot' not in candidate.symbols:return
        assert candidate.symbols['syscon_modem_boot']==self.FIELD-4
        for symbol,old in [('syscon_modem_fct_label',0xd324),('syscon_modem_fastboot_label',0xd328)]:
            pointer=candidate.symbols[symbol]
            assert candidate.cstring(pointer)==original.cstring(old)
            self.mapping[pointer]=old
    def word(self,address,size,value):
        return self.mapping.get(value,value) if (address,size)==(self.FIELD,4) else value
    def memory(self,address,data):
        data=bytearray(data)
        if address<=self.FIELD and self.FIELD+4<=address+len(data):
            offset=self.FIELD-address
            value=struct.unpack_from('<I',data,offset)[0]
            struct.pack_into('<I',data,offset,self.word(self.FIELD,4,value))
        return bytes(data)
