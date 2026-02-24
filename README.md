# 🎓Nilgiri College (NCAS)
A modern, sleek College Management System built with **Flask** and **SQLAlchemy**, featuring a glassmorphism-inspired dark theme.

EduStack has been customized for **Nilgiri College**, providing a centralized portal for students, faculty, and administration.

## ✨ Key Features

### 🎨 User Interface
- **Glassmorphism Design**: A premium, high-end aesthetic using blur and transparency effects.
- **Micro-interactions**: Smooth transitions and hover effects for an engaging experience.

### 🔐 Access Control
- **Streamlined Roles**: Dedicated experiences for Admin, Faculty, and Student.
- **Institutional Focus**: All data is pre-seeded for Nilgiri College.
- **Secure Sessions**: Powered by `Flask-Login` with RBAC enforcement for verification workflows.

### 📚 Academic Modules
- **6 Core Courses**: Including B.Sc Computer Science, B.A. English, B.Com Finance, BBA Logistics, B.Sc Psychology, and BCA.
- **Resource Distribution**: Faculty can upload study materials across courses.
- **Verification Workflow**: Content must be reviewed and verified by staff before becoming public.

##  Getting Started

### Prerequisites
- Python 3.8+ & pip

### Quick Setup

1. **Clone & Install**
   ```bash
   git clone https://github.com/c0zm3k/Bisna.git
   cd Bisna
   pip install -r requirements.txt
   ```

2. **Initialize Nilgiri Data**
   ```bash
   python bin/setup_db.py
   ```

3. **Run Application**
   ```bash
   python run.py
   ```
   Visit `http://127.0.0.1:8000`

## 👤 Test Credentials

The system is pre-seeded with specialized accounts for testing purposes.

### 🌟 Administrative Access
| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@ncas.edu` | `admin123` |

### 🎓 Institutional Access Registry
| Role | Email Pattern | Password | Count |
| :--- | :--- | :--- | :--- |
| **Faculty** | `faculty[1-10]@ncas.edu` | `password123` | 10 |
| **Student** | `stud[1-20]@ncas.edu` | `password123` | 20 |

> [!NOTE]
> All faculty accounts are pre-verified and associated with one of the 5 departmental courses. Students must use their `studX@ncas.edu` email and their registered number (e.g., `REG1001`) if re-registering.

## 📂 Project Structure
```text
EduStack/
├── app/               # Flask Application & Core Logic
├── bin/               # Maintenance (setup_db, clear_data)
├── instance/          # Database & Local Storage
├── .env               # Environment configuration
├── requirements.txt   # Dependencies
└── run.py             # Entry sequence (Port 8000)
```
