import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# Load interaction data
df = pd.DataFrame([
    {"retailer_id": 1, "product_id": 101},
    {"retailer_id": 2, "product_id": 101},
    {"retailer_id": 1, "product_id": 102},
    {"retailer_id": 3, "product_id": 103},
])

# Create user-item matrix
matrix = df.pivot_table(index='retailer_id', columns='product_id', aggfunc=lambda x: 1, fill_value=0)

# Compute similarity
similarity = cosine_similarity(matrix)

# Recommend products for retailer 1
retailer_index = matrix.index.get_loc(1)
similar_scores = similarity[retailer_index]
similar_retailers = matrix.index[similar_scores.argsort()[::-1][1:]]

# Get products viewed by similar retailers
recommended_products = df[df.retailer_id.isin(similar_retailers)].product_id.unique()
print(recommended_products)
