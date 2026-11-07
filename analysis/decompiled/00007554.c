/* UNREVIEWED Ghidra output: FUN_00007554 @ 00007554 */

undefined8 FUN_00007554(uint param_1,uint param_2,undefined4 param_3)

{
  undefined4 uVar1;
  int iVar2;
  int iVar3;
  
  uVar1 = DAT_000075c4;
  if (param_2 < 0xd) {
    iVar3 = 0;
    if (*(char *)(DAT_000075c8 + 0x68) != '\0') {
      if (*(char *)(DAT_000075c8 + 0xd4) != '\0') {
        uVar1 = DAT_000075cc;
        goto LAB_00007576;
      }
      iVar3 = 1;
    }
    iVar2 = DAT_000075c8 + iVar3 * 0x6c;
    FUN_00009748(iVar2,param_1,param_2 << 3,DAT_000075c8,param_1,param_2,param_3);
    *(char *)(iVar2 + 0x60) = (char)param_2;
    *(undefined1 *)(iVar2 + 0x61) = 0;
    *(undefined4 *)(iVar2 + 100) = 0;
    *(undefined1 *)(iVar2 + 0x68) = 1;
    FUN_00008f88(3,uVar1,DAT_000075d4,iVar3);
  }
  else {
    uVar1 = DAT_000075d0;
LAB_00007576:
    FUN_00008f88(1,DAT_000075c4,uVar1);
    iVar3 = -1;
    param_2 = param_1;
  }
  return CONCAT44(param_2,iVar3);
}


