/* UNREVIEWED Ghidra output: FUN_00005e30 @ 00005e30 */

undefined8 FUN_00005e30(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  undefined1 *puVar3;
  int iVar4;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  
  iVar4 = DAT_00005ec8;
  uStack_1c = param_2;
  uStack_18 = param_3;
  uStack_14 = param_4;
  if (*(char *)(DAT_00005ec8 + 0xd) != '\0') {
    iVar1 = FUN_00008b50(1);
    iVar2 = DAT_00005ecc;
    if (iVar1 != 0) {
      iVar1 = FUN_000098dc(DAT_00005ecc,0x2f);
      if (iVar1 != 0) {
        iVar2 = FUN_000098dc(iVar2,0x2f);
        iVar2 = iVar2 + 1;
      }
      FUN_00002678(iVar2,0x105,DAT_00005ed0);
    }
    FUN_0000975a(DAT_00005ed4,0,0x80);
    *(undefined1 *)(iVar4 + 0xd) = 0;
  }
  FUN_0000975a(&uStack_1c,0,0xc);
  uStack_18._0_2_ = CONCAT11(2,(undefined1)uStack_18);
  puVar3 = (undefined1 *)FUN_00007ac0(1);
  iVar4 = DAT_00005ecc;
  if (puVar3 == (undefined1 *)0x0) {
    iVar2 = FUN_000098dc(DAT_00005ecc,0x2f);
    if (iVar2 != 0) {
      iVar4 = FUN_000098dc(iVar4,0x2f);
      iVar4 = iVar4 + 1;
    }
    FUN_00002678(iVar4,0x116,DAT_00005ed8);
  }
  FUN_00007f58(*puVar3,&uStack_1c);
  FUN_00007f58(puVar3[3],&uStack_1c);
  return CONCAT44(uStack_1c,param_1);
}


