/* UNREVIEWED Ghidra output: FUN_00005bfc @ 00005bfc */

undefined4 FUN_00005bfc(uint param_1,int param_2)

{
  byte *pbVar1;
  undefined2 uVar2;
  
  pbVar1 = DAT_00005c34;
  if (*DAT_00005c34 == param_1) goto LAB_00005c14;
  *DAT_00005c34 = (byte)param_1;
  if (param_1 == 1) {
    pbVar1[0xc] = 0;
  }
  else {
    if (param_1 == 2) {
      uVar2 = 500;
    }
    else {
      if (param_1 != 3) goto LAB_00005c10;
      uVar2 = 100;
    }
    *(undefined2 *)(pbVar1 + 0xe) = uVar2;
  }
LAB_00005c10:
  pbVar1[0xd] = 0;
LAB_00005c14:
  if (param_2 != 0) {
    FUN_00005b48();
  }
  return 0;
}


