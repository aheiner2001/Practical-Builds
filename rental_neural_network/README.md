# Bike Rental Demand Prediction

A neural network model built to forecast hourly bike rental demand using weather, time, and calendar features.

## Overview

This project uses a feedforward neural network with TensorFlow/Keras to predict the number of bike rentals per hour. The model is trained on historical bike-sharing data and uses engineered features for improved performance.

## What it does

- Loads and cleans hourly bike rental data
- Engineers cyclical time features for hour, day, and month
- Includes weather-related predictors such as temperature, humidity, wind speed, and dew point
- Applies Min-Max scaling and model training with early stopping
- Evaluates model performance using RMSE and R²
- Exports predictions for a holdout test set

## Results

- RMSE: ~89.3
- R²: ~0.93

## Tech stack

- Python
- TensorFlow / Keras
- pandas, NumPy, scikit-learn
- Matplotlib, Seaborn
