#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// Gadget ARM32 Thumb explicite : pop {r0, pc}
// .thumb_func assure que le symbole a le bit Thumb (LSB=1)
__asm__(".section .text\n"
        ".thumb\n"
        ".global pop_r0_pc\n"
        ".thumb_func\n"
        "pop_r0_pc:\n\t"
        "pop {r0, pc}\n");

const char binsh[] = "/bin/sh";

void vulnerable() {
    char buffer[64];
    printf("Input : ");
    fflush(stdout);
    read(0, buffer, 200);
}

// Pointeur global — force le linker à inclure system dans la PLT
void (*__keep_system)(const char*) __attribute__((used)) = system;

int main() {
    vulnerable();
    return 0;
}
