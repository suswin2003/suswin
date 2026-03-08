"""
Intelligent Resume Screening and Automated Interview Notification System
MCA Final Year Project
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import sqlite3
import os
import json
import re
import smtplib
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pdfplumber
import docx
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
app = Flask(__name__)
app.secret_key = "resume_screener_mca_2024"

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "resume_screener.db")
ALLOWED_EXTENSIONS = {"pdf", "docx"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.executescript("""
    CREATE TABLE IF NOT EXISTS job_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        core_skills TEXT NOT NULL,       -- JSON array
        tools TEXT NOT NULL,             -- JSON array
        project_keywords TEXT NOT NULL,  -- JSON array
        internship_keywords TEXT NOT NULL,
        experience_keywords TEXT NOT NULL,
        core_weight REAL DEFAULT 0.40,
        tools_weight REAL DEFAULT 0.25,
        projects_weight REAL DEFAULT 0.15,
        internship_weight REAL DEFAULT 0.10,
        experience_weight REAL DEFAULT 0.10,
        min_threshold INTEGER DEFAULT 50,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        job_role_id INTEGER NOT NULL,
        name TEXT,
        email TEXT,
        phone TEXT,
        raw_text TEXT,
        skills_found TEXT,          -- JSON
        tools_found TEXT,           -- JSON
        projects_found TEXT,        -- JSON
        internship_found TEXT,      -- JSON
        experience_found TEXT,      -- JSON
        core_score REAL DEFAULT 0,
        tools_score REAL DEFAULT 0,
        projects_score REAL DEFAULT 0,
        internship_score REAL DEFAULT 0,
        experience_score REAL DEFAULT 0,
        total_score REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',   -- pending / shortlisted / rejected
        rejection_reason TEXT,
        email_sent INTEGER DEFAULT 0,
        email_sent_at TIMESTAMP,
        filename TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_role_id) REFERENCES job_roles(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

                    
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        login_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS email_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        smtp_host TEXT DEFAULT 'smtp.gmail.com',
        smtp_port INTEGER DEFAULT 587,
        sender_email TEXT,
        sender_password TEXT,
        email_subject TEXT DEFAULT 'Interview Invitation - {job_role}',
        email_body TEXT DEFAULT 'Dear {name},\n\nCongratulations! We are pleased to inform you that your application for the position of {job_role} has been shortlisted.\n\nWe would like to invite you for an interview. Our HR team will contact you shortly with the interview schedule.\n\nBest Regards,\nHR Team'
    );
    
    INSERT OR IGNORE INTO email_settings (id) VALUES (1);
    """)
    conn.commit()
    conn.close()

def migrate_db():
    """Apply schema migrations for existing databases (adds new columns safely)."""
    conn = get_db()
    c = conn.cursor()
    # Add login_count to users if missing
    try:
        c.execute("ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    # Add user_id to candidates if missing
    try:
        c.execute("ALTER TABLE candidates ADD COLUMN user_id INTEGER REFERENCES users(id)")
        conn.commit()
    except Exception:
        pass
    conn.close()

# ─────────────────────────────────────────────
# KEYWORD DATABASE FOR ALL IT ROLES
# ─────────────────────────────────────────────

DEFAULT_ROLES = [
    {
        "title": "Java Full Stack Developer",
        "description": "Develops end-to-end applications using Java backend and modern frontend frameworks.",
        "core_skills": ["Java", "Spring Boot", "Spring MVC", "Hibernate", "JPA", "REST API", "Microservices", "HTML", "CSS", "JavaScript", "React", "Angular"],
        "tools": ["Maven", "Gradle", "Git", "MySQL", "PostgreSQL", "Docker", "Jenkins", "Postman", "IntelliJ IDEA", "Eclipse", "Tomcat", "Redis"],
        "project_keywords": ["spring boot", "microservice", "rest api", "crud", "ecommerce", "banking", "full stack", "java project", "web application"],
        "internship_keywords": ["java", "spring", "backend", "full stack", "software development", "web development"],
        "experience_keywords": ["java developer", "full stack", "spring boot", "backend developer", "software engineer"]
    },
    {
        "title": "Python Full Stack Developer",
        "description": "Builds web applications using Python backend frameworks and modern frontend technologies.",
        "core_skills": ["Python", "Django", "Flask", "FastAPI", "REST API", "HTML", "CSS", "JavaScript", "React", "Bootstrap", "SQLAlchemy"],
        "tools": ["Git", "PostgreSQL", "MySQL", "Redis", "Docker", "Celery", "Nginx", "PyCharm", "VS Code", "Postman", "Heroku"],
        "project_keywords": ["django", "flask", "python web", "rest api", "fastapi", "ecommerce", "blog", "full stack python", "web app"],
        "internship_keywords": ["python", "django", "flask", "web development", "backend", "full stack"],
        "experience_keywords": ["python developer", "django developer", "flask developer", "full stack", "backend python"]
    },
    {
        "title": "MERN Stack Developer",
        "description": "Develops applications using MongoDB, Express.js, React, and Node.js.",
        "core_skills": ["MongoDB", "Express.js", "React", "Node.js", "JavaScript", "HTML", "CSS", "REST API", "JWT", "Redux"],
        "tools": ["Git", "npm", "Postman", "VS Code", "Heroku", "Netlify", "Firebase", "Mongoose", "Axios", "Webpack"],
        "project_keywords": ["mern", "react", "node.js", "mongodb", "express", "full stack javascript", "spa", "web application"],
        "internship_keywords": ["react", "node", "javascript", "mern", "frontend", "backend", "web development"],
        "experience_keywords": ["mern developer", "react developer", "node.js developer", "full stack javascript"]
    },
    {
        "title": "Data Analyst",
        "description": "Analyzes data to derive business insights using statistical and visualization tools.",
        "core_skills": ["Python", "SQL", "Excel", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Power BI", "Tableau", "Statistics", "Data Visualization"],
        "tools": ["MySQL", "PostgreSQL", "Jupyter Notebook", "Google Sheets", "Power BI", "Tableau", "Excel", "VS Code", "Git"],
        "project_keywords": ["data analysis", "dashboard", "visualization", "eda", "exploratory data analysis", "sales analysis", "business intelligence", "sql queries", "reporting"],
        "internship_keywords": ["data analysis", "sql", "python", "excel", "tableau", "power bi", "analytics"],
        "experience_keywords": ["data analyst", "business analyst", "analytics", "reporting analyst", "sql developer"]
    },
    {
        "title": "Data Scientist",
        "description": "Builds predictive models and extracts insights from large datasets using ML/AI techniques.",
        "core_skills": ["Python", "Machine Learning", "Deep Learning", "Statistics", "SQL", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "Keras", "NLP"],
        "tools": ["Jupyter Notebook", "Google Colab", "Git", "Power BI", "Tableau", "AWS", "Azure", "Docker", "Spark", "Hadoop"],
        "project_keywords": ["machine learning", "prediction", "classification", "regression", "neural network", "nlp", "deep learning", "model", "dataset", "kaggle"],
        "internship_keywords": ["data science", "machine learning", "python", "ml", "ai", "deep learning", "analytics"],
        "experience_keywords": ["data scientist", "machine learning engineer", "ml engineer", "ai developer", "research scientist"]
    },
    {
        "title": "AI/ML Engineer",
        "description": "Designs, develops, and deploys machine learning models and AI systems.",
        "core_skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "NLP", "Computer Vision", "MLOps", "REST API"],
        "tools": ["Jupyter", "Docker", "Kubernetes", "AWS SageMaker", "Azure ML", "MLflow", "Kubeflow", "Git", "DVC", "FastAPI"],
        "project_keywords": ["ai", "machine learning", "deep learning", "model deployment", "nlp", "computer vision", "recommendation system", "chatbot", "generative ai"],
        "internship_keywords": ["machine learning", "ai", "deep learning", "python", "tensorflow", "pytorch", "nlp"],
        "experience_keywords": ["ml engineer", "ai engineer", "machine learning engineer", "deep learning engineer", "research engineer"]
    },
    {
        "title": "DevOps Engineer",
        "description": "Automates software delivery pipelines and manages infrastructure for reliable deployments.",
        "core_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "Jenkins", "Git", "Terraform", "Ansible", "Shell Scripting", "Python", "AWS", "Azure"],
        "tools": ["Jenkins", "GitLab CI", "GitHub Actions", "Docker", "Kubernetes", "Terraform", "Ansible", "Prometheus", "Grafana", "ELK Stack"],
        "project_keywords": ["ci/cd", "pipeline", "docker", "kubernetes", "deployment", "infrastructure", "automation", "devops project", "monitoring"],
        "internship_keywords": ["devops", "linux", "docker", "ci/cd", "cloud", "automation", "jenkins"],
        "experience_keywords": ["devops engineer", "site reliability engineer", "sre", "cloud engineer", "infrastructure engineer"]
    },
    {
        "title": "Cloud Engineer",
        "description": "Designs and manages cloud infrastructure solutions on platforms like AWS, Azure, or GCP.",
        "core_skills": ["AWS", "Azure", "GCP", "Cloud Architecture", "Linux", "Networking", "Security", "Docker", "Kubernetes", "Terraform", "Python"],
        "tools": ["AWS EC2", "S3", "Lambda", "RDS", "Azure VM", "GCP", "Terraform", "Ansible", "CloudFormation", "VPC", "IAM"],
        "project_keywords": ["cloud migration", "aws", "azure", "infrastructure", "serverless", "cloud architecture", "lambda", "s3", "azure functions"],
        "internship_keywords": ["cloud", "aws", "azure", "gcp", "linux", "networking", "cloud services"],
        "experience_keywords": ["cloud engineer", "aws architect", "azure engineer", "cloud architect", "infrastructure engineer"]
    },
    {
        "title": "Software Tester",
        "description": "Ensures software quality through manual and automated testing methodologies.",
        "core_skills": ["Manual Testing", "Automation Testing", "Selenium", "TestNG", "JUnit", "JIRA", "SQL", "API Testing", "Postman", "SDLC", "STLC", "Test Cases"],
        "tools": ["Selenium WebDriver", "Postman", "JIRA", "TestNG", "Maven", "Jenkins", "Git", "Appium", "JMeter", "Cucumber", "BDD"],
        "project_keywords": ["test automation", "selenium", "manual testing", "api testing", "performance testing", "test cases", "bug report", "qa project"],
        "internship_keywords": ["testing", "qa", "quality assurance", "selenium", "manual testing", "automation"],
        "experience_keywords": ["software tester", "qa engineer", "test engineer", "automation tester", "quality analyst"]
    },
    {
        "title": "Database Developer",
        "description": "Designs, develops, and optimizes databases for scalability and performance.",
        "core_skills": ["SQL", "MySQL", "PostgreSQL", "Oracle", "MongoDB", "Database Design", "Normalization", "Stored Procedures", "Indexing", "PL/SQL", "Query Optimization"],
        "tools": ["MySQL Workbench", "pgAdmin", "Oracle SQL Developer", "MongoDB Compass", "Redis", "Cassandra", "Git", "DBeaver", "SSMS"],
        "project_keywords": ["database design", "schema", "sql queries", "normalization", "stored procedure", "data warehouse", "etl", "database project"],
        "internship_keywords": ["sql", "database", "mysql", "postgresql", "mongodb", "pl/sql", "data management"],
        "experience_keywords": ["database developer", "dba", "database administrator", "sql developer", "data engineer"]
    }
]

# ─────────────────────────────────────────────
# RESUME PARSING
# ─────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"PDF error: {e}")
    return text

def extract_text_from_docx(filepath):
    text = ""
    try:
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"DOCX error: {e}")
    return text

def extract_text(filepath):
    ext = filepath.rsplit(".", 1)[1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(filepath)
    elif ext == "docx":
        return extract_text_from_docx(filepath)
    return ""

def extract_name(text):
    """Extract candidate name from first few lines."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # Usually name is in the first 1-3 lines
    for line in lines[:5]:
        # Skip lines with email, phone, URLs
        if re.search(r"[@:/.()]|\d{5,}", line):
            continue
        # Skip common header words
        if re.search(r"resume|curriculum|vitae|cv|objective|summary|profile", line, re.IGNORECASE):
            continue
        # Name is usually 2-4 words, all title case or caps
        words = line.split()
        if 1 < len(words) <= 5:
            return line.strip()
    return "Unknown"

def extract_email(text):
    match = re.search(r"[\w.\-+]+@[\w.\-]+\.[a-zA-Z]{2,}", text)
    return match.group() if match else ""

def extract_phone(text):
    match = re.search(r"(\+?\d[\d\s\-().]{8,15}\d)", text)
    return match.group().strip() if match else ""

def find_keywords_in_text(text, keywords):
    """Find which keywords from list appear in text (case-insensitive)."""
    text_lower = text.lower()
    found = []
    for kw in keywords:
        # Match whole word or phrase
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(kw)
    return found

# ─────────────────────────────────────────────
# SCORING ALGORITHM
# ─────────────────────────────────────────────

def calculate_score(candidate_data, role):
    """
    Weighted scoring algorithm:
    - Core Skills:  40%
    - Tools:        25%
    - Projects:     15%
    - Internship:   10%
    - Experience:   10%
    
    Each section score = (keywords_matched / total_keywords) * 100
    Final score = weighted sum of section scores
    """
    weights = {
        "core": role["core_weight"],
        "tools": role["tools_weight"],
        "projects": role["projects_weight"],
        "internship": role["internship_weight"],
        "experience": role["experience_weight"]
    }

    def section_pct(found, total):
        if not total:
            return 0
        return min((len(found) / total) * 100, 100)

    core_score = section_pct(candidate_data["skills_found"], len(json.loads(role["core_skills"])))
    tools_score = section_pct(candidate_data["tools_found"], len(json.loads(role["tools"])))
    proj_score = section_pct(candidate_data["projects_found"], len(json.loads(role["project_keywords"])))
    intern_score = section_pct(candidate_data["internship_found"], len(json.loads(role["internship_keywords"])))
    exp_score = section_pct(candidate_data["experience_found"], len(json.loads(role["experience_keywords"])))

    total = (
        core_score * weights["core"] +
        tools_score * weights["tools"] +
        proj_score * weights["projects"] +
        intern_score * weights["internship"] +
        exp_score * weights["experience"]
    )

    return {
        "core_score": round(core_score, 1),
        "tools_score": round(tools_score, 1),
        "projects_score": round(proj_score, 1),
        "internship_score": round(intern_score, 1),
        "experience_score": round(exp_score, 1),
        "total_score": round(total, 1)
    }

def generate_rejection_reason(scores, threshold):
    """Generate human-readable rejection reason."""
    reasons = []
    if scores["core_score"] < 20:
        reasons.append("insufficient core technical skills")
    if scores["tools_score"] < 20:
        reasons.append("limited relevant tool experience")
    if scores["projects_score"] < 10:
        reasons.append("no relevant project exposure")
    if scores["internship_score"] < 10 and scores["experience_score"] < 10:
        reasons.append("no relevant internship or work experience")
    
    if not reasons:
        reasons.append(f"overall profile score ({scores['total_score']:.1f}%) below minimum threshold ({threshold}%)")
    
    return f"Profile score {scores['total_score']:.1f}% is below threshold {threshold}%. Reasons: {'; '.join(reasons)}."

def detect_internship_experience(text):
    """
    Detect internship/training experience even without exact 'internship' keyword.
    Looks for patterns like: trainee, apprentice, industrial training, project trainee,
    in-plant training, on-the-job training, practical training, summer training,
    worked at/in [company], as well as time-bound roles (e.g., 3 months at X).
    Returns a list of matched evidence strings.
    """
    text_lower = text.lower()
    evidence = []

    # Direct internship synonyms and training indicators
    internship_patterns = [
        r'\binternship\b', r'\bintern\b', r'\btrainee\b', r'\bapprentice\b',
        r'\bindustrial training\b', r'\bin[-\s]?plant training\b',
        r'\bon[-\s]?the[-\s]?job training\b', r'\bpractical training\b',
        r'\bsummer training\b', r'\bproject trainee\b', r'\bgraduate trainee\b',
        r'\bjunior trainee\b', r'\bvocational training\b', r'\bwork experience\b',
        r'\bwork placement\b', r'\bfield training\b', r'\bcorporate training\b',
        r'\btraining period\b', r'\btraining program\b', r'\btraining at\b',
        r'\bundergoing training\b', r'\bcompleted training\b',
    ]

    for pattern in internship_patterns:
        if re.search(pattern, text_lower):
            label = pattern.replace(r'\b', '').replace('[-\\s]?', ' ').replace('\\b', '').strip()
            evidence.append(label)

    # Short-duration work patterns (e.g., "2 months at TCS", "3-month project at Infosys")
    duration_pattern = re.findall(
        r'(\d+[\s-]*(?:month|week)s?\s+(?:at|with|in|for)\s+\w[\w\s]{1,30})',
        text_lower
    )
    for match in duration_pattern:
        evidence.append(match.strip())

    return list(set(evidence))  # deduplicate


def screen_resume(filepath, role):
    """Full pipeline: extract → parse → score → decide."""
    text = extract_text(filepath)
    if not text:
        return None
    
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    
    core_skills = json.loads(role["core_skills"])
    tools = json.loads(role["tools"])
    proj_kw = json.loads(role["project_keywords"])
    intern_kw = json.loads(role["internship_keywords"])
    exp_kw = json.loads(role["experience_keywords"])
    
    skills_found = find_keywords_in_text(text, core_skills)
    tools_found = find_keywords_in_text(text, tools)
    projects_found = find_keywords_in_text(text, proj_kw)

    # Enhanced internship detection: keyword match + semantic pattern detection
    internship_found_kw = find_keywords_in_text(text, intern_kw)
    internship_found_pattern = detect_internship_experience(text)
    # Merge both lists (deduplicated)
    internship_found = list(set(internship_found_kw + internship_found_pattern))

    experience_found = find_keywords_in_text(text, exp_kw)
    
    candidate_data = {
        "skills_found": skills_found,
        "tools_found": tools_found,
        "projects_found": projects_found,
        "internship_found": internship_found,
        "experience_found": experience_found
    }
    
    scores = calculate_score(candidate_data, role)
    threshold = role["min_threshold"]
    
    status = "shortlisted" if scores["total_score"] >= threshold else "rejected"
    rejection_reason = "" if status == "shortlisted" else generate_rejection_reason(scores, threshold)
    
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "raw_text": text[:2000],  # store first 2000 chars
        "skills_found": json.dumps(skills_found),
        "tools_found": json.dumps(tools_found),
        "projects_found": json.dumps(projects_found),
        "internship_found": json.dumps(internship_found),
        "experience_found": json.dumps(experience_found),
        "status": status,
        "rejection_reason": rejection_reason,
        **scores
    }

# ─────────────────────────────────────────────
# EMAIL INTEGRATION
# ─────────────────────────────────────────────

def send_interview_email(settings, candidate_name, candidate_email, job_role_title):
    """Send SMTP email with dynamic name and role substitution."""
    subject = settings["email_subject"].replace("{job_role}", job_role_title).replace("{name}", candidate_name)
    body = settings["email_body"].replace("{name}", candidate_name).replace("{job_role}", job_role_title)
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings["sender_email"]
    msg["To"] = candidate_email
    
    html_body = f"""
    <html><body>
    <div style="font-family:Arial,sans-serif; max-width:600px; margin:0 auto; padding:20px;">
      <div style="background:#2563eb; padding:20px; border-radius:8px 8px 0 0;">
        <h2 style="color:white; margin:0;">Interview Invitation</h2>
      </div>
      <div style="background:#f8fafc; padding:30px; border:1px solid #e2e8f0; border-radius:0 0 8px 8px;">
        {body.replace(chr(10), '<br>')}
      </div>
    </div>
    </body></html>
    """
    
    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    
    try:
        server = smtplib.SMTP(settings["smtp_host"], settings["smtp_port"])
        server.ehlo()
        server.starttls()
        server.login(settings["sender_email"], settings["sender_password"])
        server.sendmail(settings["sender_email"], candidate_email, msg.as_string())
        server.quit()
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

# @app.route("/")
# def index():
#     conn = get_db()
#     roles = conn.execute("SELECT * FROM job_roles ORDER BY created_at DESC").fetchall()
#     total_candidates = conn.execute("SELECT COUNT(*) as c FROM candidates").fetchone()["c"]
#     shortlisted = conn.execute("SELECT COUNT(*) as c FROM candidates WHERE status='shortlisted'").fetchone()["c"]
#     rejected = conn.execute("SELECT COUNT(*) as c FROM candidates WHERE status='rejected'").fetchone()["c"]
#     conn.close()
#     return render_template("index.html", roles=roles,
#                            total=total_candidates, shortlisted=shortlisted, rejected=rejected)

# ── JOB ROLES ──

@app.route("/roles")
def roles():
    conn = get_db()
    roles = conn.execute("SELECT * FROM job_roles ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("roles.html", roles=roles)

@app.route("/roles/new", methods=["GET", "POST"])
def new_role():
    if request.method == "POST":
        def parse_list(field):
            raw = request.form.get(field, "")
            items = [x.strip() for x in raw.split(",") if x.strip()]
            return json.dumps(items)
        
        conn = get_db()
        conn.execute("""
            INSERT INTO job_roles (title, description, core_skills, tools, project_keywords,
                internship_keywords, experience_keywords, core_weight, tools_weight,
                projects_weight, internship_weight, experience_weight, min_threshold)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            request.form["title"],
            request.form.get("description", ""),
            parse_list("core_skills"),
            parse_list("tools"),
            parse_list("project_keywords"),
            parse_list("internship_keywords"),
            parse_list("experience_keywords"),
            float(request.form.get("core_weight", 0.40)),
            float(request.form.get("tools_weight", 0.25)),
            float(request.form.get("projects_weight", 0.15)),
            float(request.form.get("internship_weight", 0.10)),
            float(request.form.get("experience_weight", 0.10)),
            int(request.form.get("min_threshold", 50))
        ))
        conn.commit()
        conn.close()
        flash("Job role created successfully!", "success")
        return redirect(url_for("roles"))
    
    return render_template("new_role.html")

@app.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
def edit_role(role_id):
    conn = get_db()
    role = conn.execute("SELECT * FROM job_roles WHERE id=?", (role_id,)).fetchone()
    
    if request.method == "POST":
        def parse_list(field):
            raw = request.form.get(field, "")
            items = [x.strip() for x in raw.split(",") if x.strip()]
            return json.dumps(items)
        
        conn.execute("""
            UPDATE job_roles SET title=?, description=?, core_skills=?, tools=?,
                project_keywords=?, internship_keywords=?, experience_keywords=?,
                core_weight=?, tools_weight=?, projects_weight=?, internship_weight=?,
                experience_weight=?, min_threshold=?
            WHERE id=?
        """, (
            request.form["title"],
            request.form.get("description", ""),
            parse_list("core_skills"),
            parse_list("tools"),
            parse_list("project_keywords"),
            parse_list("internship_keywords"),
            parse_list("experience_keywords"),
            float(request.form.get("core_weight", 0.40)),
            float(request.form.get("tools_weight", 0.25)),
            float(request.form.get("projects_weight", 0.15)),
            float(request.form.get("internship_weight", 0.10)),
            float(request.form.get("experience_weight", 0.10)),
            int(request.form.get("min_threshold", 50)),
            role_id
        ))
        conn.commit()
        flash("Job role updated!", "success")
        return redirect(url_for("roles"))
    
    conn.close()
    return render_template("edit_role.html", role=role)

@app.route("/roles/<int:role_id>/delete", methods=["POST"])
def delete_role(role_id):
    conn = get_db()
    conn.execute("DELETE FROM job_roles WHERE id=?", (role_id,))
    conn.commit()
    conn.close()
    flash("Role deleted.", "info")
    return redirect(url_for("roles"))

# ── UPLOAD & SCREEN ──

@app.route("/upload", methods=["GET", "POST"])
def upload():
    conn = get_db()
    roles = conn.execute("SELECT id, title FROM job_roles ORDER BY title").fetchall()
    conn.close()
    
    if request.method == "POST":
        role_id = int(request.form.get("role_id", 0))
        files = request.files.getlist("resumes")
        
        if not role_id:
            flash("Please select a job role.", "danger")
            return redirect(url_for("upload"))
        if not files or all(f.filename == "" for f in files):
            flash("Please upload at least one file.", "danger")
            return redirect(url_for("upload"))
        
        conn = get_db()
        role = conn.execute("SELECT * FROM job_roles WHERE id=?", (role_id,)).fetchone()
        
        processed = 0
        errors = 0
        
        for f in files:
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                # Add timestamp to avoid collisions
                ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
                save_name = f"{ts}_{filename}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], save_name)
                f.save(filepath)
                
                result = screen_resume(filepath, role)
                
                if result:
                    conn.execute("""
                        INSERT INTO candidates (user_id, job_role_id, name, email, phone, raw_text,
                            skills_found, tools_found, projects_found, internship_found, experience_found,
                            core_score, tools_score, projects_score, internship_score, experience_score,
                            total_score, status, rejection_reason, filename)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        session.get("user_id"),
                        role_id, result["name"], result["email"], result["phone"], result["raw_text"],
                        result["skills_found"], result["tools_found"], result["projects_found"],
                        result["internship_found"], result["experience_found"],
                        result["core_score"], result["tools_score"], result["projects_score"],
                        result["internship_score"], result["experience_score"],
                        result["total_score"], result["status"], result["rejection_reason"], save_name
                    ))
                    processed += 1
                else:
                    errors += 1
            else:
                errors += 1
        
        conn.commit()
        conn.close()
        flash(f"Processed {processed} resumes. {errors} errors.", "success" if processed else "danger")
        return redirect(url_for("results", role_id=role_id))
    
    return render_template("upload.html", roles=roles)

# ── RESULTS ──

@app.route("/results")
def results():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    role_id = request.args.get("role_id", type=int)
    status_filter = request.args.get("status", "all")
    
    conn = get_db()
    roles = conn.execute("SELECT id, title FROM job_roles ORDER BY title").fetchall()
    
    query = "SELECT c.*, j.title as role_title, j.min_threshold FROM candidates c JOIN job_roles j ON c.job_role_id=j.id"
    params = []
    where = ["c.user_id=?"]
    params.append(user_id)
    if role_id:
        where.append("c.job_role_id=?")
        params.append(role_id)
    if status_filter != "all":
        where.append("c.status=?")
        params.append(status_filter)
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY c.total_score DESC"
    
    candidates = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template("results.html", candidates=candidates, roles=roles,
                           selected_role=role_id, status_filter=status_filter)

@app.route("/candidate/<int:cid>")
def candidate_detail(cid):
    conn = get_db()
    c = conn.execute("""
        SELECT c.*, j.title as role_title, j.min_threshold, j.core_skills, j.tools,
               j.project_keywords, j.internship_keywords, j.experience_keywords
        FROM candidates c JOIN job_roles j ON c.job_role_id=j.id WHERE c.id=?
    """, (cid,)).fetchone()
    conn.close()
    
    if not c:
        flash("Candidate not found.", "danger")
        return redirect(url_for("results"))
    
    # Parse JSON fields for display
    parsed = dict(c)
    for field in ["skills_found", "tools_found", "projects_found", "internship_found", "experience_found",
                  "core_skills", "tools", "project_keywords", "internship_keywords", "experience_keywords"]:
        try:
            parsed[field] = json.loads(c[field] or "[]")
        except:
            parsed[field] = []
    
    return render_template("candidate_detail.html", c=parsed)

@app.route("/candidate/<int:cid>/delete", methods=["POST"])
def delete_candidate(cid):
    conn = get_db()
    conn.execute("DELETE FROM candidates WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    flash("Candidate deleted.", "info")
    return redirect(url_for("results"))

# ── EMAIL ──

@app.route("/send_emails", methods=["POST"])
def send_emails():
    candidate_ids = request.form.getlist("candidate_ids")
    if not candidate_ids:
        flash("No candidates selected.", "danger")
        return redirect(url_for("results"))
    
    conn = get_db()
    settings = conn.execute("SELECT * FROM email_settings WHERE id=1").fetchone()
    
    if not settings or not settings["sender_email"]:
        flash("Email settings not configured. Please configure SMTP settings first.", "danger")
        conn.close()
        return redirect(url_for("email_settings_page"))
    
    sent_count = 0
    fail_count = 0
    
    for cid in candidate_ids:
        c = conn.execute("""
            SELECT c.name, c.email, j.title as role_title
            FROM candidates c JOIN job_roles j ON c.job_role_id=j.id
            WHERE c.id=?
        """, (cid,)).fetchone()
        
        if c and c["email"]:
            success, msg = send_interview_email(dict(settings), c["name"], c["email"], c["role_title"])
            if success:
                conn.execute("UPDATE candidates SET email_sent=1, email_sent_at=? WHERE id=?",
                             (datetime.now(), cid))
                sent_count += 1
            else:
                fail_count += 1
    
    conn.commit()
    conn.close()
    
    if sent_count:
        flash(f"Successfully sent {sent_count} invitation email(s).", "success")
    if fail_count:
        flash(f"Failed to send {fail_count} email(s). Check SMTP settings.", "danger")
    
    return redirect(url_for("results"))

@app.route("/send_email_single/<int:cid>", methods=["POST"])
def send_email_single(cid):
    conn = get_db()
    settings = conn.execute("SELECT * FROM email_settings WHERE id=1").fetchone()
    c = conn.execute("""
        SELECT c.name, c.email, j.title as role_title
        FROM candidates c JOIN job_roles j ON c.job_role_id=j.id WHERE c.id=?
    """, (cid,)).fetchone()
    
    if not settings or not settings["sender_email"]:
        flash("Email settings not configured.", "danger")
    elif not c or not c["email"]:
        flash("Candidate email not found.", "danger")
    else:
        success, msg = send_interview_email(dict(settings), c["name"], c["email"], c["role_title"])
        if success:
            conn.execute("UPDATE candidates SET email_sent=1, email_sent_at=? WHERE id=?",
                         (datetime.now(), cid))
            conn.commit()
            flash("Interview invitation sent!", "success")
        else:
            flash(f"Email failed: {msg}", "danger")
    
    conn.close()
    return redirect(url_for("candidate_detail", cid=cid))

@app.route("/email-settings", methods=["GET", "POST"])
def email_settings_page():
    conn = get_db()
    settings = conn.execute("SELECT * FROM email_settings WHERE id=1").fetchone()
    
    if request.method == "POST":
        conn.execute("""
            UPDATE email_settings SET smtp_host=?, smtp_port=?, sender_email=?,
                sender_password=?, email_subject=?, email_body=? WHERE id=1
        """, (
            request.form["smtp_host"],
            int(request.form["smtp_port"]),
            request.form["sender_email"],
            request.form["sender_password"],
            request.form["email_subject"],
            request.form["email_body"]
        ))
        conn.commit()
        flash("Email settings saved!", "success")
        return redirect(url_for("email_settings_page"))
    
    conn.close()
    return render_template("email_settings.html", settings=settings)

# ── SEED DEFAULT ROLES ──

@app.route("/seed-roles")
def seed_roles():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) as c FROM job_roles").fetchone()["c"]
    if existing == 0:
        for role in DEFAULT_ROLES:
            conn.execute("""
                INSERT INTO job_roles (title, description, core_skills, tools, project_keywords,
                    internship_keywords, experience_keywords)
                VALUES (?,?,?,?,?,?,?)
            """, (
                role["title"], role["description"],
                json.dumps(role["core_skills"]),
                json.dumps(role["tools"]),
                json.dumps(role["project_keywords"]),
                json.dumps(role["internship_keywords"]),
                json.dumps(role["experience_keywords"])
            ))
        conn.commit()
        flash(f"Seeded {len(DEFAULT_ROLES)} default IT job roles!", "success")
    else:
        flash("Job roles already exist.", "info")
    conn.close()
    return redirect(url_for("roles"))

# ── API ENDPOINTS ──

@app.route("/api/dashboard")
def api_dashboard():
    if "user_id" not in session:
        return jsonify([])
    user_id = session["user_id"]
    conn = get_db()
    roles = conn.execute("""
        SELECT j.title, COUNT(c.id) as total,
               SUM(CASE WHEN c.status='shortlisted' THEN 1 ELSE 0 END) as shortlisted,
               SUM(CASE WHEN c.status='rejected' THEN 1 ELSE 0 END) as rejected
        FROM job_roles j LEFT JOIN candidates c ON j.id=c.job_role_id AND c.user_id=?
        GROUP BY j.id
    """, (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in roles])

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?,?,?)",
                (name, email, password)
            )
            conn.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("login"))
        except:
            flash("Email already exists!", "danger")
        finally:
            conn.close()

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            login_count = user["login_count"] if user["login_count"] else 0
            is_new_user = (login_count == 0)
            # Increment login count
            conn.execute("UPDATE users SET login_count = login_count + 1 WHERE id=?", (user["id"],))
            conn.commit()
            conn.close()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["is_new_user"] = is_new_user
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            conn.close()
            flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()
    roles = conn.execute("SELECT * FROM job_roles ORDER BY created_at DESC").fetchall()
    total_candidates = conn.execute("SELECT COUNT(*) as c FROM candidates WHERE user_id=?", (user_id,)).fetchone()["c"]
    shortlisted = conn.execute("SELECT COUNT(*) as c FROM candidates WHERE status='shortlisted' AND user_id=?", (user_id,)).fetchone()["c"]
    rejected = conn.execute("SELECT COUNT(*) as c FROM candidates WHERE status='rejected' AND user_id=?", (user_id,)).fetchone()["c"]
    conn.close()

    is_new_user = session.pop("is_new_user", False)

    return render_template(
        "index.html",
        roles=roles,
        total=total_candidates,
        shortlisted=shortlisted,
        rejected=rejected,
        user_name=session["user_name"],
        is_new_user=is_new_user
    )
# ─────────────────────────────────────────────
# CUSTOM JINJA2 FILTERS
# ─────────────────────────────────────────────

@app.template_filter("fromjson")
def fromjson_filter(value):
    try:
        return json.loads(value)
    except:
        return []

if __name__ == "__main__":
    init_db()
    migrate_db()
    app.run(debug=True, port=5000)

