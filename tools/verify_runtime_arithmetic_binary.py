"""Check five audited relocation-free runtime bodies, without byte masks."""
import hashlib,json
from pathlib import Path
from elftools.elf.elffile import ELFFile
from build_runtime_arithmetic import build,ROOT
from inventory import load_image

EXACT_BODIES=[('syscon_rt_case_sqi',0xc0,18),('syscon_rt_case_uqi',0xd4,18),
 ('syscon_rt_case_shi',0x2660,20),('syscon_rt_divzero',0x3d0,2),('__aeabi_f2iz',0x135c,64)]

def compare(elf_path):
    original=load_image();rows=[]
    with Path(elf_path).open('rb') as stream:
        elf=ELFFile(stream)
        for name,address,size in EXACT_BODIES:
            sym=elf.get_section_by_name('.symtab').get_symbol_by_name(name)[0]
            section=elf.get_section(sym['st_shndx']);offset=(sym['st_value']&~1)-section['sh_addr']
            code=section.data()[offset:offset+sym['st_size']]
            rows.append(dict(symbol=name,original_address=hex(address),original_extent_bytes=size,
                rebuilt_size=len(code),exact_bytes=code==original[address:address+size]))
    manifest=json.loads(Path(elf_path).with_name('manifest.json').read_text())
    assert manifest['elf_sha256']==hashlib.sha256(Path(elf_path).read_bytes()).hexdigest()
    return dict(source_sha256=manifest['source_sha256'],reference_sha256=hashlib.sha256(original).hexdigest(),
        elf_sha256=hashlib.sha256(Path(elf_path).read_bytes()).hexdigest(),functions=rows,
        scope='Only five audited relocation-free bodies; other arithmetic functions differ or are unassessed.',
        whole_firmware_match=False,flash_candidate=False)

if __name__=='__main__':
    result=compare(build(ROOT/'build/runtime-arithmetic'))
    (ROOT/'analysis/runtime-arithmetic-binary-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['functions'],indent=2))
