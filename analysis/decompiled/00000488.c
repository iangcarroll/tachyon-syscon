/* UNREVIEWED Ghidra output: FUN_00000488 @ 00000488 */

undefined8 FUN_00000488(uint param_1,int param_2,uint param_3,int param_4)

{
  uint uVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  
  uVar4 = (param_1 & 0xffff) * (param_3 & 0xffff);
  uVar3 = (param_1 >> 0x10) * (param_3 & 0xffff);
  iVar2 = (param_3 >> 0x10) * (param_1 >> 0x10);
  uVar1 = (uVar4 >> 0x10) + (param_3 >> 0x10) * (param_1 & 0xffff) + uVar3;
  if (uVar1 < uVar3) {
    iVar2 = iVar2 + 0x10000;
  }
  return CONCAT44(param_1 * param_4 + (uVar1 >> 0x10) + iVar2 + param_2 * param_3,
                  uVar1 * 0x10000 + (uVar4 & 0xffff));
}


