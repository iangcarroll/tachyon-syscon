/* UNREVIEWED Ghidra output: FUN_00004d68 @ 00004d68 */

void FUN_00004d68(int param_1)

{
  undefined4 uVar1;
  
  uVar1 = DAT_00004d8c;
  if (param_1 != 0) {
    uVar1 = DAT_00004d90;
  }
  FUN_00008f88(3,DAT_00004d98,DAT_00004d94,uVar1);
  FUN_0000364e(0x26,'\x01' - (param_1 == 0));
  return;
}


