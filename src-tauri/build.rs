fn main() {
    println!("cargo:rerun-if-changed=src/main.rs");
    tauri_build::build();
}