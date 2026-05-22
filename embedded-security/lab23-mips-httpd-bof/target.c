/* AngeRouter httpd v2.1 — handler HTTP vulnérable
 * Lab23 : stack overflow dans parse_auth() via strcpy sans vérification de taille
 * Architecture : MIPSEL 32-bit, O32 ABI, sans protections (-fno-stack-protector)
 */
#include <stdio.h>
#include <string.h>
#include <unistd.h>

void win() {
    puts(">>> FLAG : AngeVirus{httpd_parse_auth_overflow_pwned} <<<");
}

void parse_auth(const char *input) {
    char buf[64];
    strcpy(buf, input);   /* overflow : pas de vérification de taille */
}

int main() {
    char input[256];

    printf("AngeRouter httpd v2.1\n");
    printf("win @ %p\n", win);
    fflush(stdout);

    printf("Auth: ");
    fflush(stdout);
    read(0, input, 200);

    parse_auth(input);
    return 0;
}
