# 🎓 Bisna (EduStack) - College Management System

A robust, modern, and mobile-responsive college management ecosystem designed for seamless interaction between students, teachers, and administrators. 

Built with **Python Flask** and featuring a sleek dark theme, Bisna streamlines syllabus management, note distribution, and institutional administration.

---

## ✨ Key Features

### 🔐 Multi-Role Access Control
- **Super Admin**: System-wide configuration and college management.
- **Admin**: User and department oversight for specific colleges.
- **Teachers/Seniors**: Resource contributors with verification privileges.
- **Students**: Quick access to syllabus-aligned notes and learning materials.

### 📚 Syllabus-Centric Learning
- Hierarchical structure: `Course` → `Semester` → `Subject` → `Unit` → `Topic`.
- Direct mapping of study materials to specific syllabus topics.

### 📝 Smart Notes Management
- Support for multiple formats: **PDF**, **Word**, **PPT**, **Videos (MP4)**, and **External Links**.
- **CDN Integration**: Powered by Cloudinary for high-speed file delivery.
- **Verification Workflow**: Content can be peer-reviewed or admin-approved before publication.

### 🎨 Modern UI/UX
- **Glassmorphism Design**: High-end aesthetic with dark mode and vibrant accents.
- **Mobile First**: Fully responsive layout for learning on the go.
- **Interactive Forms**: Real-time validation, password visibility toggles, and strength indicators.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask
- **Database**: PostgreSQL / SQLite (via SQLAlchemy ORM)
- **Frontend**: Vanilla JavaScript, CSS3 (Modern Flexbox/Grid), Jinja2 Templates
- **File Storage**: Cloudinary (CDN)
- **Security**: Flask-Login, CSRF Protection, Passlib

---

## 🚀 Quick Start

### 1️⃣ Local Development
```bash
# Clone the repository
git clone https://github.com/yourusername/bisna.git
cd bisna

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables (.env)
SECRET_KEY=your_random_secret
DATABASE_URL=sqlite:///app.db
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Initialize Database
python setup_db.py

# Run the app
python run.py
```

### 2️⃣ Cloud Deployment (Render/Heroku)
Apply the following settings for seamless hosting:
- **Build Command**: `./render-build.sh`
- **Start Command**: `gunicorn run:app`
- **Env Vars**: `SECRET_KEY`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

---

## 📸 Preview
*(Screenshots coming soon!)*

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
