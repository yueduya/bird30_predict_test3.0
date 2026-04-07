import numpy as np
from PIL.Image import Image
from ultralytics import YOLO
import cv2
import os


model = YOLO('model\\yolov8n.pt')

# model('F:\\pythoncode\\YOLOtest\\dateset\\images\\baitou.jpg', save=True, show=True)


BIRD_CLASS_IDS = {
    "bird": 14,  # 鸟
    'cat': 15,
    'dog': 16
}
# print("模型类别映射:", model.names)

def filter_bird_boxes(results):
    """
    筛选属于鸟类的检测框，并选择面积最大的
    """
    bird_boxes = []

    for result in results:
        # 获取所有检测框信息
        boxes = result.boxes.cpu().numpy()

        # 遍历每个检测框
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = box.conf[0]

            # 仅保留预定义的6类鸟类
            if cls_id in BIRD_CLASS_IDS.values():
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                area = (x2 - x1) * (y2 - y1)

                bird_boxes.append({
                    "coords": (x1, y1, x2, y2),
                    "area": area,
                    "conf": conf,
                    "cls_id": cls_id
                })

    # 按面积降序排序
    sorted_boxes = sorted(bird_boxes, key=lambda x: x["area"], reverse=True)[:1]
    return sorted_boxes


def detect_and_crop(img, output_dir="output"):
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 读取图像
    # img = cv2.imread(image_path)
    orig_img = img.copy()

    # 执行预测
    results = model.predict(img, conf=0.5, max_det=3)

    # 筛选检测框
    selected_boxes = filter_bird_boxes(results)

    if len(selected_boxes) == 0:
        # print('fdasssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss')
        return img, 0, 0, 0, 0

    # 裁剪并保存区域
    cropped_paths = []
    for idx, box in enumerate(selected_boxes):
        x1, y1, x2, y2 = box["coords"]
        crop = orig_img[y1:y2, x1:x2]
        # print('fdasssssssssggggggggggggggggggggggggggggggggggggggggggggggssssssssssssssssssss')
        return crop, x1, y1, x2, y2




        # # 保存裁剪结果
        # class_name = model.names[box["cls_id"]].replace(" ", "_")
        # filename = f"{class_name}__{idx + 1}.jpg"  # 双引号包裹，避免单引号冲突
        #
        # crop_path = os.path.join(output_dir, filename)
        # cv2.imwrite(crop_path, crop)
        # cropped_paths.append(crop_path)
        #
        # cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)



    # return cropped_paths


def add_frame(img_path):
    # 1. 读取图像
    img = Image.open(img_path).convert('RGB')

    # 添加YOLOV8
    # 转换为 numpy 数组
    np_image = np.array(img)  # 类型: numpy.ndarray (H x W x 3)

    # 将 RGB 转换为 BGR
    bgr_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

    # 添加框架


    # 将 BGR 转换为 RGB
    rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 转换为 PIL.Image 对象
    img = Image.fromarray(rgb_image)  # 类型: PIL.Image.Image
    return img



