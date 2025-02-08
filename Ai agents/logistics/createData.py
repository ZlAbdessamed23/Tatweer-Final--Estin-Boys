import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_shipping_dataset(n_samples=1000, start_date='2024-01-01'):
    """
    Generate logistics dataset with date-based shipping predictions
    """
    np.random.seed(42)
    
    # Generate base date
    start = datetime.strptime(start_date, '%Y-%m-%d')
    current_dates = [start + timedelta(days=x) for x in range(n_samples)]
    
    data = {
        'current_date': current_dates,
        'current_stock': np.random.normal(500, 150, n_samples).astype(int),
        'required_time': np.random.normal(7, 2, n_samples).round(1),
        'weather_condition': np.random.choice([1, 2, 3], n_samples, p=[0.7, 0.2, 0.1]),
        'shipping_cost': np.random.normal(500, 100, n_samples).round(2)
    }
    
    df = pd.DataFrame(data)
    
    # Clean up stock levels
    df['current_stock'] = df['current_stock'].clip(lower=0)
    
    # Calculate when to ship based on conditions
    def calculate_shipping_date(row):
        current_date = row['current_date']
        
        # Immediate shipping if stock is low or weather is severe
        if row['current_stock'] < 300 or row['weather_condition'] == 3:
            return current_date
        
        # Calculate days until shipping needed based on stock level
        stock_days_remaining = max(0, (row['current_stock'] - 300) / 30)  # Assume average daily demand of 30
        shipping_days = min(stock_days_remaining, row['required_time'])
        
        return current_date + timedelta(days=int(shipping_days))
    
    # Add shipping date
    df['when_should_i_ship'] = df.apply(calculate_shipping_date, axis=1)
    
    # Split into train (80%) and test (20%) sets
    train_size = int(0.8 * len(df))
    train_df = df[:train_size]
    test_df = df[train_size:]
    
    return train_df, test_df

if __name__ == "__main__":
    # Generate datasets
    train_df, test_df = generate_shipping_dataset(n_samples=1000)
    
    # Save to CSV files
    train_df.to_csv('shipping_train.csv', index=False)
    test_df.to_csv('shipping_test.csv', index=False)
    
    print("Training data shape:", train_df.shape)
    print("Test data shape:", test_df.shape)
    print("\nSample of training data:")
    print(train_df.head())
    
    # Show distribution of shipping delays
    print("\nShipping timing distribution (days until shipping):")
    train_df['days_until_shipping'] = (
        train_df['when_should_i_ship'] - train_df['current_date']
    ).dt.days
    print(train_df['days_until_shipping'].value_counts().sort_index())