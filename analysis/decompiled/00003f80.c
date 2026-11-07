/* UNREVIEWED Ghidra output: cmd_IOEXP_READ @ 00003f80 */

undefined8 cmd_IOEXP_READ(undefined4 param_1,code *param_2,undefined4 param_3)

{
  int iVar1;
  undefined *puVar2;
  undefined4 uVar3;
  undefined4 uStack_20;
  uint local_1c;
  undefined4 uStack_18;
  
  local_1c = 0;
  uStack_20 = param_1;
  uStack_18 = param_3;
  iVar1 = FUN_000097d4(param_1,DAT_00003fc0,&local_1c);
  puVar2 = PTR_s_Invalid_parameters__Use__HELP____00003fc4;
  if (iVar1 == 1) {
    iVar1 = FUN_000039e8(local_1c & 0xff,(int)&uStack_20 + 3);
    if (iVar1 == 0) {
      (*param_2)(PTR_s_Pin__d_value___d_00003fc8,local_1c,uStack_20._3_1_);
      uVar3 = 1;
      goto LAB_00003fb4;
    }
    puVar2 = PTR_s_IOEXP_READ_Error_00003fcc;
  }
  (*param_2)(puVar2);
  uVar3 = 0;
LAB_00003fb4:
  return CONCAT44(uStack_20,uVar3);
}


