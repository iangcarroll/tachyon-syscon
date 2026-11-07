/* UNREVIEWED Ghidra output: cmd_ERROR @ 00004904 */

undefined4 cmd_ERROR(void)

{
  int iVar1;
  undefined *puVar2;
  
  iVar1 = FUN_000096aa();
  puVar2 = PTR_s__home_runner_work_tachyon_syscon_0000495c;
  if (iVar1 != 1) {
    if (iVar1 == 2) {
      FUN_00008f88(1,PTR_LAB_0000b848_1_00004968,PTR_s__1_failed___d_00004964,0xffffffff);
    }
    else {
      if (iVar1 != 0) {
        FUN_00008f88(1,PTR_LAB_0000b848_1_00004968,PTR_s_Invalid_error_test_command_0000496c);
        return 0;
      }
      iVar1 = FUN_000098dc(PTR_s__home_runner_work_tachyon_syscon_0000495c,0x2f);
      if (iVar1 != 0) {
        iVar1 = FUN_000098dc(puVar2,0x2f);
        puVar2 = (undefined *)(iVar1 + 1);
      }
      FUN_00002678(puVar2,0x110,PTR_s_0_0000b3fe_0x24_00004960);
    }
  }
  return 1;
}


