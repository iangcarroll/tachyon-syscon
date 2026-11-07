/* UNREVIEWED Ghidra output: FUN_00003620 @ 00003620 */

undefined8 FUN_00003620(uint param_1,uint param_2,undefined4 param_3)

{
  int iVar1;
  undefined4 uStack_c;
  undefined4 uStack_8;
  
  uStack_8 = param_3;
  if (param_1 < 0x19) {
    uStack_c = param_2;
    uStack_c = FUN_000080f8(param_1 & 0xffff);
  }
  else {
    uStack_c = param_2 & 0xffffff;
    iVar1 = FUN_000039e8(param_1 - 0x19 & 0xff,(int)&uStack_c + 3);
    if (iVar1 == 0) {
      uStack_c = uStack_c >> 0x18;
    }
    else {
      uStack_c = 0xffffffff;
    }
  }
  return CONCAT44(param_1,uStack_c);
}


