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

class SalesPredictor:
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler()

    def create_sequences(self, df):
        """Create sequences for LSTM training."""
        df['DayOfWeek'] = pd.to_datetime(df['Date']).dt.dayofweek
        df['Month'] = pd.to_datetime(df['Date']).dt.month
        features = ['Sales', 'Price', 'DayOfWeek', 'Month']
        scaled_data = self.scaler.fit_transform(df[features])

        X, y = [], []
        for i in range(len(scaled_data) - self.sequence_length):
            X.append(scaled_data[i:(i + self.sequence_length)])
            y.append(scaled_data[i + self.sequence_length, 0])

        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        """Build LSTM model architecture."""
        model = Sequential([
            LSTM(100, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def train(self, train_data, epochs=50, batch_size=32):
        """Train the LSTM model."""
        X, y = self.create_sequences(train_data)
        self.model = self.build_model((self.sequence_length, X.shape[2]))
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=0.2, verbose=1)

    def predict(self, input_data):
        """Make predictions using the trained model."""
        df = pd.DataFrame(input_data)
        df['DayOfWeek'] = pd.to_datetime(df['Date']).dt.dayofweek
        df['Month'] = pd.to_datetime(df['Date']).dt.month
        features = ['Sales', 'Price', 'DayOfWeek', 'Month']
        scaled_data = self.scaler.transform(df[features].tail(self.sequence_length))

        sequence = np.array([scaled_data])
        scaled_prediction = self.model.predict(sequence)

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
predictor = SalesPredictor()
model_path = 'saved_model/model.keras'
scaler_path = 'saved_model/scaler.pkl'

if os.path.exists(model_path) and os.path.exists(scaler_path):
    print("🔄 Loading existing model...")
    predictor.load(model_path, scaler_path)
else:
    print("🔄 Training model before starting the Flask server...")
    df = pd.read_csv('sales_train.csv')
    predictor.train(df)
    predictor.save('saved_model')
    print("✅ Model trained and saved!")

@app.route('/predict', methods=['POST'])
def predict_sales():
    data = request.json
    prediction = predictor.predict(data)
    return jsonify({'prediction': prediction})

if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    app.run(debug=True)
