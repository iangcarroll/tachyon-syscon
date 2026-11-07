/* UNREVIEWED Ghidra output: FUN_0000282c @ 0000282c */

byte FUN_0000282c(byte *param_1)

{
  byte bVar1;
  byte bVar2;
  byte *pbVar3;
  
  bVar2 = 0;
  pbVar3 = param_1 + 0x1f;
  do {
    bVar1 = *param_1;
    param_1 = param_1 + 1;
    bVar2 = bVar2 ^ bVar1;
  } while (param_1 != pbVar3);
  return bVar2;
}


