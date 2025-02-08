from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib
import os
from datetime import datetime

app = Flask(__name__)

class LogisticsPredictor:
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler()

    def create_sequences(self, df):
        """Create sequences for LSTM training based on logistics data."""
        # Ensure the date column exists, and replace 'current_date' with the correct name if needed
        df['DayOfWeek'] = pd.to_datetime(df['current_date']).dt.dayofweek
        df['Month'] = pd.to_datetime(df['current_date']).dt.month
        
        # Define features based on your dataset
        features = ['current_stock', 'required_time', 'weather_condition', 'shipping_cost']
        scaled_data = self.scaler.fit_transform(df[features])

        # Create sequences of data for LSTM
        X, y = [], []
        for i in range(len(scaled_data) - self.sequence_length):
            X.append(scaled_data[i:(i + self.sequence_length)])
            y.append(scaled_data[i + self.sequence_length, 0])

        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        """Build LSTM model architecture."""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train(self, train_data, epochs=50, batch_size=32):
        """Train the LSTM model."""
        X, y = self.create_sequences(train_data)
        self.model = self.build_model((self.sequence_length, X.shape[2]))
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=0.2, verbose=1)

    def predict(self, input_data):
        """Make predictions using the trained model."""
        # Check if input_data is a list of dictionaries (for multiple predictions)
        if isinstance(input_data, dict):
            input_data = [input_data]  # Wrap a single dictionary in a list

        df = pd.DataFrame(input_data)

        # Ensure the columns exist before processing
        if 'current_date' in df.columns:
            df['DayOfWeek'] = pd.to_datetime(df['current_date']).dt.dayofweek
            df['Month'] = pd.to_datetime(df['current_date']).dt.month
        else:
            raise ValueError("'current_date' column is missing in the input data.")

        # Define features based on your dataset
        features = ['current_stock', 'required_time', 'weather_condition', 'shipping_cost']

        # Ensure all necessary columns are in the dataframe
        if not all(feature in df.columns for feature in features):
            raise ValueError(f"Missing required columns: {', '.join([feature for feature in features if feature not in df.columns])}")

        # Scale the input data
        scaled_data = self.scaler.transform(df[features].tail(self.sequence_length))

        # Prepare sequence for prediction
        sequence = np.array([scaled_data])
        scaled_prediction = self.model.predict(sequence)

        # Reverse scaling and return prediction
        dummy = np.zeros((1, len(features)))
        dummy[0, 0] = scaled_prediction[0, 0]
        prediction = self.scaler.inverse_transform(dummy)[0, 0]

        return float(prediction)

    def save(self, folder_path='saved_model'):
        """Save model and scaler using new Keras format."""
        os.makedirs(folder_path, exist_ok=True)
        model_path = os.path.join(folder_path, 'model.keras')  # Use .keras format
        scaler_path = os.path.join(folder_path, 'scaler.pkl')

        self.model.save(model_path)  # Save in new format
        joblib.dump(self.scaler, scaler_path)

        return model_path, scaler_path

    def load(self, model_path, scaler_path):
        """Load saved model and scaler."""
        self.model = load_model(model_path, compile=False)  # Avoid auto-compiling
        self.model.compile(optimizer='adam', loss='mse')  # Explicitly define loss
        self.scaler = joblib.load(scaler_path)


# --- Train Model Once Before Running Flask ---
predictor = LogisticsPredictor()
model_path = 'saved_model/model.keras'
scaler_path = 'saved_model/scaler.pkl'

if os.path.exists(model_path) and os.path.exists(scaler_path):
    print("🔄 Loading existing model...")
    predictor.load(model_path, scaler_path)
else:
    print("🔄 Training model before starting the Flask server...")
    df = pd.read_csv('shipping_train.csv')  # Replace this with the correct CSV file path
    predictor.train(df)
    predictor.save('saved_model')
    print("✅ Model trained and saved!")

@app.route('/predict', methods=['POST'])
def predict_inventory():
    data = request.json

    # Ensure the input data is a list of dictionaries
    if isinstance(data, dict):
        data = [data]  # If a single dictionary is passed, wrap it in a list

    try:
        prediction = predictor.predict(data)
        return jsonify({'prediction': prediction})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    app.run(debug=True)
