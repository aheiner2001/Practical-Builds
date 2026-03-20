
Bike Rental Demand Prediction
A neural network model built to predict hourly bike rental demand using weather, time, and calendar features.
Overview
This project uses a feedforward neural network (built with TensorFlow/Keras) to predict the total number of bike rentals per hour. The model was trained on historical bike-sharing data that includes weather conditions, temperature, humidity, wind speed, and time-based features.
What It Does

Loads and cleans hourly bike rental data
Engineers features like cyclical time encodings (hour, day, month), dew point, prime riding conditions, and working hour indicators
Scales features using Min-Max normalization
Trains a simple dense neural network with early stopping
Evaluates performance using RMSE and R² score
Exports predictions on a holdout test set

Results

RMSE: ~89.3
R²: ~0.93

Tech Stack
Python, TensorFlow/Keras, Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn
