use std::env;
use chrono::Utc;
use crate::services::data_collector_service::DataCollectorService;
use crate::services::predict_load_service::PredictLoadService;
use crate::utils::{denormalize, normalize, unix_epoch_to_iso8601};

pub struct MainService {
    data_service: DataCollectorService,
    inference_service: PredictLoadService,
}

impl Default for MainService {
    fn default() -> Self {
        // Load authentication token or use a default value
        let auth_token = env::var("POWER_GRID_API_TOKEN")
            .unwrap_or_else(|_| "dummy_token".to_string());

        // Service instances
        let data_service = DataCollectorService::new(auth_token.clone());
        let inference_service = PredictLoadService::default();

        MainService {
            data_service,
            inference_service,
        }
    }
}

impl MainService {
    /// Executes the power grid load prediction process
    pub fn predict_power_grid_load(&self) -> Result<f32, String> {
        // Set the start and end times for the last 24 hours
        let end = Utc::now().date_naive().and_hms_opt(23, 45, 0).unwrap();
        let start = Utc::now().date_naive().and_hms_opt(0, 0, 0).unwrap();

        // Retrieve the power consumption data
        let data = self.data_service.get_power_data(start.and_utc(), end.and_utc())
            .map_err(|e| format!("Error fetching power data: {}", e))?;

        // Print the power consumption data
        if env::var("DEBUG_VALUES").is_ok() {
            for (timestamp, value) in &data {
                println!("--> Timestamp: {}, Power Consumption: {} MW", unix_epoch_to_iso8601(*timestamp), value);
            }
        }

        // Normalize the power consumption data
        let (min, max) = data.iter()
            .map(|(_, v)| *v)
            .fold((f32::INFINITY, f32::NEG_INFINITY), |(min, max), v| (min.min(v), max.max(v)));

        let normalized_data: Vec<(i64, f32)> = data.iter()
            .map(|(timestamp, value)| (*timestamp, normalize(*value, min, max)))
            .collect();

        // Pass the normalized data to the inference service
        let results = self.inference_service.predict_load(normalized_data)
            .map_err(|e| format!("Error running inference: {}", e))?;

        // Denormalize the result and return it
        Ok(denormalize(results, min, max))
    }
}