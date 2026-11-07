/* UNREVIEWED Ghidra output: FUN_00008954 @ 00008954 */

undefined4 FUN_00008954(int param_1,int param_2)

{
  int *piVar1;
  ushort uVar2;
  undefined1 *puVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  undefined4 uVar7;
  undefined4 uVar8;
  uint uVar9;
  undefined8 uVar10;
  undefined1 local_28;
  undefined1 local_27;
  undefined1 auStack_24 [16];
  
  puVar3 = (undefined1 *)FUN_00007ac0();
  iVar5 = DAT_00008b04;
  if (puVar3 == (undefined1 *)0x0) {
    iVar4 = FUN_000098dc(DAT_00008b04,0x2f);
    if (iVar4 != 0) {
      iVar5 = FUN_000098dc(iVar5,0x2f);
      iVar5 = iVar5 + 1;
    }
    FUN_00002678(iVar5,0x5b,DAT_00008b08);
  }
  iVar5 = DAT_00008b04;
  if (param_2 == 0) {
    iVar4 = FUN_000098dc(DAT_00008b04,0x2f);
    if (iVar4 != 0) {
      iVar5 = FUN_000098dc(iVar5,0x2f);
      iVar5 = iVar5 + 1;
    }
    FUN_00002678(iVar5,0x5c,DAT_00008b0c);
  }
  iVar4 = FUN_00007a54(*puVar3);
  iVar6 = FUN_00007a54(puVar3[3]);
  iVar5 = DAT_00008b10;
  *(uint *)((uint)*(byte *)(iVar4 + 5) * 4 + DAT_00008b10 + 4) = (byte)puVar3[1] | 0x80;
  *(uint *)((uint)*(byte *)(iVar6 + 5) * 4 + iVar5 + 4) = DAT_00008b14 | (byte)puVar3[4];
  iVar5 = DAT_00008b18;
  iVar4 = *(int *)(puVar3 + 8);
  *(undefined4 *)(iVar4 + DAT_00008b18) = DAT_00008b1c;
  *(undefined4 *)(iVar4 + iVar5 + -4) = DAT_00008b20;
  local_28 = 8;
  local_27 = 0;
  FUN_00009638(iVar4,&local_28);
  FUN_00009748(auStack_24,DAT_00008b24,10);
  FUN_000095f0(*(undefined4 *)(puVar3 + 8),auStack_24);
  uVar7 = DAT_00008b2c;
  iVar4 = *(int *)(puVar3 + 8);
  *(uint *)(iVar4 + 0x1100) = *(uint *)(iVar4 + 0x1100) & DAT_00008b28;
  FUN_000000e8(uVar7,*(undefined4 *)(param_2 + 4));
  uVar7 = FUN_00001438();
  uVar2 = FUN_000004e4();
  *(uint *)(iVar4 + DAT_00008b30) =
       ((uint)uVar2 ^ *(uint *)(iVar4 + DAT_00008b30)) & 0xffff ^ *(uint *)(iVar4 + DAT_00008b30);
  uVar9 = *(uint *)(iVar4 + DAT_00008b34);
  uVar8 = FUN_0000139c();
  uVar7 = FUN_00001000(uVar7,uVar8);
  FUN_00000db4(uVar7,0x42800000);
  uVar10 = FUN_000022c4();
  FUN_000014bc((int)uVar10,(int)((ulonglong)uVar10 >> 0x20),0,DAT_00008b38);
  uVar2 = FUN_00000514();
  iVar5 = DAT_00008b3c;
  *(uint *)(iVar4 + DAT_00008b34) = (uVar2 ^ uVar9) & 0x3f ^ uVar9;
  *(uint *)(iVar4 + iVar5) =
       (*(uint *)(iVar4 + iVar5) & 1 ^ *(uint *)(iVar4 + iVar5)) & 1 ^ *(uint *)(iVar4 + iVar5);
  if (*(char *)(param_2 + 8) == '\0') {
    *(uint *)(iVar4 + DAT_00008b40) = *(uint *)(iVar4 + DAT_00008b40) | 0x400;
    piVar1 = DAT_00008b44;
    if (-1 < (char)puVar3[0xc]) {
      iVar5 = 1 << ((int)(char)puVar3[0xc] & 0x1fU);
      DAT_00008b44[0x60] = iVar5;
      *piVar1 = iVar5;
    }
  }
  *(uint *)(*(int *)(puVar3 + 8) + 0x1100) = *(uint *)(*(int *)(puVar3 + 8) + 0x1100) | 1;
  uVar2 = *(ushort *)(param_2 + 2);
  if (8 < uVar2) {
    uVar2 = 9;
  }
  FUN_00009748(DAT_00008b48 + param_1 * 9,param_2,uVar2);
  FUN_0000975a(param_1 * 0x4c + DAT_00008b4c,0);
  return 0;
}


