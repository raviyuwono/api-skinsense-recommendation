from fastapi import FastAPI, File, UploadFile, HTTPException
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from PIL import Image
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import io
import os

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# Load model ML
model_acne = load_model('models/model_mobilenetv2_V5.h5', compile=False)
model_flek = load_model('models/model_moblenetv2_V2_flek.h5', compile=False)
model_wrinkle = load_model('models/model_moblenetv2_V2_wrinkle.h5', compile=False)

# Load data rekomendasi produk
data_skincare = pd.read_excel('data/Toped_combined_scraper_preprocessed_with_labels.xlsx', engine='openpyxl')

async def preprocess_image(file: UploadFile, target_size=(224, 224)):
    try:
        # Menggunakan await untuk membaca file
        file_bytes = await file.read()
        img = Image.open(io.BytesIO(file_bytes))
        img = img.resize(target_size)
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        return preprocess_input(img_array)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {e}")

# Prediksi kondisi kulit
def predict_skin_condition(image_array):
    # Prediksi dari model
    pred_acne = model_acne.predict(image_array)[0][0]
    pred_flek = model_flek.predict(image_array)[0][0]
    pred_wrinkle = model_wrinkle.predict(image_array)[0][0]
    
    # Hitung total untuk normalisasi
    total = pred_acne + pred_flek + pred_wrinkle
    
    # Ubah menjadi persentase
    predictions = {
        'acne': float(pred_acne / total * 100),
        'flek': float(pred_flek / total * 100),
        'wrinkle': float(pred_wrinkle / total * 100)
    }
    
    # Ambil kondisi dengan persentase tertinggi
    condition = max(predictions, key=predictions.get)
    
    # Format output
    formatted_predictions = {
        "Primary condition": f"{condition} ({predictions[condition]:.2f}%)",
        "Acne likelihood": f"{predictions['acne']:.2f}%",
        "Flek likelihood": f"{predictions['flek']:.2f}%",
        "Wrinkle likelihood": f"{predictions['wrinkle']:.2f}%"
    }
    
    return condition, formatted_predictions



# Rekomendasi produk
def recommend_products(condition, top_n=6):
    produk_relevan = data_skincare[data_skincare['kategori'].str.lower() == condition]
    if produk_relevan.empty:
        return []

    idx_referensi = produk_relevan['rating'].idxmax()
    fitur = produk_relevan[['rating']].fillna(0)
    cosine_sim = cosine_similarity(fitur, fitur)
    skor_sim = sorted(list(enumerate(cosine_sim[produk_relevan.index.get_loc(idx_referensi)])), key=lambda x: x[1], reverse=True)
    
    top_n = min(top_n, len(produk_relevan) - 1)
    produk_top = skor_sim[1:top_n + 1]
    
    rekomendasi = []
    for idx, skor in produk_top:
        produk = produk_relevan.iloc[idx]
        rekomendasi.append({
            'nama_produk': produk['nama_produk'],
            'harga': produk['harga'],
            'rating': produk['rating'],
            'kategori': produk['kategori'],
            'link_produk': produk['link_produk'],
            'gambar_produk': produk['gambar_produk'],
            'similarity_score': skor,
        })
    return rekomendasi

# Endpoint untuk prediksi dan rekomendasi
@app.post("/predict-recommend/")
async def predict_and_recommend(file: UploadFile = File(...)):
    if not file.filename.endswith(('jpg', 'jpeg', 'png')):
        raise HTTPException(status_code=400, detail="Invalid file type. Upload a JPG or PNG image.")
    
    # Preprocess gambar
    image_array = await preprocess_image(file)
    
    # Prediksi kondisi kulit
    condition, predictions = predict_skin_condition(image_array)
    
    # Dapatkan rekomendasi produk
    recommendations = recommend_products(condition)
    
    if not recommendations:
        raise HTTPException(status_code=404, detail=f"No recommendations found for condition: {condition}")
    
    return {
        "predictions": predictions,
        "main_condition": condition,
        "recommendations": recommendations
    }
