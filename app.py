import cv2
from PIL import Image, ImageDraw
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import torch
import torch.nn.functional as F
import pandas as pd
import base64
from io import BytesIO
import numpy as np
from torchvision import transforms
import uuid
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

import yolofunc
from cbam import build_cbam_resnet18
from routers import user, chat

MODEL_CACHE = {}
IDX_TO_LABELS = None
device = torch.device('cpu')


def preload_models():
    """应用启动时预加载所有模型"""
    global IDX_TO_LABELS
    
    IDX_TO_LABELS = np.load(
        r'F:\pythoncode\bird30_predict_test\try_one\checkpoint\idx_to_labels.npy',
        allow_pickle=True
    ).item()
    
    MODEL_CACHE["Resnet18_CBAM"] = _load_cbam_model()
    MODEL_CACHE["vgg16"] = _load_simple_model(r"model/best-nopre-vgg16-0.998.pth")
    MODEL_CACHE["Resnet18"] = _load_simple_model(r"model/resnet18_BATCH-50_Adam_all_layer.pth")
    
    print("✅ 所有模型预加载完成")


def _load_cbam_model():
    checkpoint = torch.load(r'model/new-2.1best-preCBAM-res18-0.997.pth', map_location=device, weights_only=False)
    model = build_cbam_resnet18(n_class=checkpoint['num_classes'])
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    return model


def _load_simple_model(path):
    model = torch.load(path, map_location=device, weights_only=False)
    model.eval()
    return model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    if not os.path.exists('temp'):
        os.makedirs('temp')
    preload_models()
    yield


app = FastAPI(title="鸟类识别系统", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(chat.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def generate_chart(outputs, idx_to_labels):
    """线程安全的图表生成"""
    fig = Figure(figsize=(22, 10))
    ax = fig.add_subplot(111)
    
    pred_softmax = F.softmax(outputs, dim=1)
    x = list(idx_to_labels.values())
    y = pred_softmax.cpu().detach().numpy()[0] * 100
    
    bars = ax.bar(x, y, 0.45)
    ax.bar_label(bars, fmt='%.2f', fontsize=15)
    ax.set_title("预测概率图", fontsize=30)
    ax.set_xlabel('类别', fontsize=20)
    ax.set_ylabel('置信度', fontsize=20)
    for label in ax.get_xticklabels():
        label.set_rotation(45)
    
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def process_image(image_bytes):
    """处理上传的图片"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    bgr_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    cropped, x1, y1, x2, y2 = yolofunc.detect_and_crop(bgr_image)
    
    rgb_image = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb_image)
    
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    processed_img = preprocess(img).unsqueeze(0)
    return processed_img, x1, y1, x2, y2


@app.get("/index", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径重定向到首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/detail/{group}/{photo}", response_class=HTMLResponse)
async def detail(request: Request, group: str, photo: str):
    with open(f'static/images/{group}/简介.txt', 'r', encoding='utf-8') as f:
        txt_content = f.read()
    
    image_dir = os.path.join('static', 'images', group)
    images = [f'{group}/{img}' for img in os.listdir(image_dir) if img.endswith(('.jpg', '.png'))]
    
    return templates.TemplateResponse("detail.html", {
        "request": request,
        "group": group,
        "photo": photo,
        "images": images,
        "txt_content": txt_content
    })


@app.get("/predict_page", response_class=HTMLResponse)
async def predict_page(request: Request):
    return templates.TemplateResponse("predict.html", {"request": request})


@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    model: str = Form(...)
):
    start = time.time()
    
    ext = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    temp_path = os.path.join('temp', unique_filename)
    
    try:
        content = await image.read()
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        current_model = MODEL_CACHE.get(model)
        if current_model is None:
            return JSONResponse({"success": False, "error": "模型不存在"}, status_code=400)
        
        processed_img, x1, y1, x2, y2 = process_image(content)
        
        with torch.no_grad():
            outputs = current_model(processed_img)
            probs = F.softmax(outputs, dim=1)
            top_probs, top_classes = torch.topk(probs, 10)
            
            confs = top_probs.cpu().numpy().squeeze().tolist()
            pred_ids = top_classes.cpu().numpy().squeeze().tolist()
        
        results = []
        for i in range(len(pred_ids)):
            class_name = IDX_TO_LABELS[pred_ids[i]]
            results.append({
                'Class': class_name,
                'Class_ID': int(pred_ids[i]),
                'Confidence(%)': round(confs[i] * 100, 2),
                'group': class_name
            })
        
        chart_base64 = generate_chart(outputs, IDX_TO_LABELS)
        
        img = Image.open(BytesIO(content))
        draw = ImageDraw.Draw(img)
        draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=2)
        
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        end = time.time()
        print(f"预测耗时: {end - start:.2f}s")
        
        return {
            "success": True,
            "data": {
                "framed_image": f"data:image/png;base64,{img_base64}",
                "predictions": results,
                "chart": chart_base64,
                "reference_images": [
                    {"path": f"/static/images/{results[0]['Class']}/{i}.jpg"}
                    for i in range(1, 6)
                ]
            }
        }
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.api_route("/search", methods=["GET", "POST"])
async def search(request: Request, folder: str = "乌鸦"):
    if request.method == "POST":
        form = await request.form()
        folder = form.get("folder", "乌鸦")
    
    folder_path = os.path.join('static', 'images', folder)
    
    if not os.path.exists(folder_path):
        return {"folder": folder, "images": [], "exists": False}
    
    images = [
        {"url": f"/static/images/{folder}/{f}", "name": f}
        for f in os.listdir(folder_path)
        if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))
    ]
    
    with open(f'static/images/{folder}/简介.txt', 'r', encoding='utf-8') as f:
        txt_content = f.read()
    
    if request.method == "POST":
        return {
            "folder": folder,
            "images": images,
            "exists": len(images) > 0,
            "photo": images[0]['url'] if images else "",
            "txt_content": txt_content
        }
    
    return templates.TemplateResponse("search.html", {
        "request": request,
        "default_folder": folder,
        "default_images": images,
        "txt_content": txt_content,
        "photo": "1.jpg"
    })


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)