# backend/ml_model.py
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def get_ml_recommendations(retailer_id: int, interaction_data: list):
    df = pd.DataFrame(interaction_data)

    matrix = df.pivot_table(index='retailer_id', columns='product_id', aggfunc=lambda x: 1, fill_value=0)

    if retailer_id not in matrix.index:
        return []

    similarity = cosine_similarity(matrix)
    retailer_index = matrix.index.get_loc(retailer_id)
    similar_scores = similarity[retailer_index]
    similar_retailers = matrix.index[similar_scores.argsort()[::-1][1:]]

    recommended_products = df[df.retailer_id.isin(similar_retailers)].product_id.unique().tolist()
    return recommended_products
