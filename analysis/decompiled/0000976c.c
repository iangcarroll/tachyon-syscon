/* UNREVIEWED Ghidra output: FUN_0000976c @ 0000976c */

int FUN_0000976c(undefined1 *param_1,int param_2,undefined4 param_3)

{
  int iVar1;
  undefined4 *puVar2;
  undefined1 *local_80 [2];
  int local_78;
  undefined2 local_74;
  undefined2 local_72;
  undefined1 *local_70;
  int local_6c;
  
  puVar2 = (undefined4 *)*DAT_000097d0;
  if (param_2 < 0) {
    *puVar2 = 0x8b;
    iVar1 = -1;
  }
  else {
    local_74 = 0x208;
    local_78 = 0;
    if (param_2 != 0) {
      local_78 = param_2 + -1;
    }
    local_72 = 0xffff;
    local_80[0] = param_1;
    local_70 = param_1;
    local_6c = local_78;
    iVar1 = FUN_00009b24(puVar2,local_80,param_3);
    if (iVar1 < -1) {
      *puVar2 = 0x8b;
    }
    if (param_2 != 0) {
      *local_80[0] = 0;
    }
  }
  return iVar1;
}


