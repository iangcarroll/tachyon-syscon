/* UNREVIEWED Ghidra output: cmd_HELP @ 00003f24 */

undefined4 cmd_HELP(undefined4 param_1,code *param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  undefined *puVar2;
  int iVar3;
  
  iVar3 = 0;
  (*param_2)(PTR_s_Available_commands__00003f74);
  do {
    iVar1 = iVar3 * 0xe;
    iVar3 = iVar3 + 1;
    puVar2 = PTR_DAT_00003f78 + iVar1;
    (*param_2)(PTR_s__s____s_00003f7c,
               CONCAT13(puVar2[3],CONCAT12(puVar2[2],CONCAT11(puVar2[1],PTR_DAT_00003f78[iVar1]))),
               *(undefined4 *)(puVar2 + 10),puVar2,param_4);
  } while (iVar3 != 0x25);
  return 1;
}


