
## 项目简介

这是一个基于深度学习的鸟类识别系统，使用FastAPI框架开发，支持用户上传图片进行鸟类识别，并提供聊天功能和鸟类信息浏览。

## 技术栈

- **后端框架**：FastAPI
- **数据库**：MySQL + MongoDB
- **深度学习框架**：PyTorch
- **前端**：HTML + CSS + JavaScript
- **认证**：JWT
- **其他**：YOLOv8（目标检测）、ResNet18 + CBAM（图像分类）

## 项目结构

```
.
├── app.py              # 主应用文件
├── cbam.py             # CBAM模型实现
├── config.py           # 配置文件
├── routers/            # 路由目录
│   ├── user.py         # 用户相关路由
│   └── chat.py         # 聊天相关路由
├── auth/               # 认证相关
│   ├── dependencies.py # 依赖注入
│   └── jwt_handler.py  # JWT处理
├── database/           # 数据库操作
│   ├── mysql.py        # MySQL操作
│   └── mongodb.py      # MongoDB操作
├── services/           # 服务目录
│   └── llm_service.py  # LLM服务调用
├── model/              # 模型文件
├── static/             # 静态文件
│   ├── css/            # 样式文件
│   └── images/         # 鸟类图片和简介
├── templates/          # 模板文件
└── .env                # 环境变量
```

## 主要功能

1. **鸟类识别**：用户上传图片，系统使用YOLOv8进行目标检测，然后使用ResNet18 + CBAM或VGG16进行分类，返回识别结果和置信度。

2. **用户系统**：支持用户注册、登录，使用JWT进行身份验证。

3. **聊天功能**：集成LLM服务，用户可以与AI助手进行对话，询问鸟类相关问题。

4. **鸟类信息浏览**：用户可以浏览不同鸟类的图片和简介。

5. **搜索功能**：用户可以搜索特定鸟类的信息。

## 如何运行

### 环境要求

- Python 3.7+
- PyTorch
- FastAPI
- MySQL
- MongoDB

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

在`.env`文件中配置以下环境变量：

```
# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=bird_recognition

# MongoDB配置
MONGO_URI=mongodb://localhost:27017
MONGO_DB=bird_chat

# JWT配置
SECRET_KEY=your_secret_key

# LLM配置
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

### 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 运行。

## 项目截图

### 首页

![首页](static/images/book.svg)
<img width="1872" height="884" alt="{F6460DF0-AA9E-4FB4-94E6-E9C2E2D88AAA}" src="https://github.com/user-attachments/assets/0d3d5347-903b-4617-8961-8395b2dd0f00" />

### 识别页面

![识别页面](static/images/book.svg)
<img width="1741" height="795" alt="{C201AE69-B36F-431B-8F2D-719DD5E3F1AE}" src="https://github.com/user-attachments/assets/0e60200b-8f1a-441f-a01f-a4d491790619" />
<img width="1883" height="906" alt="image" src="https://github.com/user-attachments/assets/e18bf901-a977-4550-b795-c8a9f9912adf" />
<img width="1608" height="828" alt="image" src="https://github.com/user-attachments/assets/87415660-a602-4216-ba3e-2b0a7c9fe22a" />


### 聊天页面

![聊天页面](static/images/book.svg)
<img width="1033" height="875" alt="{A460A843-CBA3-4DA7-AE94-64E754F6CCEC}" src="https://github.com/user-attachments/assets/28a7ba9e-463c-4422-aa95-d14f5658a4d7" />



## 联系方式

- 项目链接：[GitHub链接]()
- 作者：[YueDuYa]()
