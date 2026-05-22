#include <stdio.h>
#include <string.h>

void win() {
    printf(">>> FLAG : AngeVirus{arm_overflow_controlled_pc} <<<\n");
}

void vulnerable() {
    char buffer[64];
    printf("win @ %p\n", win);
    fflush(stdout);
    gets(buffer);   // overflow volontaire — pas de gets en prod !
}

int main() {
    vulnerable();
    return 0;
}
