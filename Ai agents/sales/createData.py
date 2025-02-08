import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. Set up basic parameters
start_date = datetime(2022, 1, 1)
end_date = datetime(2023, 12, 31)
dates = pd.date_range(start_date, end_date)

# 2. Define products with their base prices and seasonal patterns
products = {
    'Winter Jacket': {
        'base_price': 89.99,
        'base_sales': 25000,  # Higher base sales
        'sales_std': 5000,    # Standard deviation for sales variation
        'winter_boost': 1.8,
        'summer_penalty': 0.3,
    },
    'T-Shirt': {
        'base_price': 19.99,
        'base_sales': 50000,  # Very high base sales for common item
        'sales_std': 8000,
        'winter_penalty': 0.4,
        'summer_boost': 1.5,
    },
    'Umbrella': {
        'base_price': 24.99,
        'base_sales': 15000,
        'sales_std': 3000,
        'spring_boost': 1.4,
        'fall_boost': 1.3,
    },
    'Sunglasses': {
        'base_price': 49.99,
        'base_sales': 20000,
        'sales_std': 4000,
        'summer_boost': 2.0,
        'winter_penalty': 0.5,
    },
    'Sneakers': {
        'base_price': 79.99,
        'base_sales': 35000,
        'sales_std': 6000,
        'seasonal_variance': 0.2,
    }
}

def get_season(date):
    """Determine season based on month."""
    month = date.month
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    else:
        return 'Fall'

def generate_product_sales(dates, product_info):
    """Generate sales data for a specific product."""
    sales_data = []
    
    for date in dates:
        season = get_season(date)
        # Generate base sales with higher numbers
        base_sales = np.random.normal(
            product_info['base_sales'], 
            product_info['sales_std']
        )
        
        # Apply seasonal adjustments
        seasonal_multiplier = 1.0
        if season == 'Winter' and 'winter_boost' in product_info:
            seasonal_multiplier = product_info['winter_boost']
        elif season == 'Summer' and 'summer_boost' in product_info:
            seasonal_multiplier = product_info['summer_boost']
        elif season == 'Winter' and 'winter_penalty' in product_info:
            seasonal_multiplier = product_info['winter_penalty']
        elif season == 'Summer' and 'summer_penalty' in product_info:
            seasonal_multiplier = product_info['summer_penalty']
        elif season == 'Spring' and 'spring_boost' in product_info:
            seasonal_multiplier = product_info['spring_boost']
        elif season == 'Fall' and 'fall_boost' in product_info:
            seasonal_multiplier = product_info['fall_boost']
        
        # Apply weekday/weekend effect (bigger impact for retail)
        weekend_multiplier = 1.5 if date.dayofweek >= 5 else 1.0
        
        # Special events multiplier (holidays, etc.)
        special_multiplier = 1.0
        # Black Friday
        if date.month == 11 and 20 <= date.day <= 27:
            special_multiplier = 2.5
        # Christmas season
        elif date.month == 12 and 15 <= date.day <= 24:
            special_multiplier = 2.0
        
        # Calculate final sales
        final_sales = base_sales * seasonal_multiplier * weekend_multiplier * special_multiplier
        
        # Calculate price with some random variation
        base_price = product_info['base_price']
        price_variation = np.random.uniform(-0.1, 0.1)  # ±10% price variation
        final_price = base_price * (1 + price_variation)
        
        sales_data.append({
            'Date': date,
            'Product': product_info,
            'Season': season,
            'Sales': max(0, round(final_sales, 2)),
            'Price': round(final_price, 2)
        })
    
    return sales_data

# 3. Generate data for all products
all_sales_data = []
for product_name, product_info in products.items():
    product_sales = generate_product_sales(dates, {
        'name': product_name,
        **product_info
    })
    all_sales_data.extend(product_sales)

# 4. Create DataFrame
df = pd.DataFrame(all_sales_data)
df['Product_Name'] = df['Product'].apply(lambda x: x['name'])
df = df.drop('Product', axis=1)

# 5. Split into train and test sets (80/20 split)
split_date = dates[int(len(dates) * 0.8)]
train_df = df[df['Date'] < split_date]
test_df = df[df['Date'] >= split_date]

# 6. Save to CSV
train_df.to_csv('sales_train.csv', index=False)
test_df.to_csv('sales_test.csv', index=False)

# 7. Display sample and summary statistics
print("\nSample of training data:")
print(train_df.head())
print("\nSales Statistics:")
print(df.groupby('Product_Name')['Sales'].describe())
print("\nShape of training data:", train_df.shape)
print("Shape of test data:", test_df.shape)