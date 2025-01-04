import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

df = pd.read_csv("/content/drive/MyDrive/DSCI560/DSCI_560_Chatbot_data/Lab3/Snig/final_dataset.csv")

# temp df filled with 0s for all nans just to fit a KNN model
df0 = df.fillna(0)

float_columns = df0.select_dtypes(include=['float64']).columns
float_df = df0[float_columns]
nbrs = NearestNeighbors(n_neighbors=4, algorithm='auto').fit(float_df)

# get distances and indices of neighbors for each row
distances, indices = nbrs.kneighbors(float_df)
nbr_indices = [i[1:] for i in indices]

# fill missing values in original df with 3 closest neighbor's means for the same attribute

for i in range(len(df)):
    for column in float_columns:
        if pd.isna(df.at[i, column]):
            means = [df.loc[ni, column] for ni in nbr_indices[i]]
            mean = [value for value in means if not pd.isna(value)]
            mean_value = np.mean(means) if means else 0
            df.at[i, column] = mean_value


df.to_csv('stocks_data.csv', index=False)

