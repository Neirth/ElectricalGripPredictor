use std::process::Command;
use std::path::Path;

fn main() {
    // Ruta al script de Python
    let script_path = Path::new("src/main.py");

    // Verificar si el script de Python existe
    if !script_path.exists() {
        panic!("El archivo main.py no se encuentra en la carpeta src");
    }

    // Llamar al script de Python durante el build
    let output = Command::new("python3")
        .arg(script_path)
        .output()
        .expect("Error al ejecutar el script de Python");

    // Mostrar el output o errores del script en la consola
    if !output.status.success() {
        eprintln!(
            "Error en el script de Python: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    } else {
        println!(
            "Script ejecutado con éxito: {}",
            String::from_utf8_lossy(&output.stdout)
        );
    }

    // Otras tareas de build.rs pueden ir aquí
}