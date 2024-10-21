use reqwest::blocking::Client;
use serde::Deserialize;
use std::error::Error;

#[derive(Deserialize)]
struct ApiResponse {
    zone: String,
    datetime: String,
    powerConsumptionTotal: i64,
}

pub struct DataCollectorService {
    client: Client,
    auth_token: String,
}

impl DataCollectorService {
    /// Initializes the service with a REST client and an authentication token.
    pub fn new(auth_token: String) -> Self {
        let client = Client::new();
        Self { client, auth_token }
    }

    /// Retrieves the power data for a specified range.
    pub fn get_power_data(&self, start: &str, end: &str) -> Result<Vec<(i64, f32)>, Box<dyn Error>> {
        // Coordinates of Austria
        let lat = 47.5162;
        let lon = 14.5501;

        let url = format!(
            "https://api.electricitymap.org/v3/power-breakdown/past-range?lat={}&lon={}&start={}&end={}",
            lat, lon, start, end
        );

        // Make the GET request
        let response = self.client.get(&url)
            .header("auth-token", &self.auth_token)
            .send()?;

        // Check the result
        if response.status().is_success() {
            let api_response: Vec<ApiResponse> = response.json()?;

            // Extract the total power consumption
            let data: Vec<(i64, f32)> = api_response.into_iter().map(|entry| {
                let timestamp = entry.datetime.parse::<i64>().unwrap() / 1000; // Convert ms to s
                let consumption_total_kwh = entry.powerConsumptionTotal as f32; // already in kWh
                (timestamp, consumption_total_kwh)
            }).collect();

            Ok(data)
        } else {
            Err(format!("Error fetching data: {}", response.status()).into())
        }
    }
}