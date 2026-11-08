"""Compare rebuilt memory-runtime bodies without masking unresolved relocations."""
import hashlib
import json
import subprocess
from elftools.elf.elffile import ELFFile
from inventory import ROOT,load_image

ENTRIES={'strcmp':(0x263c,20),'strlen':(0x2650,14),'memcmp':(0x972c,28),
 'memcpy':(0x9748,18),'memset':(0x975a,16),'strchr':(0x9828,28),
 'strncmp':(0x9890,36),'strncpy':(0x98b4,40),'strrchr':(0x98dc,38),'memchr':(0xa8b0,22)}


def main():
    obj=ROOT/'build/runtime-memory.arm.o';obj.parent.mkdir(exist_ok=True)
    flags=['-std=c11','-mcpu=cortex-m0plus','-mthumb','-Os','-ffreestanding',
           '-fno-builtin','-ffunction-sections','-fdata-sections']
    subprocess.run(['arm-none-eabi-gcc',*flags,'-I',str(ROOT/'include'),'-c',
        str(ROOT/'src/runtime/runtime_memory.c'),'-o',str(obj)],check=True)
    image=load_image();rows=[]
    with obj.open('rb') as file:
        elf=ELFFile(file)
        for name,(address,size) in ENTRIES.items():
            symbol=elf.get_section_by_name('.symtab').get_symbol_by_name('syscon_rt_'+name)[0]
            index=symbol['st_shndx'];offset=symbol['st_value']&~1
            code=elf.get_section(index).data()[offset:offset+symbol['st_size']]
            relocs=[]
            for section in elf.iter_sections():
                if section['sh_type'] in ('SHT_REL','SHT_RELA') and section['sh_info']==index:
                    relocs += [dict(offset=r['r_offset'],type=r['r_info_type']) for r in section.iter_relocations()
                               if offset<=r['r_offset']<offset+len(code)]
            rows.append(dict(function='syscon_rt_'+name,original_address=hex(address),original_size=size,
                reconstructed_size=len(code),unresolved_relocations=relocs,
                exact_bytes=not relocs and code==image[address:address+size]))
    result=dict(compiler=subprocess.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
        compiler_flags=flags,source_sha256=hashlib.sha256((ROOT/'src/runtime/runtime_memory.c').read_bytes()).hexdigest(),
        reference_sha256=hashlib.sha256(image).hexdigest(),functions=rows,
        whole_firmware_match=False,flash_candidate=False)
    (ROOT/'analysis/runtime-memory-binary-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
