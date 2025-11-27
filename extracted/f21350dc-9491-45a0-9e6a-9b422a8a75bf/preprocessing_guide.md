# Data Preprocessing Best Practices
    
    ## Missing Data Handling
    
    ### Techniques:
    1. **Deletion**: Remove rows with missing values
       - Use when: <5% missing data
       - Pros: Simple, no assumptions
       - Cons: Loss of information
    
    2. **Mean/Median Imputation**: Replace with average
       - Use when: Numerical data, symmetric distribution
       - Pros: Preserves sample size
       - Cons: Reduces variance
    
    3. **Mode Imputation**: Replace with most frequent value
       - Use when: Categorical data
       - Pros: Simple for categories
       - Cons: May introduce bias
    
    ## Feature Scaling
    
    ### Min-Max Scaling
    Formula: X_scaled = (X - X_min) / (X_max - X_min)
    Range: [0, 1]
    Use case: Neural networks, distance-based algorithms
    
    ### Standardization (Z-score)
    Formula: X_scaled = (X - μ) / σ
    Range: Mean=0, Std=1
    Use case: Algorithms assuming normal distribution
    
    ## Encoding Categorical Variables
    
    ### One-Hot Encoding
    - Converts categories to binary vectors
    - Example: [Red, Blue, Green] → [1,0,0], [0,1,0], [0,0,1]
    - Best for: Nominal data (no order)
    
    ### Label Encoding
    - Assigns integers to categories
    - Example: [Low, Medium, High] → [0, 1, 2]
    - Best for: Ordinal data (has order)