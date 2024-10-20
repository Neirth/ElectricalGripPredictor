use std::env;
use std::error::Error;
use electrical_grid_core::{
    services::data_collector_service::DataCollectorService,
    services::predict_load_service::PredictLoadService,
};

fn main() -> Result<(), Box<dyn Error>> {
    // Get the authentication token from environment variables or set a default value
    let auth_token = env::var("ELECTRICITYMAP_API_TOKEN").unwrap_or_else(|_| "UQfwh8hp8TqvO".to_string());

    // Create an instance of the DataCollectorService
    let data_service = DataCollectorService::new(auth_token.clone());

    // Create an instance of the PredictLoadService
    let inference_service = PredictLoadService::default();

    // Check if the user requested data
    if env::args().len() > 1 {
        let command = env::args().nth(1).unwrap();

        match command.as_str() {
            "predict_power_grid_load" => {
                // Fetch power data
                match data_service.get_power_data() {
                    Ok(data) => {
                        // Print the fetched power data
                        for (timestamp, value) in &data {
                            println!("Timestamp: {}, Power Consumption: {} kWh", timestamp, value);
                        }

                        // Pass the fetched data to the inference service
                        match inference_service.predict_load(data) {
                            Ok(results) => println!("Predicted power grid load for the next 15 minutes: {} kWh", results / 4.0),
                            Err(e) => eprintln!("Error running inference: {}", e),
                        }
                    },
                    Err(e) => eprintln!("Error fetching power data: {}", e),
                }
            },
            _ => {
                eprintln!("Unknown command: {}", command);
                eprintln!("Usage: {} <command>", env::args().nth(0).unwrap());
                eprintln!("Available commands: predict_power_grid_load");
            }
        }
    } else {
        eprintln!("No command provided. Please specify a command.");
        eprintln!("Usage: {} <command>", env::args().nth(0).unwrap());
        eprintln!("Available commands: predict_power_grid_load");
    }

    Ok(())
}