use std::collections::HashMap;
use std::path::PathBuf;
use candle_core::{Device, NdArray};
use candle_onnx::{onnx::ModelProto, read_file, simple_eval };
use candle_onnx::eval::Value;
use crate::utils::{generate_sin_components, select_best_device_inference};

pub struct PredictLoadService {
    device: Device,
    model: ModelProto,
}

impl Default for PredictLoadService {
    /// Creates a new instance of the prediction service.
    ///
    /// # Returns
    ///
    /// A new instance of the prediction service with a loaded model, using the best available device.
    fn default() -> PredictLoadService {
        // Select the best available device (GPU if available, otherwise CPU)
        let device = select_best_device_inference().expect("OS: Failed to select best device for inference");

        // Load the model using the selected device
        let model_path = PathBuf::from("assets/grid_predictor.onnx");
        let model = read_file(model_path).expect("OS: Failed to read model file");

        PredictLoadService { device, model }
    }
}

impl PredictLoadService {
    /// Predicts, based on a time series of electrical data, the load value for the next 15 minutes.
    ///
    /// # Arguments
    ///
    /// * `input_data` - A tuple containing the Unix timestamp and the load value at that time.
    ///
    /// # Returns
    ///
    /// Returns a result with the predicted value or an error message.
    pub fn predict_load(&self, input_data: Vec<(i64, f32)>) -> Result<f32, String> {
        // Check if the vector length is correct
        if input_data.len() != 19 {
            return Err("BUG: Input data must have 19 elements".to_string());
        }

        // Generate the sine components for the day and minutes
        let window_values: Vec<Vec<f32>> = input_data.iter().map(
            |(timestamp, load)| {
                let (day_sin, minute_sin) = generate_sin_components(*timestamp)
                    .map_err(|e| format!("BUG: Error generating sin components -> {}", e))?;

                Ok(vec![day_sin, minute_sin, *load])
            }
        ).collect::<Result<Vec<Vec<f32>>, String>>()?;

        // Transpose the window_values into a 3D shape of [1, 19, 3]
        let reshaped_window_values = vec![window_values]; // This creates a 1x19x3 shape
        println!("--> Window values shape: {:?}", reshaped_window_values.shape().unwrap());

        // Obtaining the graph from the model
        let graph = self.model.graph.as_ref().unwrap();

        // Create the inputs map
        let mut inputs = HashMap::new();

        // Create the tensor and insert it into inputs
        inputs.insert(graph.input[0].name.to_string(), Value::new(reshaped_window_values, &Device::Cpu).unwrap());

        // Evaluate the model
        match simple_eval(&self.model, inputs) {
            Ok(outputs) => {
                let output = outputs.get(&graph.output[0].name).unwrap();
                Ok(output.get(0).unwrap().to_scalar::<f32>().unwrap())
            }
            Err(e) => Err(format!("BUG: Error evaluating model -> {}", e))
        }
    }
}