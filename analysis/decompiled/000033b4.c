/* UNREVIEWED Ghidra output: FUN_000033b4 @ 000033b4 */

undefined4 FUN_000033b4(undefined4 param_1)

{
  undefined4 uVar1;
  int iVar2;
  undefined *puVar3;
  undefined4 uVar4;
  undefined1 auStack_30 [32];
  
  iVar2 = FUN_0000263c(param_1,PTR_s_particle_0000343c);
  uVar1 = DAT_00003448;
  if (iVar2 == 0) {
    iVar2 = FUN_000027a8(DAT_00003448,0x3c0);
    puVar3 = PTR_s_confVersion_0000344c;
    uVar4 = 0;
    if (iVar2 != 0) {
      uVar4 = FUN_00002f0c(uVar1,0x3c0,PTR_s_confVersion_0000344c,PTR_s_1_0000b386_0x3b_00003450);
      iVar2 = FUN_00002cb8(uVar1,0x3c0,puVar3,auStack_30);
      if (iVar2 == 0) {
        FUN_00008f88(1,PTR_s_CONF_00003444,PTR_s_configuration_param_erase___Fail_00003454);
        puVar3 = PTR_s__home_runner_work_tachyon_syscon_00003458;
        iVar2 = FUN_000098dc(PTR_s__home_runner_work_tachyon_syscon_00003458,0x2f);
        if (iVar2 != 0) {
          iVar2 = FUN_000098dc(puVar3,0x2f);
          puVar3 = (undefined *)(iVar2 + 1);
        }
        FUN_00002678(puVar3,PTR_LAB_00003460,PTR_s_0_0000b3fe_0x24_0000345c);
      }
      FUN_00002df8();
    }
  }
  else {
    FUN_00008f88(1,PTR_s_CONF_00003444,PTR_s_Invalid_password_00003440);
    uVar4 = 0;
  }
  return uVar4;
}


