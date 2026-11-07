/* UNREVIEWED Ghidra output: cmd_READ_PWR @ 00004420 */

undefined4 cmd_READ_PWR(undefined4 param_1,code *param_2)

{
  undefined4 uVar1;
  undefined *puVar2;
  char cVar3;
  
  cVar3 = '\0';
  do {
    if (cVar3 == '\0') {
      uVar1 = FUN_00004c50(0xc);
      puVar2 = PTR_s_VPH__00004478;
    }
    else if (cVar3 == '\x01') {
      uVar1 = FUN_00004c50(0xd);
      puVar2 = PTR_s_5V__00004480;
    }
    else if (cVar3 == '\x02') {
      uVar1 = FUN_00004c50(0xe);
      puVar2 = PTR_s_VBAT__00004484;
    }
    else if (cVar3 == '\x03') {
      uVar1 = FUN_00004c50(0xf);
      puVar2 = PTR_s_1V8__00004488;
    }
    else {
      uVar1 = FUN_00004c50(0x10);
      puVar2 = PTR_s_VUSB__0000448c;
    }
    cVar3 = cVar3 + '\x01';
    (*param_2)(PTR_s__s___dmV_0000447c,puVar2,uVar1);
  } while (cVar3 != '\x05');
  return 1;
}


