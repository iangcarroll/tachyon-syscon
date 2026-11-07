"""Audited entry mapping, including compiler entries missed by Ghidra discovery."""
C='src/runtime_arithmetic.c';A='target/runtime_arithmetic_abi.S';F='target/runtime_arithmetic_float.c';V='vendor/gcc-soft-fp/'
MAPPINGS={
 0xc0:('syscon_rt_case_sqi',A),0xd4:('syscon_rt_case_uqi',A),0x2660:('syscon_rt_case_shi',A),
 0xe8:('syscon_rt_udiv32',C),0x1f4:('syscon_rt_udivmod32',C),0x1fc:('syscon_rt_idiv32',C),0x3c8:('syscon_rt_idivmod32',C),0x3d0:('syscon_rt_divzero',A),
 0x3d4:('syscon_rt_frcmp_flags',A),0x3dc:('syscon_rt_fcmp_flags',A),
 0x3ec:('syscon_rt_f_eq',C),0x3f8:('syscon_rt_f_lt',C),0x40c:('syscon_rt_f_le',C),0x420:('syscon_rt_f_gt',C),0x434:('syscon_rt_f_ge',C),
 0x448:('syscon_rt_uldivmod',A),0x488:('syscon_rt_mul64',C),0x4e4:('syscon_rt_f2u',F),0x514:('syscon_rt_d2u',F),0x550:('syscon_rt_udiv64',C),
 0x6e8:('__aeabi_fadd',V+'addsf3.c'),0xa24:('__aeabi_fdiv',V+'divsf3.c'),0xc54:('syscon_rt_fne',C),0xca0:('syscon_rt_fcmp_low',C),0xd2c:('syscon_rt_fcmp_high',C),0xdb4:('__aeabi_fmul',V+'mulsf3.c'),0x1000:('__aeabi_fsub',V+'subsf3.c'),
 0x135c:('__aeabi_f2iz',V+'fixsfsi.c'),0x139c:('__aeabi_i2f',V+'floatsisf.c'),0x1438:('__aeabi_ui2f',V+'floatunsisf.c'),
 0x14bc:('__aeabi_dadd',V+'adddf3.c'),0x1b34:('__aeabi_dsub',V+'subdf3.c'),0x2258:('__aeabi_d2iz',V+'fixdfsi.c'),0x22c4:('__aeabi_f2d',V+'extendsfdf2.c'),
 0x2354:('syscon_rt_drcmp_flags',A),0x2364:('syscon_rt_dcmp_flags',A),0x2374:('syscon_rt_d_eq',C),0x2380:('syscon_rt_d_lt',C),0x2394:('syscon_rt_d_le',C),0x23a8:('syscon_rt_d_gt',C),0x23bc:('syscon_rt_d_ge',C),
 0x23d0:('syscon_rt_clz32',C),0x240c:('syscon_rt_clz64',C),0x2424:('syscon_rt_dne',C),0x24a8:('syscon_rt_dcmp_low',C),0x2574:('syscon_rt_dcmp_high',C)}
