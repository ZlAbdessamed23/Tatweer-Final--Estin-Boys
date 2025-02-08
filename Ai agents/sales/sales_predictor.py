import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, save_model, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
from datetime import datetime, timedelta

class SalesPredictor:
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler()
        self.history = None
        
    def create_sequences(self, df):
        """Create sequences for LSTM training."""
        # Create features
        df['DayOfWeek'] = pd.to_datetime(df['Date']).dt.dayofweek
        df['Month'] = pd.to_datetime(df['Date']).dt.month
        
        # Select features
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
    
    def train(self, train_data, validation_split=0.2, epochs=50, batch_size=32):
        """Train the LSTM model and save training history."""
        # Prepare sequences
        X, y = self.create_sequences(train_data)
        
        # Build and train model
        self.model = self.build_model((self.sequence_length, X.shape[2]))
        self.history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )
        
        return self.history
    
    def predict(self, input_data):
        """Make predictions using the trained model."""
        # Prepare input data
        df = pd.DataFrame(input_data)
        df['DayOfWeek'] = pd.to_datetime(df['Date']).dt.dayofweek
        df['Month'] = pd.to_datetime(df['Date']).dt.month
        
        features = ['Sales', 'Price', 'DayOfWeek', 'Month']
        scaled_data = self.scaler.transform(df[features].tail(self.sequence_length))
        
        # Make prediction
        sequence = np.array([scaled_data])
        scaled_prediction = self.model.predict(sequence)
        
        # Inverse transform
        dummy = np.zeros((1, len(features)))
        dummy[0, 0] = scaled_prediction[0, 0]
        prediction = self.scaler.inverse_transform(dummy)[0, 0]
        
        return float(prediction)
    
    def save(self, folder_path='saved_model'):
        """Save model, scaler, and generate report."""
        # Create folder if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)
        
        # Save model and scaler
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = os.path.join(folder_path, f'model_{timestamp}.h5')
        scaler_path = os.path.join(folder_path, f'scaler_{timestamp}.pkl')
        
        save_model(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
        # Save training history plot
        self.plot_training_history(folder_path, timestamp)
        
        return {
            'model_path': model_path,
            'scaler_path': scaler_path,
            'timestamp': timestamp
        }
    
    def load(self, model_path, scaler_path):
        """Load saved model and scaler."""
        self.model = load_model(model_path)
        self.scaler = joblib.load(scaler_path)
    
    def plot_training_history(self, folder_path, timestamp):
        """Plot and save training history."""
        plt.figure(figsize=(15, 6))
        
        # Plot training & validation loss
        plt.subplot(1, 2, 1)
        plt.plot(self.history.history['loss'], label='Training Loss')
        plt.plot(self.history.history['val_loss'], label='Validation Loss')
        plt.title('Model Loss During Training')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        # Save plot
        plt.savefig(os.path.join(folder_path, f'training_history_{timestamp}.png'))
        plt.close()
    
    def plot_predictions(self, actual_data, predictions, folder_path=None):
        """Plot actual vs predicted values."""
        plt.figure(figsize=(15, 6))
        
        # Plot actual vs predicted
        plt.plot(actual_data, label='Actual Sales', color='blue')
        plt.plot(predictions, label='Predicted Sales', color='red', linestyle='--')
        
        plt.title('Sales Prediction vs Actual')
        plt.xlabel('Time')
        plt.ylabel('Sales')
        plt.legend()
        
        if folder_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            plt.savefig(os.path.join(folder_path, f'predictions_{timestamp}.png'))
        
        plt.show()
        plt.close()

# Example usage
if __name__ == "__main__":
    # Load your data
    df = pd.read_csv('sales_train.csv')
    
    # Initialize predictor
    predictor = SalesPredictor()
    
    # Train model
    history = predictor.train(df)
    
    # Save model and visualizations
    save_info = predictor.save('saved_model')
    print(f"Model saved with timestamp: {save_info['timestamp']}")
    
    # Make predictions
    recent_data = df.tail(30)  # Last 30 days
    prediction = predictor.predict(recent_data)
    print(f"Next day sales prediction: {prediction:.2f}")
    
    # Plot predictions vs actual
    actual_values = df['Sales'].values[-50:]  # Last 50 days
    predictions = []
    
    # Generate predictions for comparison
    for i in range(len(actual_values) - 30):
        pred = predictor.predict(df.iloc[i:i+30])
        predictions.append(pred)
    
    # Plot results
    predictor.plot_predictions(
        actual_values[-len(predictions):],
        predictions,
        'saved_model'
    )