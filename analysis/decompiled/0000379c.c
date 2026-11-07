/* UNREVIEWED Ghidra output: FUN_0000379c @ 0000379c */

longlong FUN_0000379c(uint param_1,uint param_2,undefined4 param_3)

{
  byte bVar1;
  byte bVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  
  uVar5 = 1 << (param_1 & 7);
  iVar3 = (param_1 >> 3) + 2;
  uStack_1c = param_2;
  uStack_18 = param_3;
  FUN_000036bc(iVar3,(int)&uStack_1c + 3);
  uVar4 = uVar5 & 0xff;
  bVar2 = (byte)(uStack_1c >> 0x18);
  bVar1 = (byte)uVar5;
  if (param_2 == 1) {
    if ((uVar4 & uStack_1c >> 0x18) != 0) goto LAB_000037c4;
    bVar2 = bVar2 | bVar1;
  }
  else {
    bVar2 = bVar2 & ~bVar1;
    if (param_2 == 0 && (uVar4 & uStack_1c >> 0x18) == 0) goto LAB_000037c4;
  }
  uStack_1c = CONCAT13(bVar2,(undefined3)uStack_1c);
  FUN_0000374c(iVar3);
LAB_000037c4:
  return (ulonglong)param_1 << 0x20;
}


