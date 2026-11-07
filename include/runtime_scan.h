#ifndef SYSCON_RUNTIME_SCAN_H
#define SYSCON_RUNTIME_SCAN_H
#include <stdint.h>
#include <stddef.h>
#include <stdarg.h>
struct _reent;
typedef struct { unsigned char *_base;int _size; } syscon_rt_buffer;
typedef struct syscon_rt_file {
 unsigned char *_p;int _r,_w;short _flags,_file;syscon_rt_buffer _bf;
 int _lbfsize;struct _reent *_data;void *_cookie;
 void *_read,*_write,*_seek,*_close;
 syscon_rt_buffer _ub;unsigned char *_up;int _ur;
 unsigned char _ubuf[3],_nbuf[1];syscon_rt_buffer _lb;
 int _blksize,_offset;uint32_t _lock;uint8_t _mbstate[8];int _flags2;
} syscon_rt_file;
#define EOF (-1)
#define __SERR 0x40
/* ARM32 syscon_rt_file/reent layout is checked by the implementation. */
struct syscon_scan_state {
 int flags,base;size_t width;int nassigned,nread;char *ccltab;int code;
 char buf[350];
 int (*pfn_ungetc)(struct _reent*,int,syscon_rt_file*);
 int (*pfn_refill)(struct _reent*,syscon_rt_file*);
};
int32_t syscon_rt_strtol_core(void *,const char *,char **,int32_t);
int32_t syscon_rt_strtol_r(void *,const char *,char **,int32_t);
int32_t syscon_rt_strtol(const char *,char **,int32_t);
int syscon_rt_strncasecmp(const char *,const char *,uint32_t);
unsigned char *syscon_scan_sccl(char *,const unsigned char *);
int syscon_scan_chars(struct _reent *,struct syscon_scan_state *,syscon_rt_file *,va_list *);
int syscon_scan_integer(struct _reent *,struct syscon_scan_state *,syscon_rt_file *,va_list *);
int syscon_rt_vfscanf(struct _reent *,syscon_rt_file *,const char *,va_list);
int syscon_rt_seofread(void *,void *,char *,int);
int syscon_rt_sscanf(const char *,const char *,...);
int syscon_rt_vfprintf_seeded(void *,void *,const char *,va_list,int32_t,int32_t);
int syscon_rt_snprintf_seeded(int32_t,int32_t,char *,uint32_t,const char *,...);
/* Original ABI entries sample the original incoming stack slot in ARM glue. */
int syscon_rt_vfprintf(void *,void *,const char *,va_list);
int syscon_rt_snprintf(char *,uint32_t,const char *,...);
/* Checked convenience APIs return INT_MIN for unavailable first-float or alternate-octal size seeds. */
int syscon_rt_vfprintf_checked(void *,void *,const char *,va_list);
int syscon_rt_snprintf_checked(char *,uint32_t,const char *,...);
#endif
