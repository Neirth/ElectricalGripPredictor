use candle_core::Device;
use chrono::{DateTime, Datelike, Timelike};
use candle_core::utils::{cuda_is_available, metal_is_available};

/// Genera los componentes sinusoidales del día y los minutos a partir de un timestamp.
pub(crate) fn generate_sin_components(timestamp: i64) -> Result<(f32, f32), String> {
    let naive_datetime = DateTime::from_timestamp(timestamp, 0)
        .ok_or("Error al convertir el timestamp")?;

    let day_of_year = naive_datetime.ordinal();
    let minutes_of_day = naive_datetime.hour() * 60 + naive_datetime.minute();

    let day_sin = (2.0 * std::f32::consts::PI * day_of_year as f32 / 365.0).sin();
    let minute_sin = (2.0 * std::f32::consts::PI * minutes_of_day as f32 / 1440.0).sin();

    Ok((day_sin, minute_sin))
}

pub(crate) fn select_best_device_inference() -> Result<Device, String> {
    if cuda_is_available() {
        Ok(Device::new_cuda(0).unwrap())
    } else if metal_is_available() {
        Ok(Device::new_metal(0).unwrap())
    } else {
        Ok(Device::Cpu)
    }
}