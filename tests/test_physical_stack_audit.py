"""Controls for static evidence: unresolved paths must never become bounds."""
from audit_physical_stack import parse_disassembly, function_flow, local_stack_peak, calculate_bounds

def instructions(text):
    return parse_disassembly(text)

def test_direct_call_and_conditional_cfg():
    code=instructions('''
  100: b510       push {r4, lr}
  102: d001       beq.n 108 <f+0x8>
  104: f000 f87c  bl 200 <g>
  108: bd10       pop {r4, pc}
  200: 4770       bx lr
''')
    flow=function_flow(0x100,code)
    assert flow['calls']==[0x200] and not flow['unknown']
    assert local_stack_peak(0x100,code)=={'peak':8,'unknown':[]}

def test_mutable_callback_is_unknown_not_zero_stack():
    code=instructions('''
  100: b510       push {r4, lr}
  102: 4798       blx r3
  104: bd10       pop {r4, pc}
''')
    flow=function_flow(0x100,code)
    bound,_=calculate_bounds({0x100:dict(frame=8,**flow)})
    assert bound[0x100]['bound'] is None
    assert flow['unknown'][0]['reason']=='indirect call'

def test_recursion_poison_propagates_to_callers():
    nodes={1:dict(frame=8,calls=[2],unknown=[]),2:dict(frame=16,calls=[3],unknown=[]),3:dict(frame=24,calls=[2],unknown=[])}
    bounds,cycles=calculate_bounds(nodes)
    assert cycles==[[2,3]]
    assert all(b['bound'] is None for b in bounds.values())

def test_closed_graph_bound_is_conservative_sum():
    nodes={1:dict(frame=8,calls=[2,3],unknown=[]),2:dict(frame=16,calls=[],unknown=[]),3:dict(frame=24,calls=[],unknown=[])}
    bounds,cycles=calculate_bounds(nodes)
    assert not cycles and bounds[1]['bound']==32
    nodes[3]['frame']=None
    bounds,_=calculate_bounds(nodes)
    assert bounds[1]['bound'] is None

def test_variadic_pushes_exceed_compiler_frame_negative_control():
    code=instructions('''
  100: b40e       push {r1, r2, r3}
  102: b500       push {lr}
  104: b09c       sub sp, #112
  106: f000 f87b  bl 200 <g>
  10a: b01c       add sp, #112
  10c: bc08       pop {r3}
  10e: b003       add sp, #12
  110: 4718       bx r3
''')
    check=local_stack_peak(0x100,code)
    assert check['peak']==128 and check['peak']>116
    assert not check['unknown']
    code[0x104]=(2,'sub','sp, #100')
    assert local_stack_peak(0x100,code)['peak']==116

def test_growing_stack_loop_and_dynamic_sp_are_unresolved():
    loop=instructions('''
  100: b401       push {r0}
  102: e7fd       b.n 100 <f>
''')
    assert local_stack_peak(0x100,loop)['unknown']
    dynamic=instructions('''
  100: 44a5       add sp, r4
  102: 4770       bx lr
''')
    assert local_stack_peak(0x100,dynamic)['unknown']

def test_data_words_and_undecoded_paths_are_not_instructions():
    code=instructions('''
  100: 12345678   .word 0x12345678
  104: e7fc       b.n 100 <data>
''')
    assert 0x100 not in code
    assert function_flow(0x104,code)['unknown']
