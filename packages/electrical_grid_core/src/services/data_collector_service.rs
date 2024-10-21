use reqwest::blocking::Client;
use serde::Deserialize;
use std::error::Error;
use quick_xml::de::from_str;

#[derive(Deserialize, Debug)]
struct Point {
    position: i32,
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

    /// Retrieves the power data for a specified range.
    pub fn get_power_data(&self, start: &str, end: &str) -> Result<Vec<(i64, f32)>, Box<dyn Error>> {
        let url = format!(
            "https://transparency.entsoe.eu/api?securityToken={}&documentType=A65&processType=A01&outBiddingZone_Domain=10YAT-APG------L&periodStart={}&periodEnd={}",
            self.auth_token, start, end
        );

        // Request body in XML format
        let body = format!(r#"
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
                <attributeValue>A01</attributeValue>
            </AttributeInstanceComponent>
            <AttributeInstanceComponent>
                <attribute>OutBiddingZone_Domain</attribute>
                <attributeValue>10YAT-APG------L</attributeValue>
            </AttributeInstanceComponent>
            <AttributeInstanceComponent>
                <attribute>TimeInterval</attribute>
                <attributeValue>{start}/{end}</attributeValue>
            </AttributeInstanceComponent>
        </StatusRequest_MarketDocument>
        "#);

        // Send the POST request
        let response = self.client.post(&url)
            .header("Content-Type", "application/xml")
            .body(body)
            .send()?;

        // Check the result
        if response.status().is_success() {
            let response_text = response.text()?;

            // Parse the XML response
            let market_doc: GLMarketDocument = from_str(&response_text)?;

            // Collect the last 19 data points
            let data: Vec<(i64, f32)> = market_doc
                .time_series
                .period
                .points
                .into_iter()
                .rev() // reverse to get last points first
                .take(19)
                .map(|point| {
                    // Convert MAW to kWh (1 MW = 1000 kWh)
                    let consumption_total_kwh = point.quantity * 1000.0;
                    let timestamp = point.position as i64; // Assuming position represents time in seconds
                    (timestamp, consumption_total_kwh)
                })
                .collect();

            Ok(data)
        } else {
            Err(format!("Error fetching data: {}", response.status()).into())
        }
    }
}