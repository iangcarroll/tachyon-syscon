/* Cooperative two-slot scheduler, recovered from 0x7540..0x76f0.
 * Preserve the original 32-bit start timestamp and zero sentinel behavior.
 */
#include "syscon.h"
#include <string.h>

void syscon_tasks_init(syscon_tasks *tasks) { memset(tasks,0,sizeof(*tasks)); }

int syscon_tasks_submit(syscon_tasks *tasks, const syscon_action *actions, unsigned count) {
    if (count > 12) return -1;
    unsigned index=tasks->slots[0].active ? 1 : 0;
    if (tasks->slots[index].active) return -1;
    syscon_task *t=&tasks->slots[index];
    memcpy(t->actions,actions,count*sizeof(*actions));
    t->count=(uint8_t)count;
    t->current=0;
    t->started_ms=0;
    t->active=1;
    return (int)index;
}

void syscon_tasks_poll(syscon_tasks *tasks, uint64_t now_ms, syscon_action_call call, void *ctx) {
    for (unsigned i=0;i<2;++i) {
        syscon_task *t=&tasks->slots[i];
        if (!t->active) continue;
        if (t->current >= t->count) { t->active=0; continue; }
        const syscon_action *a=&t->actions[t->current];
        if (a->kind == 0) {
            if (call(ctx,a->value) == 0) t->active=0;
            else ++t->current;
        } else if (a->kind == 1) {
            if (t->started_ms == 0) t->started_ms=(uint32_t)now_ms;
            else if (now_ms-(uint64_t)t->started_ms >= a->value) {
                t->started_ms=0;
                ++t->current;
            }
        } else t->active=0;
        if (t->current >= t->count) t->active=0;
    }
}

int syscon_tasks_active(const syscon_tasks *tasks) {
    return tasks->slots[0].active ? tasks->slots[0].active : tasks->slots[1].active;
}
