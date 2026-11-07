/* UNREVIEWED Ghidra output: cmd_GPIO_READ @ 000047bc */

undefined8 cmd_GPIO_READ(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined4 uVar2;
  uint local_14;
  
  local_14 = 0;
  iVar1 = FUN_000097d4(param_1,DAT_000047f0,&local_14);
  if (iVar1 != 1) {
    (*param_2)(PTR_s_Invalid_parameters__Use__HELP____000047f8);
  }
  else {
    uVar2 = FUN_000080f8(local_14 & 0xffff);
    (*param_2)(PTR_s_Pin__d_value___d_000047f4,local_14,uVar2);
  }
  return CONCAT44(param_1,(uint)(iVar1 == 1));
}


