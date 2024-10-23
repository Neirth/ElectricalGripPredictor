use std::path::PathBuf;
use tract_onnx::prelude::*;
use crate::utils::generate_sin_components;

pub struct PredictLoadService {
    model: RunnableModel<TypedFact, Box<dyn TypedOp>, Graph<TypedFact, Box<dyn TypedOp>>>,
}

impl Default for PredictLoadService {
    fn default() -> PredictLoadService {
        let model_path = PathBuf::from("assets/grid_predictor.onnx");
        let model = tract_onnx::onnx()
            .model_for_path(model_path)
            .expect("OS: Failed to read model file")
            .with_input_fact(0, InferenceFact::dt_shape(f32::datum_type(), tvec!(1, 19, 3)))
            .expect("OS: Failed to set input shape")
            .into_optimized()
            .expect("OS: Failed to optimize model")
            .into_runnable()
            .expect("OS: Failed to create runnable model");

        PredictLoadService { model }
    }
}

impl PredictLoadService {
    pub fn predict_load(&self, input_data: Vec<(i64, f32)>) -> Result<f32, String> {
        if input_data.len() != 19 {
            return Err("BUG: Input data must have 19 elements".to_string());
        }

        let window_values: Vec<f32> = input_data.iter().flat_map(
            |(timestamp, load)| {
                let (day_sin, minute_sin) = generate_sin_components(*timestamp)
                    .map_err(|e| format!("BUG: Error generating sin components -> {}", e)).unwrap();

                vec![day_sin, minute_sin, *load]
            }
        ).collect();

        // Convert the values to a Tensor with the appropriate shape [1, 19, 3]
        let input_tensor = Tensor::from_shape(&[1, 19, 3], &*window_values)
            .map_err(|e| format!("BUG: Error creating input tensor -> {}", e))?;

        // Run the model
        let result = self.model.run(
            tvec!(input_tensor.into())).map_err(|e| format!("BUG: Error running model -> {}", e)
        )?;

        // Extract the output value
        let output = result[0].to_scalar::<f32>().map_err(|e|
            format!("BUG: Error extracting output -> {}", e)
        )?;

        Ok(*output)
    }
}