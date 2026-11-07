/* UNREVIEWED Ghidra output: FUN_00007c08 @ 00007c08 */

undefined1 FUN_00007c08(void)

{
  undefined1 uVar1;
  uint uVar2;
  
  uVar2 = (uint)*DAT_00007c30;
  if (uVar2 == 0xff) {
    uVar2 = *(uint *)(DAT_00007c34 + 0x1220) & 0x1f;
    *DAT_00007c30 = (byte)uVar2;
  }
  uVar2 = uVar2 - 1 & 0xff;
  uVar1 = 3;
  if (uVar2 < 0x15) {
    uVar1 = *(undefined1 *)(DAT_00007c38 + uVar2);
  }
  return uVar1;
}


