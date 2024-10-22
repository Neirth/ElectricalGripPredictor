use reqwest::blocking::Client;
use serde::Deserialize;
use std::error::Error;
use std::str::FromStr;
use chrono::{DateTime, Duration, SecondsFormat, Utc, Timelike};
use quick_xml::de::from_str;

#[derive(Deserialize, Debug)]
struct Point {
    quantity: f32,
}

#[derive(Deserialize, Debug)]
struct Period {
    #[serde(rename = "Point", default)]
    points: Vec<Point>,
}

#[derive(Deserialize, Debug)]
struct TimeSeries {
    #[serde(rename = "Period")]
    period: Period,
}

#[derive(Deserialize, Debug)]
struct GLMarketDocument {
    #[serde(rename = "TimeSeries")]
    time_series: TimeSeries,
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

    /// Creates the XML request body for the API call.
    fn create_request_body(start: DateTime<Utc>, end: DateTime<Utc>) -> String {
        let start_str = &*start.to_rfc3339_opts(SecondsFormat::Secs, true);
        let end_str = &*end.to_rfc3339_opts(SecondsFormat::Secs, true);

        format!(
            r#"
<StatusRequest_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-5:statusrequestdocument:4:0">
    <mRID>SampleCallToRestfulApi</mRID>
    <type>A59</type>
    <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
    <sender_MarketParticipant.marketRole.type>A07</sender_MarketParticipant.marketRole.type>
    <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
    <receiver_MarketParticipant.marketRole.type>A32</receiver_MarketParticipant.marketRole.type>
    <createdDateTime>2016-01-10T13:00:00Z</createdDateTime>
    <AttributeInstanceComponent>
        <attribute>DocumentType</attribute>
        <attributeValue>A65</attributeValue>
    </AttributeInstanceComponent>
    <AttributeInstanceComponent>
        <attribute>ProcessType</attribute>
        <attributeValue>A16</attributeValue>
    </AttributeInstanceComponent>
    <AttributeInstanceComponent>
        <attribute>OutBiddingZone_Domain</attribute>
        <attributeValue>10YAT-APG------L</attributeValue>
    </AttributeInstanceComponent>
    <AttributeInstanceComponent>
        <attribute>TimeInterval</attribute>
        <attributeValue>{start_str}/{end_str}</attributeValue>
    </AttributeInstanceComponent>
</StatusRequest_MarketDocument>
        "#
        )
    }

    /// Rounds up the current time to the nearest 15-minute interval.
    fn round_up_to_nearest_15_minutes(time: DateTime<Utc>) -> DateTime<Utc> {
        let minutes = time.minute();
        let extra_minutes = if minutes % 15 == 0 { 0 } else { 15 - (minutes % 15) };
        time + Duration::minutes(extra_minutes as i64)
    }

    /// Calculates the timestamp for a given position, with a 15-minute decrement.
    fn calculate_timestamp_from_position(start_time: DateTime<Utc>, position: i32) -> DateTime<Utc> {
        // Each position is 15 minutes before the last, so we decrement by position * 15 minutes
        start_time - Duration::minutes(15 * (19 - position) as i64)
    }

    /// Parses and processes the API response.
    fn parse_response(response_text: &str) -> Result<Vec<(i64, f32)>, Box<dyn Error>> {
        let market_doc: GLMarketDocument = from_str(response_text)?;

        // Start from the current time, rounded up to the nearest 15 minutes
        let start_time = Self::round_up_to_nearest_15_minutes(Utc::now());
        let mut i = 0;

        // Extract and transform the data points
        let data: Vec<(i64, f32)> = market_doc
            .time_series
            .period
            .points
            .into_iter()
            .rev() // Reverse to get the last points first
            .take(19)
            .map(|point| {
                let consumption_total_kwh = point.quantity;
                let timestamp = Self::calculate_timestamp_from_position(start_time, i).timestamp();
                i += 1;
                (timestamp, consumption_total_kwh)
            })
            .collect();

        Ok(data)
    }

    /// Retrieves the power data for a specified range.
    pub fn get_power_data(&self, start: DateTime<Utc>, end: DateTime<Utc>) -> Result<Vec<(i64, f32)>, Box<dyn Error>> {
        let url = String::from_str("https://web-api.tp.entsoe.eu/api")?;

        let body = Self::create_request_body(start, end);

        // Send the POST request
        let response = self.client.post(&url)
            .header("Content-Type", "application/xml")
            .header("SECURITY_TOKEN", self.auth_token.clone())
            .body(body)
            .send()?;

        if response.status().is_success() {
            let response_text = response.text()?;
            Self::parse_response(&response_text)
        } else {
            Err(format!("[!] Error fetching data: {}", response.status()).into())
        }
    }
}