"""Find toolchain runtime candidates by exact or relocation-masked machine code.

This identifies compiled code provenance candidates; it does not replace source
review, resolve masked branch targets, or declare the firmware rebuilt.
"""
import hashlib
import json
import subprocess
from pathlib import Path
from elftools.elf.elffile import ELFFile
from inventory import ROOT,load_image

def matches(image,code,mask):
    runs=[];start=0
    while start<len(code):
        while start<len(code) and not mask[start]:start+=1
        end=start
        while end<len(code) and mask[end]:end+=1
        if end>start:runs.append((start,end))
        start=end
    if not runs:return []
    lo,hi=max(runs,key=lambda r:r[1]-r[0])
    if hi-lo<8:return []
    found=[];pos=0
    while True:
        at=image.find(code[lo:hi],pos)
        if at<0:break
        candidate=at-lo;pos=at+1
        if candidate<0 or candidate&1 or candidate+len(code)>len(image):continue
        if all(not mask[i] or image[candidate+i]==byte for i,byte in enumerate(code)):
            found.append(candidate)
    return found

def main():
    image=load_image();results=[];archives=[]
    for name in ['libgcc.a','libc_nano.a']:
        flag='-print-libgcc-file-name' if name=='libgcc.a' else '-print-file-name='+name
        archive=Path(subprocess.check_output(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb',flag],text=True).strip()).resolve()
        dest=ROOT/'build/runtime'/archive.stem;dest.mkdir(parents=True,exist_ok=True)
        subprocess.run(['arm-none-eabi-ar','x',str(archive)],cwd=dest,check=True)
        archives.append(dict(path=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest()))
        for path in sorted(dest.glob('*.o')):
            with path.open('rb') as file:
                elf=ELFFile(file);symtab=elf.get_section_by_name('.symtab')
                if symtab is None:continue
                relocations={}
                for section in elf.iter_sections():
                    if section['sh_type'] not in ('SHT_REL','SHT_RELA'):continue
                    offsets=relocations.setdefault(section['sh_info'],set())
                    for relocation in section.iter_relocations():
                        size=2 if relocation['r_info_type'] in (102,103) else 4
                        offsets.update(range(relocation['r_offset'],relocation['r_offset']+size))
                for symbol in symtab.iter_symbols():
                    if symbol['st_info']['type']!='STT_FUNC' or symbol['st_size']<16:continue
                    index=symbol['st_shndx']
                    if not isinstance(index,int):continue
                    section=elf.get_section(index)
                    if not section['sh_flags']&4:continue
                    offset=symbol['st_value']&~1;size=symbol['st_size']
                    code=section.data()[offset:offset+size]
                    if len(code)!=size:continue
                    ignored=relocations.get(index,set())
                    mask=[offset+i not in ignored for i in range(size)]
                    found=matches(image,code,mask)
                    for address in found:
                        results.append(dict(library=name,object=path.name,symbol=symbol.name,
                            address=hex(address),size=size,unique_match=len(found)==1,
                            exact_bytes=code==image[address:address+size],
                            ignored_relocation_bytes=mask.count(False)))
    output=dict(archives=archives,matches=results,
                exact_unmasked_matches=sum(r['exact_bytes'] and r['ignored_relocation_bytes']==0 for r in results),
                limitations=['Relocation-masked matches are candidates until call/data targets are verified.',
                            'Short/generic functions may be ambiguous; matching does not prove source provenance.',
                            'Only installed libgcc and nano-newlib archives were searched; sizes below16 bytes omitted.',
                            'This is not a complete firmware rebuild or proof of semantic coverage.'])
    (ROOT/'analysis/runtime-fingerprints.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('archives','matches','limitations')}))
    print(f'{len(results)} candidates across {len(set(r["address"] for r in results))} original addresses')

if __name__=='__main__':main()
