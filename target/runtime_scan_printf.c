/*
 * Copyright (c) 1990 The Regents of the University of California.
 * All rights reserved.
 *
 * This code is derived from software contributed to Berkeley by
 * Chris Torek.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the University nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */
/*
 * Copyright (c) 2012-2014 ARM Ltd
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the company may not be used to endorse or promote
 *    products derived from this software without specific prior written
 *    permission.
 *
 * THIS SOFTWARE IS PROVIDED BY ARM LTD ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL ARM LTD BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
 * TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/* Nano vfprintf parser recovered from original0x9b24. Upstream provenance and
 * licensing are in vendor/newlib-4.3.0/nano-vfprintf.c. */
#include "runtime_scan.h"
#include "runtime_stdio.h"
#include "runtime_heap.h"
#include "runtime_support.h"
#include <limits.h>
#include <stddef.h>
typedef struct {
 int flags,prec,dprec,width,size,ret;
 char code,blank,zero,buf[40],l_buf[3];double value;char expstr[7];int lead;
} print_state;
_Static_assert(offsetof(print_state,l_buf)==67,"printf state sign ABI");
_Static_assert(offsetof(print_state,lead)==88,"printf state lead ABI");
static const char *find(const char *s,int c,unsigned n){while(n--){if(*s==c)return s;s++;}return 0;}
static int format_impl(void *r,void *file,const char *fmt,va_list ap,int32_t seed,int32_t size_seed,int known){
 syscon_rt_file *f=file;print_state s;va_list args;va_copy(args,ap);int n=seed;
 if((f->_flags&0x80)&&!f->_bf._base){f->_bf._base=f->_p=syscon_rt_malloc_r(r,64);if(!f->_p){*(int*)r=12;return -1;}f->_bf._size=64;}
 s.size=size_seed;s.ret=0;s.blank=' ';s.zero='0';
 for(;;){
  const char *start=fmt;while(*fmt&&*fmt!='%')fmt++;
  if(fmt!=start){if(syscon_rt_swrite(r,f,start,fmt-start)==-1)break;s.ret+=(uint32_t)(fmt-start);}
  if(!*fmt)break;
  fmt++;
  s.flags=0;s.width=0;s.prec=-1;s.dprec=0;s.l_buf[0]=0;s.lead=0;
  const char *flags="#-0+ ",*p;
  while((p=find(flags,*fmt,5))){s.flags|=1<<(p-flags);fmt++;}
  if(s.flags&16)s.l_buf[0]=' ';
  if(s.flags&8)s.l_buf[0]='+';
  if(*fmt=='*'){s.width=va_arg(args,int);if(s.width<0){s.width=0u-(uint32_t)s.width;s.flags|=2;}fmt++;}
  else while((unsigned)(*fmt-'0')<=9){s.width=(uint32_t)s.width*10+*fmt++-'0';}
  if(*fmt=='.'){fmt++;if(*fmt=='*'){fmt++;s.prec=va_arg(args,int);if(s.prec<0)s.prec=-1;}
   else{s.prec=0;while((unsigned)(*fmt-'0')<=9)s.prec=(uint32_t)s.prec*10+*fmt++-'0';}}
  flags="hlL";if((p=find(flags,*fmt,3))){s.flags|=64<<(p-flags);fmt++;}
  s.code=*fmt++;
  if(find("efgEFG",s.code,6)){
   /* Original absent weak float handler consumes a double and leaves n as-is.
    * The first value of n is the caller-supplied original stack word. */
   if(!(known&1)){va_end(args);return INT_MIN;}
   (void)va_arg(args,double);
  }else {
   if(s.code=='o' && (s.flags&1) && !(known&2)){va_end(args);return INT_MIN;}
   n=syscon_rt_printf_integer(r,&s,f,syscon_rt_swrite,&args);known=3;if(n==-1)break;
  }
  s.ret+=(uint32_t)n;
 }
 va_end(args);return (f->_flags&0x40)?-1:s.ret;
}
int syscon_rt_vfprintf_seeded(void*r,void*f,const char*format,va_list ap,int32_t seed,int32_t size_seed){return format_impl(r,f,format,ap,seed,size_seed,3);}
int syscon_rt_vfprintf_checked(void*r,void*f,const char*format,va_list ap){return format_impl(r,f,format,ap,0,0,0);}
static int bounded(int known,int32_t seed,int32_t size_seed,char*out,uint32_t size,const char*fmt,va_list ap){
 void*r=syscon_rt_getreent();if(size>INT_MAX){*(int*)r=139;return -1;}
 syscon_rt_file f;f._flags=0x208;f._bf._base=f._p=(unsigned char*)out;f._bf._size=f._w=size?size-1:0;f._file=-1;
 int result=format_impl(r,&f,fmt,ap,seed,size_seed,known);if(result < -1)*(int*)r=139;if(size)*f._p=0;return result;
}
int syscon_rt_snprintf_checked(char*out,uint32_t size,const char*fmt,...){va_list ap;va_start(ap,fmt);int n=bounded(0,0,0,out,size,fmt,ap);va_end(ap);return n;}
int syscon_rt_snprintf_seeded(int32_t seed,int32_t size_seed,char*out,uint32_t size,const char*fmt,...){va_list ap;va_start(ap,fmt);int n=bounded(3,seed,size_seed,out,size,fmt,ap);va_end(ap);return n;}
