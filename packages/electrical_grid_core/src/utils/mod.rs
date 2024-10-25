use chrono::{DateTime, Datelike, Timelike, Utc};

/// Generates the sinusoidal components of the day and minutes from a timestamp.
pub(crate) fn generate_sin_components(timestamp: i64) -> Result<(f32, f32), String> {
    let naive_datetime = DateTime::from_timestamp(timestamp, 0)
        .ok_or("Error converting the timestamp")?;

    let day_of_year = naive_datetime.ordinal();
    let minutes_of_day = naive_datetime.hour() * 60 + naive_datetime.minute();

    let day_sin = (2.0 * std::f32::consts::PI * day_of_year as f32 / 365.0).sin();
    let minute_sin = (2.0 * std::f32::consts::PI * minutes_of_day as f32 / 1440.0).sin();

    Ok((day_sin, minute_sin))
}

/// Normalizes a value to the range [0, 1].
pub(crate) fn normalize(value: f32, min: f32, max: f32) -> f32 {
    if max > min {
        (value - min) / (max - min)
    } else {
        0.0 // Handles case where min == max
    }
}

/// Denormalizes a value to the original range.
pub(crate) fn denormalize(normalized_value: f32, min: f32, max: f32) -> f32 {
    if max > min {
        normalized_value * (max - min) + min
    } else {
        min // Handles case where min == max
    }
}

/// Converts Unix epoch time to an ISO 8601 formatted string.
pub(crate) fn unix_epoch_to_iso8601(epoch_time: i64) -> String {
    let datetime: DateTime<Utc> = DateTime::from_timestamp(epoch_time, 0).unwrap();
    datetime.to_rfc3339()
}