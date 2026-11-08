"""Reject common private-address dependencies in production C and assembly.

This source lint complements relocated-image execution; it is not an alias or
whole-program proof. Integer masks are not pointer evidence. The physical linker
is the sole owner of object placement, with hardware/persistent regions allowed.
"""
import re
from pathlib import Path

NUMBER=r'(?:0[xX][0-9a-fA-F]+|[0-9]+)[uUlL]*'
TOKEN=re.compile(r'\b'+NUMBER+r'\b')
POINTER=re.compile(r'(?:\(uintptr_t\)|\([^()\n;]*\*\s*\))\s*('+NUMBER+r')\b')
ACCESS=re.compile(r'\b(?:U32|WORD|REGISTER|TEXT|PTR|S|B|W|V)\s*\(\s*('+NUMBER+r')\b')

def number(text):return int(text.rstrip('uUlL'),0)
def allowed_address(value):
    return (0xf7f8<=value<0x10000 or 0x40000000<=value<0x60000000 or
            0xe0000000<=value<0xe0100000 or value in (0,0x20000000,0x20001000))

def violations(source):
    # Comments and strings may explain historical addresses without using them.
    source=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                  lambda m:'\n'*m[0].count('\n') or ' ',source,flags=re.S)
    findings=set()
    for match in TOKEN.finditer(source):
        value=number(match[0])
        if 0x20000000<value<0x20001000:
            findings.add((source.count('\n',0,match.start())+1,match[0]))
    for pattern in (POINTER,ACCESS):
        for match in pattern.finditer(source):
            value=number(match[1])
            if value and not allowed_address(value):
                findings.add((source.count('\n',0,match.start())+1,match[1]))
    return sorted(findings)

def audit(root=None):
    from build_physical_firmware import production_sources,ROOT
    root=Path(root or ROOT)
    paths=[root/path for path in production_sources()]+list((root/'include').glob('*.h'))
    result=[]
    for path in dict.fromkeys(paths):
        for line,value in violations(path.read_text()):
            result.append((str(path.relative_to(root)),line,value))
    return result

if __name__=='__main__':
    results=audit()
    for path,line,value in results:print(f'{path}:{line}: private address {value}')
    raise SystemExit(bool(results))
