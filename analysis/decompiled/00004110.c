/* UNREVIEWED Ghidra output: cmd_MCU_REBOOT @ 00004110 */

undefined4 cmd_MCU_REBOOT(int param_1,code *param_2)

{
  bool bVar1;
  int iVar2;
  undefined *puVar3;
  
  puVar3 = PTR_s_HARD___00004180;
  if (param_1 != 0) {
    iVar2 = FUN_0000263c(param_1,PTR_s_HARD___00004180);
    if ((iVar2 != 0) && (iVar2 = FUN_0000263c(param_1,PTR_s_SOFT___00004184), iVar2 != 0)) {
      (*param_2)(PTR_s_Invalid_parameters__Use__HELP____000041a0);
      return 0;
    }
    iVar2 = FUN_0000263c(param_1,puVar3);
    if (iVar2 == 0) {
      bVar1 = true;
      puVar3 = PTR_s_hard_0000419c;
      goto LAB_00004142;
    }
  }
  bVar1 = false;
  puVar3 = PTR_s_soft_00004188;
LAB_00004142:
  FUN_00008f88(3,PTR_LAB_0000b848_1_00004190,PTR_DAT_0000418c,puVar3);
  if (bVar1) {
    FUN_000037e4();
    FUN_00005a88();
  }
  FUN_000077c0(500);
  DataSynchronizationBarrier(0xf);
  *(undefined4 *)(DAT_00004194 + 0xc) = DAT_00004198;
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}


