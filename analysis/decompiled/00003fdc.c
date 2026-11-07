/* UNREVIEWED Ghidra output: cmd_CONFIG_INTERNAL @ 00003fdc */

undefined4 cmd_CONFIG_INTERNAL(undefined4 param_1,code *param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  undefined4 uVar7;
  undefined4 uVar8;
  undefined *puVar9;
  
  iVar1 = FUN_00003114();
  iVar2 = FUN_00003120();
  iVar3 = FUN_0000312c();
  iVar4 = FUN_00003138();
  iVar5 = FUN_00003144();
  iVar6 = FUN_00003150();
  uVar7 = FUN_0000315c();
  uVar8 = FUN_00003178();
  puVar9 = PTR_s_true_00004078;
  if (iVar1 == 0) {
    puVar9 = PTR_s_false_0000407c;
  }
  (*param_2)(PTR_s_sys_auto_boot___s_00004080,puVar9);
  puVar9 = PTR_s_true_00004078;
  if (iVar2 == 0) {
    puVar9 = PTR_s_false_0000407c;
  }
  (*param_2)(PTR_s_sys_wake_pin_enable___s_00004084,puVar9);
  puVar9 = PTR_s_true_00004078;
  if (iVar3 == 0) {
    puVar9 = PTR_s_false_0000407c;
  }
  (*param_2)(PTR_s_sys_color_debug_enable___s_00004088,puVar9);
  puVar9 = PTR_s_true_00004078;
  if (iVar4 == 0) {
    puVar9 = PTR_s_false_0000407c;
  }
  (*param_2)(PTR_s_sys_fastboot_enabled___s_0000408c,puVar9);
  puVar9 = PTR_s_true_00004078;
  if (iVar5 == 0) {
    puVar9 = PTR_s_false_0000407c;
  }
  (*param_2)(PTR_s_sys_demo_enabled___s_00004090,puVar9);
  puVar9 = PTR_s_true_00004078;
  if (iVar6 == 0) {
    puVar9 = PTR_s_false_0000407c;
  }
  (*param_2)(PTR_s_sys_enable_5v_when_off___s_00004094,puVar9);
  (*param_2)(PTR_s_sys_edl_timer___d_00004098,uVar7);
  (*param_2)(PTR_s_sys_shutdown_timer___d_0000409c,uVar8);
  return 1;
}


