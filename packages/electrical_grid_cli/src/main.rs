use std::env;
use std::error::Error;
use chrono::{DateTime, Utc};
use electrical_grid_core::{
    services::data_collector_service::DataCollectorService,
    services::predict_load_service::PredictLoadService,
};

fn main() -> Result<(), Box<dyn Error>> {
    // Get the authentication token from environment variables or set a default value
    let auth_token = env::var("POWER_GRID_API_TOKEN").unwrap_or_else(|_| "dummy_token".to_string());

    // Create an instance of the DataCollectorService
    let data_service = DataCollectorService::new(auth_token.clone());

    // Create an instance of the PredictLoadService
    let inference_service = PredictLoadService::default();

    // Check if the user requested data
    if env::args().len() > 1 {
        let command = env::args().nth(1).unwrap();

        match command.as_str() {
            "predict_power_grid_load" => {
                // Set end and start hour and minute to 0:00 of the current day
                let end = chrono::Utc::now().date_naive().and_hms_opt(23, 45, 0).unwrap();
                let start = chrono::Utc::now().date_naive().and_hms_opt(0, 0, 0).unwrap();

                println!("[*] Getting power data for the last 24 hours...");

                // Fetch power data
                match data_service.get_power_data(
                    start.and_utc(), end.and_utc()
                ) {
                    Ok(data) => {
                        // Normalize the fetched power data
                        let (min, max) = data.iter().map(|(_, v)| *v).fold((f32::INFINITY, f32::NEG_INFINITY), |(min, max), v| (min.min(v), max.max(v)));
                        let normalized_data: Vec<(i64, f32)> = data.iter()
                            .map(|(timestamp, value)| (*timestamp, normalize(*value, min, max)))
                            .collect();

                        // Print the normalized power data
                        for (timestamp, value) in &data {
                            println!("--> Timestamp: {}, Power Consumption: {} MW", unix_epoch_to_iso8601(*timestamp), value);
                        }

                        // Pass the normalized data to the inference service
                        match inference_service.predict_load(normalized_data) {
                            Ok(results) => {
                                // Denormalize the result
                                let denormalized_result = denormalize(results, min, max);
                                println!("[*] Forecast power grid load for the next 15 minutes: {} MW", denormalized_result);
                            },
                            Err(e) => eprintln!("[!] Error running inference -> {}", e),
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
        eprintln!("[!] No command provided. Please specify a command.");
        eprintln!("Usage: {} <command>", env::args().nth(0).unwrap());
        eprintln!("Available commands: predict_power_grid_load");
    }

    Ok(())
}

/// Normalizes a value to the range [0, 1].
fn normalize(value: f32, min: f32, max: f32) -> f32 {
    if max > min {
        (value - min) / (max - min)
    } else {
        0.0 // Handle the edge case where min == max
    }
}

/// Denormalizes a normalized value back to the original range.
fn denormalize(normalized_value: f32, min: f32, max: f32) -> f32 {
    if max > min {
        normalized_value * (max - min) + min
    } else {
        min // Handle the edge case where min == max
    }
}

/// Converts a Unix epoch time to an ISO 8601 formatted string.
fn unix_epoch_to_iso8601(epoch_time: i64) -> String {
    // Convert to DateTime<Utc>
    let datetime: DateTime<Utc> = DateTime::from_timestamp(epoch_time, 0).unwrap();

    // Format to ISO 8601
    datetime.to_rfc3339()
}
