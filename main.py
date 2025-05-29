from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
import os
import pandas as pd
import numpy as np
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import load_model
from sklearn.metrics.pairwise import cosine_similarity
import io

app = FastAPI()

# Load models once
model_acne = load_model('models/model_mobilenetv2_V5.h5', compile=False)
model_flek = load_model('models/model_moblenetv2_V2_flek.h5', compile=False)
model_wrinkle = load_model('models/model_moblenetv2_V2_wrinkle.h5', compile=False)

# Load skincare data once
skincare_data = pd.read_excel('data/Toped_combined_scraper_preprocessed_with_labels.xlsx', engine='openpyxl')

def preprocess_image_file(image_file: UploadFile, target_size=(224, 224)):
    """Preprocess uploaded image"""
    try:
        img = Image.open(io.BytesIO(image_file.file.read()))
        img = img.resize(target_size)
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        return preprocess_input(img_array)
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def predict_condition(image_data):
    """Predict skin conditions using the models."""
    pred_acne = model_acne.predict(image_data)[0][0]
    pred_flek = model_flek.predict(image_data)[0][0]
    pred_wrinkle = model_wrinkle.predict(image_data)[0][0]
    return {
        'acne': float(pred_acne),
        'flek': float(pred_flek),
        'wrinkle': float(pred_wrinkle)
    }

def get_recommendations(condition, top_n=5):
    relevant_products = skincare_data[skincare_data['kategori'].str.lower() == condition]
    if relevant_products.empty:
        return []

    reference_idx = relevant_products['rating'].idxmax()
    reference_position = relevant_products.index.get_loc(reference_idx)

    features = relevant_products[['rating']].fillna(0)
    cosine_sim = cosine_similarity(features, features)
    sim_scores = sorted(list(enumerate(cosine_sim[reference_position])), key=lambda x: x[1], reverse=True)
    top_products = sim_scores[1:top_n + 1]

    recommendations = []
    for idx, score in top_products:
        product = relevant_products.iloc[idx]
        recommendations.append({
            'nama_produk': product['nama_produk'],
            'harga': product['harga'],
            'rating': product['rating'],
            'kategori': product['kategori'],
            'link_produk': product['link_produk'],
            'gambar_produk': product['gambar_produk'],
            'similarity_score': round(score, 4),
        })

    return recommendations


@app.post("/predict-skin/")
async def analyze_skin(
    image_depan: UploadFile = File(...),
    image_kiri: UploadFile = File(...),
    image_kanan: UploadFile = File(...)
):
    image_files = [image_depan, image_kiri, image_kanan]
    condition_sums = {'acne': 0, 'flek': 0, 'wrinkle': 0}
    valid_images = 0

    for image_file in image_files:
        processed = preprocess_image_file(image_file)
        if processed is None:
            continue
        prediction = predict_condition(processed)
        for key in condition_sums:
            condition_sums[key] += prediction[key]
        valid_images += 1

    if valid_images == 0:
        return JSONResponse(content={"error": "No valid images uploaded."}, status_code=400)

    avg_predictions = {k: v / valid_images for k, v in condition_sums.items()}
    primary_condition = max(avg_predictions.items(), key=lambda x: x[1])[0]

    recommendations = get_recommendations(primary_condition)

    return {
        "avg_predictions": avg_predictions,
        "primary_condition": primary_condition,
        "recommendations": recommendations
    }
