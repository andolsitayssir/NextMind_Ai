# 🧠 NextMind - AI-Powered Psychological Assessment Platform

![NextMind Banner](https://img.shields.io/badge/NextMind-Psychological%20Assessment-764ba2?style=for-the-badge&logo=brain&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> **NextMind** is an advanced psychological assessment platform that leverages AI to provide comprehensive personality analysis through validated psychometric tests including Big Five, DISC, Well-being, and Emotional Intelligence assessments.

---



## ✨ Features

### 🎯 Core Features
- **Multi-Language Support** (French, English, Arabic)
- **4 Validated Psychometric Tests**:
  - Big Five Personality Traits
  - DISC Behavioral Assessment
  - Professional Well-being Index
  - Resilience & Emotional Intelligence

### 🤖 AI-Powered Features
- **Ai powered Assemessment**
- - **Detailed Analysis**
- **NextMind CoachAI**



### 🎨 User Experience
- **Responsive Design**: Beautiful glassmorphism UI
- **Full-Page Scrolling**: Smooth section-by-section navigation
- **Interactive Reports**: Dynamic visualizations and progress indicators
- **Accessibility**: WCAG 2.1 compliant, RTL support for Arabic

---

## 🛠️ Tech Stack

### Backend
- **Django 5.1** - Python web framework
- **Python 3.11+** - Programming language
- **PostegrSQL** - Database
- **Llama3** integration

### Frontend
- **HTML5 / CSS3** - Modern web standards
- **JavaScript (Vanilla)** - No framework dependencies
- **Responsive Design** - Mobile-first approach

### AI & Analysis
- **Custom AI Coach** - Intelligent conversation system
- **Psychometric Algorithms** - Validated scoring systems
- **Natural Language Processing** - Multi-language analysis

---

## 🚀 Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/NextMind.git
cd NextMind
```

### Step 2: Create Virtual Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
LANGUAGE_CODE=fr-fr
TIME_ZONE=UTC
```

### Step 5: Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Step 6: Collect Static Files
```bash
python manage.py collectstatic
```

### Step 7: Run Development Server
```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** in your browser 🎉




## 🎓 Assessments

### Big Five Personality Traits
Measures five core personality dimensions:
- **Openness to Experience** - Creativity, curiosity
- **Conscientiousness** - Organization, responsibility
- **Extraversion** - Sociability, assertiveness
- **Agreeableness** - Cooperation, empathy
- **Emotional Stability** - Stress management, resilience

### DISC Behavioral Profile
Analyzes behavioral tendencies:
- **Dominance** - Results-oriented, direct
- **Influence** - Enthusiastic, optimistic
- **Steadiness** - Patient, supportive
- **Compliance** - Accurate, analytical

### Professional Well-being
Evaluates workplace satisfaction across multiple dimensions

### Resilience & Emotional Intelligence
Measures stress management and emotional awareness

---

embers)

</div>
