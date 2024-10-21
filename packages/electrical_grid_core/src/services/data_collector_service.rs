use reqwest::blocking::Client;
use serde::Deserialize;

#[derive(Deserialize)]
struct PowerData {
    powerConsumptionTotal: i64,
}

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

    /// Retrieves the last 19 elements of power consumption in kWh.
    pub fn get_power_data(&self) -> Result<Vec<(i64, f32)>, String> {
        // Coordinates of Austria (you can adjust them if necessary)
        let lat = 47.5162;
        let lon = 14.5501;

        let url = format!(
            "https://api.electricitymap.org/v3/power-breakdown/latest?lat={}&lon={}",
            lat, lon
        );

        // Make the GET request
        let response = self.client.get(&url)
            .header("auth-token", &self.auth_token)
            .send();

        // Check the result
        match response {
            Ok(resp) => {
                if resp.status().is_success() {
                    let api_response: ApiResponse = resp.json().map_err(|e| e.to_string())?;
                    let consumption_total_kw = api_response.powerConsumptionTotal; // in MW/h

                    // Convert to kWh
                    let consumption_total_kwh = consumption_total_kw * 1000; // in kW/h

                    // Here we return the last 19 elements, simulating the logic for the example
                    let data: Vec<(i64, f32)> = (0..19)
                        .map(|i| {
                            let timestamp = (api_response.datetime.parse::<i64>().unwrap() + i * 900) as i64; // 15 min = 900 s
                            let value = (consumption_total_kwh as f32) * 4.0; // Multiplied by 4 to get the value in kWh as a expect the model
                            (timestamp, value)
                        })
                        .collect();

                    Ok(data)
                } else {
                    Err(format!("Error fetching data: {}", resp.status()))
                }
            }
            Err(e) => Err(format!("Request failed: {}", e)),
        }
    }
}
