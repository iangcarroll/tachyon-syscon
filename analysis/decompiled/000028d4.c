/* UNREVIEWED Ghidra output: FUN_000028d4 @ 000028d4 */

undefined4 FUN_000028d4(int param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  undefined4 uVar2;
  int iVar3;
  undefined1 auStack_50 [31];
  undefined1 local_31;
  undefined1 auStack_30 [31];
  undefined1 local_11;
  
  FUN_00007b44(DAT_00002968);
  iVar1 = FUN_00007b60(DAT_00002968,param_1);
  if (iVar1 == 3) {
    FUN_0000975a(auStack_50,0,0x40);
    FUN_0000975a(auStack_50,0xff,0x40);
    FUN_0000976c(auStack_50,0x1f,param_2);
    FUN_0000976c(auStack_30,0x1f,param_3);
    local_31 = FUN_0000282c(auStack_50);
    local_11 = FUN_0000282c(auStack_30);
    FUN_00002840(auStack_50);
    iVar1 = 0;
    do {
      FUN_00007b44(DAT_00002968);
      iVar3 = FUN_00007b10(DAT_00002968,param_1 + iVar1,auStack_50 + iVar1);
      if (iVar3 != 3) goto LAB_000028f0;
      iVar1 = iVar1 + 8;
    } while (iVar1 != 0x40);
    FUN_00002840(param_1);
    uVar2 = 1;
  }
  else {
LAB_000028f0:
    FUN_00002738();
    uVar2 = 0;
  }
  return uVar2;
}


