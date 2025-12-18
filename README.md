# EduStack - College Management System

A modern, mobile-responsive college management system with a DARKYN-inspired dark theme.

## 🚀 Easy Zero-Cost Deployment (Render)

### 1. Push to GitHub
Upload this project to a private or public GitHub repository.

### 2. Configure Render Web Service
> [!IMPORTANT]
> Render often defaults to `gunicorn app:app`. You **MUST** change it to the following in your Render Dashboard settings or it will crash:
- **Build Command**: `./render-build.sh`
- **Start Command**: `gunicorn run:app`

### 3. Set Environment Variables
In the Render dashboard, add the following variables:
- `SECRET_KEY`: (any long random string)
- `CLOUDINARY_CLOUD_NAME`: (your Cloudinary name)
- `CLOUDINARY_API_KEY`: (your Cloudinary API key)
- `CLOUDINARY_API_SECRET`: (your Cloudinary API secret)

## ✨ Key Features
- **Modern UI**: Dark theme with orange accents and glassmorphism.
- **Responsive**: Fully optimized for mobile and desktop.
- **Security**: Password visibility toggles & strength indicators.
- **Content**: Support for PDF, Word, and Video (MP4) uploads.
- **Storage**: Integrated with Cloudinary for free CDN file hosting.

## 🛠️ Local Setup
1. `python -m venv .venv`
2. `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
3. `pip install -r requirements.txt`
4. `python setup_db.py`
5. `python run.py`
