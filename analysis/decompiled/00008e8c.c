/* UNREVIEWED Ghidra output: FUN_00008e8c @ 00008e8c */

void FUN_00008e8c(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  undefined4 uVar2;
  undefined1 *puVar3;
  undefined8 uVar4;
  undefined4 local_15c;
  undefined1 auStack_158 [32];
  undefined1 auStack_138 [32];
  undefined1 auStack_118 [252];
  undefined1 auStack_1c [3];
  undefined1 local_19;
  
  if (*DAT_00008f64 == '\0') {
    return;
  }
  iVar1 = FUN_0000312c();
  if (iVar1 != 0) {
    if (param_1 == 4) {
      uVar2 = DAT_00008f68;
    }
    else if (param_1 == 3) {
      uVar2 = DAT_00008f7c;
    }
    else if (param_1 == 2) {
      uVar2 = DAT_00008f80;
    }
    else {
      if (param_1 != 1) goto LAB_00008eb4;
      uVar2 = DAT_00008f84;
    }
    FUN_00003af4(uVar2,7);
  }
LAB_00008eb4:
  uVar4 = FUN_000077b4();
  uVar2 = FUN_000092f4(auStack_158,0x20,DAT_00008f6c);
  FUN_00003af4(auStack_158,uVar2);
  iVar1 = FUN_000092ac(auStack_138,0x20,param_3,param_4,uVar4,param_2);
  puVar3 = auStack_138;
  if (0x1e < iVar1 - 1U) {
    iVar1 = FUN_000092ac(auStack_118,0x100,param_3,param_4,uVar4,param_2);
    if (iVar1 < 1) goto LAB_00008f20;
    if (0xff < iVar1) {
      local_15c = DAT_00008f70;
      FUN_00009748(auStack_1c,&local_15c,3);
      iVar1 = 0xff;
      local_19 = 0;
    }
    puVar3 = auStack_118;
  }
  FUN_00003af4(puVar3,iVar1);
LAB_00008f20:
  iVar1 = FUN_0000312c();
  if (iVar1 != 0) {
    FUN_00003af4(DAT_00008f74,4);
  }
  FUN_00009748(auStack_118,DAT_00008f78,3);
  FUN_00003af4(auStack_118,2);
  return;
}


