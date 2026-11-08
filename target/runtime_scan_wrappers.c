/*-
 * Copyright (c) 1990 The Regents of the University of California.
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
#include "runtime_scan.h"
#include "runtime_support.h"
#include <limits.h>
_Static_assert(sizeof(long)==4,"32-bit long required");
int32_t
syscon_rt_strtol_core (void *rptr, const char *__restrict nptr,
	   char **__restrict endptr, int32_t base)
{
	register const unsigned char *s = (const unsigned char *)nptr;
	register unsigned long acc;
	register int c;
	register unsigned long cutoff;
	register int neg = 0, any, cutlim;

	if (base < 0 || base == 1 || base > 36) {
		*(int32_t*)syscon_rt_getreent() = 22;
		return 0;
	}

	/*
	 * Skip white space and pick up leading +/- sign if any.
	 * If base is 0, allow 0x for hex and 0 for octal, else
	 * assume decimal; if base is already 16, allow 0x.
	 */
	do {
		c = *s++;
	} while ((syscon_rt_ctype((unsigned char)c)&SYSCON_CTYPE_SPACE));
	if (c == '-') {
		neg = 1;
		c = *s++;
	} else if (c == '+')
		c = *s++;
	if ((base == 0 || base == 16) &&
	    c == '0' && (*s == 'x' || *s == 'X')) {
		c = s[1];
		s += 2;
		base = 16;
	}
	if (base == 0)
		base = c == '0' ? 8 : 10;

	/*
	 * Compute the cutoff value between legal numbers and illegal
	 * numbers.  That is the largest legal value, divided by the
	 * base.  An input number that is greater than this value, if
	 * followed by a legal input character, is too big.  One that
	 * is equal to this value may be valid or not; the limit
	 * between valid and invalid numbers is then based on the last
	 * digit.  For instance, if the range for longs is
	 * [-2147483648..2147483647] and the input base is 10,
	 * cutoff will be set to 214748364 and cutlim to either
	 * 7 (neg==0) or 8 (neg==1), meaning that if we have accumulated
	 * a value > 214748364, or equal but the next digit is > 7 (or 8),
	 * the number is too big, and we will return a range error.
	 *
	 * Set any if any `digits' consumed; make it negative to indicate
	 * overflow.
	 */
	cutoff = neg ? -(unsigned long)LONG_MIN : LONG_MAX;
	cutlim = cutoff % (unsigned long)base;
	cutoff /= (unsigned long)base;
	for (acc = 0, any = 0;; c = *s++) {
		if (c >= '0' && c <= '9')
			c -= '0';
		else if (c >= 'A' && c <= 'Z')
			c -= 'A' - 10;
		else if (c >= 'a' && c <= 'z')
			c -= 'a' - 10;
		else
			break;
		if (c >= base)
			break;
		if (any < 0 || acc > cutoff || (acc == cutoff && c > cutlim)) {
			any = -1;
		} else {
			any = 1;
			acc *= base;
			acc += c;
		}
	}
	if (any < 0) {
		acc = neg ? LONG_MIN : LONG_MAX;
		*(int32_t*)rptr = 34;
	} else if (neg)
		acc = -acc;
	if (endptr != 0)
		*endptr = (char *) (any ? (char *)s - 1 : nptr);
	return (acc);
}

int32_t syscon_rt_strtol_r(void *r,const char*s,char**e,int32_t b){return syscon_rt_strtol_core(r,s,e,b);}
int32_t syscon_rt_strtol(const char*s,char**e,int32_t b){return syscon_rt_strtol_core(syscon_rt_getreent(),s,e,b);}
int syscon_rt_strncasecmp(const char *a,const char*b,uint32_t n){
 while(n--){uint32_t x=(unsigned char)*a++,y=(unsigned char)*b++;
 if((syscon_rt_ctype(x)&3)==1)x+=32;
 if((syscon_rt_ctype(y)&3)==1)y+=32;
 if(x!=y)return (int)x-(int)y;
 if(!y)break;}return 0;
}
/* Original0x9824: string input has no bytes beyond its buffer. */
int syscon_rt_seofread(void *reent,void *cookie,char *buffer,int length){
 (void)reent;(void)cookie;(void)buffer;(void)length;return 0;
}
int syscon_rt_sscanf(const char *input,const char *format,...){
 syscon_rt_file f;int n=0;while(input[n])n++;
 f._flags=0x204;f._p=f._bf._base=(unsigned char*)input;f._r=f._bf._size=n;
 f._read=(void *)(uintptr_t)syscon_rt_seofread;
 f._file=-1;f._ub._base=0;f._lb._base=0;
 va_list ap;va_start(ap,format);int result=syscon_rt_vfscanf((struct _reent*)syscon_rt_getreent(),&f,format,ap);va_end(ap);return result;
}
