/* UNREVIEWED Ghidra output: FUN_00003ec0 @ 00003ec0 */

void FUN_00003ec0(void)

{
  undefined *puVar1;
  undefined *puVar2;
  undefined4 uVar3;
  
  puVar1 = PTR_DAT_00003ee0;
  *(undefined **)PTR_DAT_00003ee0 = PTR_DAT_00003ee4;
  *(undefined4 *)(puVar1 + 4) = 4;
  puVar2 = PTR_DAT_00003ee8;
  *(undefined4 *)(puVar1 + 0xc) = 0;
  uVar3 = DAT_00003eec;
  *(undefined4 *)(puVar1 + 8) = 0;
  puVar1[0x10] = 0;
  FUN_0000969c(puVar1,uVar3,puVar2);
  return;
}


