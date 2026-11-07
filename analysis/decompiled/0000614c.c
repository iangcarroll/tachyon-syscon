/* UNREVIEWED Ghidra output: FUN_0000614c @ 0000614c */

undefined8 FUN_0000614c(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined2 uStack_1c;
  undefined2 local_1a;
  undefined4 local_18;
  undefined4 uStack_14;
  
  iVar1 = DAT_000061a8;
  uStack_1c = (undefined2)param_2;
  local_1a = (undefined2)((uint)param_2 >> 0x10);
  if (*(char *)(DAT_000061a8 + 0xd) == '\0') {
    local_18 = param_3;
    uStack_14 = param_4;
    FUN_0000975a(&uStack_1c,0,9);
    local_1a = 9;
    local_18 = 0x1c200;
    iVar2 = FUN_00008954(1,&uStack_1c);
    iVar3 = DAT_000061ac;
    if (iVar2 != 0) {
      iVar2 = FUN_000098dc(DAT_000061ac,0x2f);
      if (iVar2 != 0) {
        iVar3 = FUN_000098dc(iVar3,0x2f);
        iVar3 = iVar3 + 1;
      }
      FUN_00002678(iVar3,0xf8,DAT_000061b0);
    }
    FUN_0000975a(DAT_000061b4,0,0x80);
    *(undefined1 *)(iVar1 + 0xd) = 1;
  }
  return CONCAT26(local_1a,CONCAT24(uStack_1c,param_1));
}


