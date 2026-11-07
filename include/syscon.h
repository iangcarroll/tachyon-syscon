#ifndef SYSCON_RE_H
#define SYSCON_RE_H
#include <stddef.h>
#include <stdint.h>

/* Recovered packed flash ABI: two 31-byte strings, each with an XOR checksum. */
typedef struct {
    uint8_t key[31];
    uint8_t key_checksum;
    uint8_t value[31];
    uint8_t value_checksum;
} syscon_slot;
_Static_assert(sizeof(syscon_slot) == 64, "flash slot ABI");

uint8_t syscon_checksum31(const uint8_t field[31]);
int syscon_field_readable(const uint8_t field[31]);
int syscon_field_writable(const uint8_t *field);
int syscon_slot_valid(const syscon_slot *slot);
int syscon_slot_encode(syscon_slot *slot, const char *key, const char *value);
/* Legacy behavior: newest matching key wins even if its checksum is invalid. */
int syscon_find_legacy(const syscon_slot *slots, size_t count, const char *key);

/* Explicit flash boundary. Callbacks receive byte offsets from slots and return
 * the original controller status (3 = success). erase must implement physical
 * sector geometry; program writes one eight-byte word. Fault normally resets. */
typedef struct {
    void *context;
    int (*blank)(void *context, size_t offset);
    int (*program)(void *context, size_t offset, const uint8_t data[8]);
    int (*erase)(void *context, size_t offset);
    void (*fault)(void *context);
} syscon_flash_io;
typedef struct {
    syscon_slot *slots;
    size_t count; /* Runtime = 15, identity = 16. Physical sectors are 1024 bytes. */
    syscon_flash_io io;
} syscon_store;
/* APIs below report -1 for a firmware assertion/reset, -2 for an explicitly
 * unsupported input. Neither is a successful firmware-compatible return. */
int syscon_store_get(syscon_store *store, const char *key, char value[32]);
int syscon_store_append(syscon_store *store, const char *key, const char *value);
int syscon_store_erase(syscon_store *store);
int syscon_store_compact(syscon_store *store, const char *key, const char *value);
int syscon_config_set(syscon_store *store, const char *key, const char *value);
int syscon_store_init(syscon_store *store);
/* Decode the packed 22-byte runtime ABI. Configuration set does not implicitly
 * call this host API; firmware 0x32c8 reloads it after a successful mutation. */
void syscon_config_load(syscon_store *config, syscon_store *identity, uint8_t packed[22]);

typedef struct {
    const char *name;
    uint32_t original_handler;
    uint8_t argument_policy; /* 0 absent, 1 required, 2 optional */
    uint8_t uppercase_arguments;
} syscon_command;
extern const syscon_command syscon_commands[37];

typedef int (*syscon_dispatch)(void *, uint32_t handler, const char *arguments);
typedef void (*syscon_print)(void *, const char *text);
typedef void (*syscon_echo)(void *, uint8_t byte);
typedef struct {
    /* Includes byte preceding buffer: original parser reads it for a lone ';'. */
    uint8_t storage[129];
    uint32_t used;
    uint8_t enabled, echo;
} syscon_parser;
void syscon_parser_init(syscon_parser *parser, int enabled, int echo);
void syscon_parser_feed(syscon_parser *parser, const uint8_t *data, size_t len,
                        syscon_dispatch dispatch, syscon_print print,
                        syscon_echo echo, void *context);

/* ARM ABI represented using 32-bit callback addresses even on a 64-bit host. */
typedef struct {
    uint8_t kind; /* 0 = callback, 1 = delay */
    uint8_t padding[3];
    uint32_t value;
} syscon_action;
typedef struct {
    syscon_action actions[12];
    uint8_t count, current, padding[2];
    uint32_t started_ms;
    uint8_t active, trailing_padding[3];
} syscon_task;
typedef struct { syscon_task slots[2]; } syscon_tasks;
_Static_assert(sizeof(syscon_action) == 8, "action ABI");
_Static_assert(sizeof(syscon_task) == 108, "task ABI");
_Static_assert(offsetof(syscon_task, started_ms) == 100, "timer ABI");
typedef int (*syscon_action_call)(void *, uint32_t address);
void syscon_tasks_init(syscon_tasks *tasks);
int syscon_tasks_submit(syscon_tasks *tasks, const syscon_action *actions, unsigned count);
void syscon_tasks_poll(syscon_tasks *tasks, uint64_t now_ms, syscon_action_call call, void *ctx);
int syscon_tasks_active(const syscon_tasks *tasks);
#endif
