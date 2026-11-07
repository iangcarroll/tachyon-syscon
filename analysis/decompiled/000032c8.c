/* UNREVIEWED Ghidra output: FUN_000032c8 @ 000032c8 */

int FUN_000032c8(undefined4 param_1,undefined4 param_2)

{
  undefined4 uVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  undefined4 local_3c;
  undefined1 auStack_38 [36];
  
  uVar2 = FUN_00002650();
  if ((uVar2 < 0x1f) && (uVar2 = FUN_00002650(param_2), uVar2 < 0x1f)) {
    iVar3 = FUN_00002810(param_1);
    if ((iVar3 == 0) || (iVar3 = FUN_00002810(param_2), uVar1 = DAT_00003390, iVar3 == 0)) {
      FUN_00008f88(1,PTR_s_CONF_0000338c,PTR_s_Refusing__s__char_cannot_be_read_00003398,param_1);
    }
    else {
      iVar4 = FUN_00002cb8(DAT_00003390,0x3c0,param_1,auStack_38);
      if ((iVar4 != 0) && (iVar5 = FUN_0000263c(auStack_38,param_2), iVar5 == 0)) {
        return iVar4;
      }
      local_3c = 0;
      iVar4 = FUN_000029a0(uVar1,0x3c0,param_1,0,&local_3c);
      if (iVar4 == 0) {
        FUN_00008f88(3,PTR_s_CONF_0000338c,PTR_s_Config_storage_full__attempting_c_00003394);
        iVar4 = FUN_00002abc(uVar1,param_1,param_2);
      }
      else {
        iVar4 = FUN_00002650(param_2);
        if (iVar4 == 0) {
          return 0;
        }
        iVar4 = FUN_000028d4(local_3c,param_1,param_2);
      }
      if (iVar4 != 0) {
        FUN_00002df8();
        return iVar3;
      }
    }
  }
  else {
    FUN_00008f88(1,PTR_s_CONF_0000338c,PTR_s_Key_or_value_too_long_00003388);
  }
  return 0;
}


