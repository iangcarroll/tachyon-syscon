/* UNREVIEWED Ghidra output: FUN_00005edc @ 00005edc */

void FUN_00005edc(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 uVar1;
  undefined1 auStack_a0 [4];
  undefined4 *local_9c;
  undefined1 auStack_98 [128];
  undefined4 uStack_c;
  undefined4 uStack_8;
  undefined4 uStack_4;
  
  local_9c = &uStack_c;
  uStack_c = param_2;
  uStack_8 = param_3;
  uStack_4 = param_4;
  FUN_0000975a(auStack_98,0,0x80);
  FUN_000092ac(auStack_98,0x80,param_1,local_9c);
  uVar1 = FUN_00002650(auStack_98);
  FUN_00008c8c(1,auStack_98,uVar1);
  FUN_00009748(auStack_a0,DAT_00005f2c,3);
  FUN_00008c8c(1,auStack_a0,2);
  return;
}


