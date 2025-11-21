import pandas as pd

# Example: Load your data
df = pd.read_csv('UP_before_75.csv')

# Remove duplicates based on one column (e.g., 'email')
df = df.drop_duplicates(subset='extraction_date', keep='first')

# Save back if needed
df.to_csv('UP_cleaned.csv', index=False)
