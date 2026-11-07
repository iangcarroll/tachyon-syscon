"""Read-only static stack evidence, not a whole-image stack proof.

Uses ELF symbols/instruction CFGs and GCC .su metadata. Unknown control flow,
assembly frames, recursion and indirect calls invalidate a transitive bound.
All bounds assume intact call frames, ordinary AAPCS returns, no asynchronous
exception, and that the supplied .su files match the ELF compilation.
"""
import argparse, hashlib, json, re, subprocess
from collections import defaultdict
from pathlib import Path
from elftools.elf.elffile import ELFFile


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_su(paths):
    result=defaultdict(list)
    for path in paths:
        for line in Path(path).read_text().splitlines():
            match=re.match(r'(.+?):(\d+):(\d+):([^\t]+)\t(\d+)\t(.+)$',line)
            if not match: continue
            source,_,_,name,size,kind=match.groups()
            result[name].append(dict(source=source,bytes=int(size),kind=kind,artifact=str(path)))
    return result


def parse_disassembly(text):
    instructions={}
    for line in text.splitlines():
        match=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{4}(?:[ \t]+|$))+)[ \t]*(\S+)(?:[ \t]+(.*))?$',line)
        if not match:continue
        address,raw,mnemonic,args=match.groups()
        if mnemonic.startswith('.'):continue
        instructions[int(address,16)]=(len(raw.split())*2,mnemonic,(args or '').split('@')[0].strip())
    return instructions


def function_flow(entry,instructions):
    """Reachable direct calls and unresolved branches; branch loops terminate."""
    todo=[entry];visited=set();calls=set();unknown=[]
    while todo:
        pc=todo.pop()
        if pc in visited:continue
        visited.add(pc)
        if pc not in instructions:
            unknown.append(dict(address=hex(pc),reason='control flow reaches undecoded bytes'));continue
        size,op,args=instructions[pc];op=op.removesuffix('.n').removesuffix('.w')
        target=re.match(r'^([0-9a-f]+)\s+<',args)
        if op in ('bl','blx'):
            if target:calls.add(int(target[1],16)&~1)
            else:unknown.append(dict(address=hex(pc),reason='indirect call',instruction=op+' '+args))
            todo.append(pc+size);continue
        if op=='bx':
            if args!='lr':unknown.append(dict(address=hex(pc),reason='indirect branch or non-LR assembly return',instruction=op+' '+args))
            continue
        if op=='pop' and re.search(r'\bpc\b',args):continue
        if op in ('udf','bkpt'):
            unknown.append(dict(address=hex(pc),reason='terminal instruction/fault behavior needs external contract'));continue
        if op in ('b','beq','bne','bcs','bcc','bhs','blo','bmi','bpl','bvs','bvc','bhi','bls','bge','blt','bgt','ble'):
            if target:todo.append(int(target[1],16)&~1)
            else:unknown.append(dict(address=hex(pc),reason='unresolved direct branch'))
            if op!='b':todo.append(pc+size)
            continue
        if re.match(r'(?:mov|ldr|add|subs?)\s*$',op) and args.startswith('pc,'):
            unknown.append(dict(address=hex(pc),reason='computed PC write',instruction=op+' '+args));continue
        todo.append(pc+size)
    return dict(calls=sorted(calls),unknown=unknown,instruction_count=len(visited))


def local_stack_peak(entry,instructions):
    """Validate fixed SP effects along the local CFG independently of .su."""
    todo=[(entry,0)];seen={};peak=0;unknown=[]
    while todo:
        pc,depth=todo.pop()
        if pc in seen:
            if seen[pc]!=depth:unknown.append('different SP depths at CFG join '+hex(pc))
            continue
        seen[pc]=depth
        if pc not in instructions:continue
        size,op,args=instructions[pc];op=op.removesuffix('.n').removesuffix('.w')
        if op in ('push','pop'):
            regs=args.strip('{} ').split(',');count=0
            for reg in regs:
                reg=reg.strip();ran=re.fullmatch(r'r(\d+)-r(\d+)',reg)
                count+=int(ran[2])-int(ran[1])+1 if ran else 1
            depth+=(1 if op=='push' else -1)*count*4
        elif re.match(r'^(?:add|sub)s?$',op) and args.startswith('sp,'):
            value=re.search(r'#(0x[0-9a-f]+|\d+)',args)
            if value:depth+=(1 if op.startswith('sub') else -1)*int(value[1],0)
            else:unknown.append('dynamic SP arithmetic '+hex(pc))
        elif args.startswith('sp,') and op not in ('cmp','tst','str'):
            unknown.append('unmodeled SP assignment '+hex(pc))
        peak=max(peak,depth)
        if depth<0:unknown.append('SP above entry on path '+hex(pc))
        if op=='bx' or (op=='pop' and re.search(r'\bpc\b',args)) or op in ('udf','bkpt'):continue
        target=re.match(r'^([0-9a-f]+)\s+<',args)
        if op in ('b','beq','bne','bcs','bcc','bhs','blo','bmi','bpl','bvs','bvc','bhi','bls','bge','blt','bgt','ble'):
            if target:todo.append((int(target[1],16)&~1,depth))
            if op=='b':continue
        if op not in ('bl','blx') and args.startswith('pc,'):continue
        todo.append((pc+size,depth))
    return dict(peak=peak,unknown=sorted(set(unknown)))


def strongly_connected(graph):
    index=0;indices={};low={};stack=[];active=set();result=[]
    def visit(v):
        nonlocal index
        indices[v]=low[v]=index;index+=1;stack.append(v);active.add(v)
        for w in graph.get(v,[]):
            if w not in graph:continue
            if w not in indices:visit(w);low[v]=min(low[v],low[w])
            elif w in active:low[v]=min(low[v],indices[w])
        if low[v]==indices[v]:
            group=[]
            while True:
                w=stack.pop();active.remove(w);group.append(w)
                if w==v:break
            if len(group)>1 or v in graph[v]:result.append(sorted(group))
    for v in graph:
        if v not in indices:visit(v)
    return result


def calculate_bounds(nodes):
    graph={a:n['calls'] for a,n in nodes.items()}
    cycles=strongly_connected(graph);cyclic={a for group in cycles for a in group};memo={}
    def visit(a):
        if a in memo:return memo[a]
        if a not in nodes:return dict(bound=None,known_path_bytes=0,known_path=[a],unknown=['missing target symbol'])
        n=nodes[a];reasons=[]
        if n['frame'] is None:reasons.append('no unambiguous static compiler frame bound')
        if n['unknown']:reasons.append('unresolved instruction control flow')
        if a in cyclic:
            result=dict(bound=None,known_path_bytes=n['frame'] or 0,known_path=[a],unknown=reasons+['recursive call graph component'])
            memo[a]=result;return result
        children=[visit(c) for c in n['calls']]
        if any(c['bound'] is None for c in children):reasons.append('callee has unresolved transitive bound')
        largest=max(children,key=lambda c:c['known_path_bytes'],default=None)
        path_bytes=(n['frame'] or 0)+(largest['known_path_bytes'] if largest else 0)
        result=dict(bound=None if reasons else (n['frame']+max((c['bound'] for c in children),default=0)),known_path_bytes=path_bytes,
                    known_path=[a]+(largest['known_path'] if largest else []),unknown=reasons)
        memo[a]=result;return result
    for a in nodes:visit(a)
    return memo,cycles


def audit(directory):
    directory=Path(directory);elfpath=directory/'firmware.elf';paths=sorted(directory.glob('*.su'));su=parse_su(paths)
    nodes={};symbols={};vectors=[];file_name=''
    with elfpath.open('rb') as stream:
        elf=ELFFile(stream)
        for symbol in elf.get_section_by_name('.symtab').iter_symbols():
            kind=symbol['st_info']['type'];name=symbol.name;address=symbol['st_value']&~1
            symbols[name]=symbol['st_value']
            if kind=='STT_FILE':file_name=name
            if kind!='STT_FUNC' or symbol['st_shndx']=='SHN_UNDEF':continue
            candidates=su.get(name,[])
            if symbol['st_info']['bind']=='STB_LOCAL':candidates=[c for c in candidates if Path(c['source']).name==file_name]
            frame=max((c['bytes'] for c in candidates),default=None) if candidates and all(c['kind']=='static' for c in candidates) else None
            node=nodes.setdefault(address,dict(names=[],frame=None,metadata=[]))
            node['names'].append(name);node['metadata']+=candidates
            if frame is not None:node['frame']=max(node['frame'] or 0,frame)
        section=elf.get_section_by_name('.vectors')
        if section:
            raw=section.data();vectors=[int.from_bytes(raw[i:i+4],'little') for i in range(0,len(raw),4)]
    disassembly=subprocess.check_output(['arm-none-eabi-objdump','-d',str(elfpath)],text=True)
    instructions=parse_disassembly(disassembly)
    for address,node in nodes.items():
        node.update(function_flow(address,instructions))
        node['local_sp_check']=local_stack_peak(address,instructions)
        if node['local_sp_check']['unknown'] or (node['frame'] is not None and node['local_sp_check']['peak']>node['frame']):
            node['unknown'].append(dict(address=hex(address),reason='local SP effects not bounded by compiler frame metadata'))
    bounds,cycles=calculate_bounds(nodes)
    def named_path(path):return [dict(address=hex(a),names=nodes.get(a,{}).get('names',[])) for a in path]
    for address,node in nodes.items():
        node['calls']=[hex(a) for a in node['calls']]
        value=bounds[address].copy();value['known_path']=named_path(value['known_path']);node['stack']=value
    root_names=['syscon_physical_reset','syscon_target_main','syscon_target_timer_tick','syscon_target_gpio_irq','syscon_target_i2c_irq','syscon_physical_uart0_irq','syscon_physical_uart1_irq','syscon_hardfault','syscon_nmi','syscon_default_exception']
    roots={name:dict(address=hex(symbols[name]&~1),**nodes[symbols[name]&~1]['stack']) for name in root_names if name in symbols}
    top=vectors[0] if vectors else 0x20001000;floor=max(0x20000820,symbols.get('__extra_bss_end',0x20000820),symbols.get('__ram_extra_end',0x20000820))
    known=[dict(address=hex(a),names=n['names'],bytes=n['stack']['bound']) for a,n in nodes.items() if n['stack']['bound'] is not None]
    return dict(elf_sha256=digest(elfpath),input_sha256={str(p):digest(p) for p in [elfpath,*paths]},
        initial_msp=hex(top),fixed_state_end=hex(floor),nominal_stack_headroom=top-floor,
        roots=roots,recursive_components=[named_path(c) for c in cycles],
        vectors=[dict(vector=i,address=hex(v&~1),names=nodes.get(v&~1,{}).get('names',[])) for i,v in enumerate(vectors) if i and v],
        bounded_functions=sorted(known,key=lambda x:x['bytes'],reverse=True),functions={hex(a):n for a,n in sorted(nodes.items())},
        assumptions=['Compiler static .su files correspond to the ELF; source manifest hashes are evidence, not proof of compiler correctness.',
            'Normal calls preserve intact AAPCS frames; arbitrary memory corruption or forged returns excluded.',
            'Bounds cover synchronous direct-call closures only; interrupts and unresolved callbacks excluded.',
            'Each call is charged the full caller frame plus the largest callee bound, conservatively regardless of call-site SP.',
            'Known-path sums omit unknown frames and are neither measured peaks nor proven upper/lower bounds.'],
        exception_note='ARMv6-M exception entry needs32bytes plus possible4byte alignment. Add every active handler frame and nested exception; priority/PRIMASK reachability and nesting bound have not been established here.',
        whole_image_stack_bound_proven=False,flash_candidate=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=Path('build/physical-stack-audit'));p.add_argument('--output',type=Path,default=Path('analysis/physical-stack-audit.json'));a=p.parse_args()
    report=audit(a.directory);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['elf_sha256','nominal_stack_headroom','roots','recursive_components','whole_image_stack_bound_proven']},indent=2))
