#include <stdio.h>
#include <string.h>

int secret = 0;

void win() {
    printf(">>> FLAG : AngeVirus{format_string_write} <<<\n");
}

int main() {
    char buffer[128];

    printf("secret est a l'adresse : %p\n", &secret);
    printf("Input : ");
    fflush(stdout);
    fgets(buffer, sizeof(buffer), stdin);
    buffer[strcspn(buffer, "\n")] = 0;

    printf(buffer);   // VULNERABLE : input traite comme format string
    printf("\n");

    printf("Valeur de secret : 0x%x\n", secret);

    if (secret == 0xdeadbeef) {
        win();
    }

    return 0;
}
