import struct
import pytest
from test_runtime_scan import Pair,INPUT,OUT,REENT,scan_elf


def test_atoi_and_unsigned_alias_use_reconstructed_parsers_and_errno(scan_elf):
    p=Pair(scan_elf)
    for text in [b'',b'\t -123tail',b'0x12',b'2147483648',b'-2147483649',b'9'*80,b'+17',b'0777']:
        p.put(INPUT,text+b'\0');p.put(REENT,struct.pack('<I',123))
        p.call(0x96aa,'syscon_rt_atoi',INPUT);p.equal(REENT,4)
        for base in [0,2,8,10,16,36]:
            p.put(REENT,struct.pack('<I',123));p.put(OUT,b'\xa5'*4)
            p.call(0xa828,'syscon_rt_strtoul_alias',REENT,INPUT,OUT,base)
            p.equal(OUT,4);p.equal(REENT,4)
