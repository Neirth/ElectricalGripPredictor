use std::env;
use std::process;
use electrical_grid_core::services::main_service::MainService;

fn main() {
    if env::args().len() > 1 {
        let command = env::args().nth(1).unwrap();

        match command.as_str() {
            "predict_power_grid_load" => {
                // Create an instance of the main service
                let main_service = MainService::default();

                // Print a message for info purposes
                println!("[*] Getting power data for the last 24 hours...");

                // Predict the power grid load
                match main_service.predict_power_grid_load() {
                    Ok(result) => println!("[*] Predicted power grid load: {} MW", result),
                    Err(e) => {
                        eprintln!("[!] Error predicting power grid load: {}", e);
                        process::exit(1);
                    }
                }
            },
            _ => {
                eprintln!("[!] Unknown command: {}", command);
                print_usage_and_exit();
            }
        }
    } else {
        eprintln!("[!] No command provided. Please specify a command.");
        print_usage_and_exit();
    }
}

fn print_usage_and_exit() {
    eprintln!("Usage: {} <command>", env::args().nth(0).unwrap());
    eprintln!("Available commands: predict_power_grid_load");
    process::exit(1);
}