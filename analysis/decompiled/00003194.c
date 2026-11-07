/* UNREVIEWED Ghidra output: FUN_00003194 @ 00003194 */

bool FUN_00003194(void)

{
  int iVar1;
  bool bVar2;
  int local_14;
  uint local_10 [2];
  
  bVar2 = false;
  local_10[1] = 0;
  iVar1 = FUN_000097d4(DAT_000031c8 + 0xe,DAT_000031cc,&local_14,local_10,local_10 + 1);
  if ((iVar1 == 3) && (local_14 == 1)) {
    bVar2 = 1 < local_10[0];
  }
  return bVar2;
}


