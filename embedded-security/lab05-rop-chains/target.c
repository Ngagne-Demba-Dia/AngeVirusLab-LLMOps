#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// Force system() dans le PLT et "/bin/sh" dans le binaire
// Cette fonction n'est jamais appelée par main()
void setup() {
    system("/bin/sh");
}

void vulnerable() {
    char buffer[64];
    printf("Input : ");
    fflush(stdout);
    read(0, buffer, 200);
}

int main() {
    vulnerable();
    return 0;
}
