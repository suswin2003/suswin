const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, PageBreak, VerticalAlign
} = require('docx');
const fs = require('fs');

const PRIMARY = "2563EB";
const DARK = "1E3A8A";
const LIGHT_BG = "EFF6FF";
const SUCCESS = "16A34A";
const DANGER = "DC2626";
const WARNING = "D97706";
const GRAY = "64748B";
const TABLE_HEADER = "1E3A8A";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CBD5E1" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorders = {
  top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }
};

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, size: 36, color: DARK, font: "Arial" })],
    spacing: { before: 400, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: PRIMARY, space: 1 } }
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, size: 28, color: PRIMARY, font: "Arial" })],
    spacing: { before: 300, after: 120 }
  });
}

function h3(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: 24, color: DARK, font: "Arial" })],
    spacing: { before: 200, after: 80 }
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, size: 22, font: "Arial", color: "374151", ...opts })],
    spacing: { after: 120 }
  });
}

function bullet(text, sub = false) {
  return new Paragraph({
    numbering: { reference: sub ? "sub-bullets" : "bullets", level: 0 },
    children: [new TextRun({ text, size: 21, font: "Arial", color: "374151" })],
    spacing: { after: 60 }
  });
}

function codeBlock(text) {
  return new Paragraph({
    children: [new TextRun({ text, size: 19, font: "Courier New", color: "1E40AF" })],
    shading: { fill: "F0F9FF", type: ShadingType.CLEAR },
    spacing: { before: 60, after: 60 },
    indent: { left: 360 },
    border: { left: { style: BorderStyle.SINGLE, size: 6, color: PRIMARY, space: 8 } }
  });
}

function tRow(cells, isHeader = false) {
  return new TableRow({
    tableHeader: isHeader,
    children: cells.map((c, i) =>
      new TableCell({
        borders,
        shading: { fill: isHeader ? TABLE_HEADER : (i % 2 === 0 ? "F8FAFC" : "FFFFFF"), type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({
          children: [new TextRun({
            text: c,
            size: isHeader ? 20 : 19,
            bold: isHeader,
            color: isHeader ? "FFFFFF" : "374151",
            font: "Arial"
          })]
        })]
      })
    )
  });
}

function infoBox(title, body, color = LIGHT_BG) {
  return new Paragraph({
    children: [
      new TextRun({ text: `${title}  `, bold: true, size: 21, font: "Arial", color: PRIMARY }),
      new TextRun({ text: body, size: 21, font: "Arial", color: "374151" })
    ],
    shading: { fill: color, type: ShadingType.CLEAR },
    spacing: { before: 80, after: 80 },
    indent: { left: 360, right: 360 },
    border: { left: { style: BorderStyle.SINGLE, size: 8, color: PRIMARY, space: 8 } }
  });
}

function spacer() {
  return new Paragraph({ children: [new TextRun("")], spacing: { after: 100 } });
}

// ─── BUILD DOCUMENT ───────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "sub-bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "○", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1080, hanging: 360 } } }
        }]
      },
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      }
    ]
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: DARK },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: PRIMARY },
        paragraph: { spacing: { before: 300, after: 120 }, outlineLevel: 1 }
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1080, bottom: 1440, left: 1080 }
      }
    },
    children: [
      // ═══ TITLE PAGE ═══
      spacer(), spacer(), spacer(),
      new Paragraph({
        children: [new TextRun({ text: "🤖", size: 96 })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "INTELLIGENT RESUME SCREENING", bold: true, size: 48, color: DARK, font: "Arial" })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "AND AUTOMATED INTERVIEW NOTIFICATION SYSTEM", bold: true, size: 36, color: PRIMARY, font: "Arial" })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 400 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "MCA Final Year Project — Complete Documentation", size: 24, color: GRAY, font: "Arial" })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "Decision Support System for IT Recruitment", size: 22, color: GRAY, font: "Arial" })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 800 }
      }),
      spacer(), spacer(), spacer(),

      // ═══ 1. SYSTEM ARCHITECTURE ═══
      new Paragraph({ children: [new PageBreak()] }),
      h1("1. System Architecture"),
      para("The system follows a three-tier architecture pattern separating Presentation, Application, and Data layers. It is designed as a Decision Support System — augmenting HR judgment rather than replacing it."),
      spacer(),
      
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2000, 3680, 3680],
        rows: [
          tRow(["Layer", "Components", "Responsibilities"], true),
          tRow(["Presentation (Frontend)", "HTML5, Bootstrap 5, JavaScript, Jinja2 Templates", "User Interface — job role management, resume upload, results dashboard, email actions"]),
          tRow(["Application (Backend)", "Python, Flask Framework, Custom Screening Engine", "Business logic, resume parsing, scoring algorithm, email integration"]),
          tRow(["Data (Storage)", "SQLite Database (upgradeable to PostgreSQL/MySQL)", "Persistent storage of job roles, candidates, scores, email settings"]),
          tRow(["File Processing", "pdfplumber (PDF), python-docx (DOCX)", "Text extraction from uploaded resume files"]),
          tRow(["Email Service", "smtplib + MIME (STARTTLS/TLS)", "Secure SMTP email dispatch with dynamic templates"])
        ]
      }),
      spacer(),

      h2("1.1 Data Flow Diagram"),
      new Paragraph({
        children: [new TextRun({ text: "HR → Upload Resumes (PDF/DOCX) → Text Extraction → Named Entity Recognition → Keyword Matching → Weighted Scoring → Threshold Decision → Shortlist/Reject → Email Notification", size: 20, font: "Courier New", color: "1E40AF" })],
        shading: { fill: "F0F9FF", type: ShadingType.CLEAR },
        spacing: { before: 80, after: 80 },
        indent: { left: 360, right: 360 }
      }),
      spacer(),

      h2("1.2 Technology Stack"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 3480, 3480],
        rows: [
          tRow(["Category", "Technology", "Purpose"], true),
          tRow(["Web Framework", "Flask 3.x (Python)", "Lightweight, easy to extend, ideal for MCA project"]),
          tRow(["Database", "SQLite (dev) / PostgreSQL (prod)", "Relational storage for roles, candidates, scores"]),
          tRow(["PDF Parsing", "pdfplumber", "Accurate text extraction including tables"]),
          tRow(["DOCX Parsing", "python-docx", "Extract paragraphs and tables from Word files"]),
          tRow(["Frontend", "Bootstrap 5 + Font Awesome", "Responsive UI, icons"]),
          tRow(["Email", "smtplib + MIMEMultipart", "Secure SMTP with HTML/plain text emails"]),
          tRow(["Templating", "Jinja2", "Dynamic HTML generation"]),
          tRow(["Hosting", "localhost / Render / Railway / Heroku", "Deployment options"])
        ]
      }),

      // ═══ 2. DATABASE SCHEMA ═══
      new Paragraph({ children: [new PageBreak()] }),
      h1("2. Database Schema"),
      
      h2("2.1 Table: job_roles"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2000, 1800, 1560, 4000],
        rows: [
          tRow(["Column", "Type", "Constraint", "Description"], true),
          tRow(["id", "INTEGER", "PK, AI", "Auto-increment primary key"]),
          tRow(["title", "TEXT", "NOT NULL", "Job role name (e.g., Java Full Stack Developer)"]),
          tRow(["description", "TEXT", "", "Brief role description"]),
          tRow(["core_skills", "TEXT (JSON)", "NOT NULL", "JSON array of core skill keywords"]),
          tRow(["tools", "TEXT (JSON)", "NOT NULL", "JSON array of tool/technology keywords"]),
          tRow(["project_keywords", "TEXT (JSON)", "NOT NULL", "Keywords for project section matching"]),
          tRow(["internship_keywords", "TEXT (JSON)", "NOT NULL", "Keywords for internship section matching"]),
          tRow(["experience_keywords", "TEXT (JSON)", "NOT NULL", "Keywords for experience section matching"]),
          tRow(["core_weight", "REAL", "DEFAULT 0.40", "Weight for core skills (0.0–1.0)"]),
          tRow(["tools_weight", "REAL", "DEFAULT 0.25", "Weight for tools section"]),
          tRow(["projects_weight", "REAL", "DEFAULT 0.15", "Weight for projects section"]),
          tRow(["internship_weight", "REAL", "DEFAULT 0.10", "Weight for internship section"]),
          tRow(["experience_weight", "REAL", "DEFAULT 0.10", "Weight for experience section"]),
          tRow(["min_threshold", "INTEGER", "DEFAULT 50", "Minimum score (%) to shortlist candidate"]),
          tRow(["created_at", "TIMESTAMP", "DEFAULT NOW", "Role creation timestamp"])
        ]
      }),
      spacer(),

      h2("2.2 Table: candidates"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2200, 1600, 1560, 4000],
        rows: [
          tRow(["Column", "Type", "Constraint", "Description"], true),
          tRow(["id", "INTEGER", "PK, AI", "Auto-increment primary key"]),
          tRow(["job_role_id", "INTEGER", "FK → job_roles", "Which role this candidate applied for"]),
          tRow(["name", "TEXT", "", "Extracted candidate name"]),
          tRow(["email", "TEXT", "", "Extracted email address"]),
          tRow(["phone", "TEXT", "", "Extracted phone number"]),
          tRow(["raw_text", "TEXT", "", "First 2000 chars of extracted resume text"]),
          tRow(["skills_found", "TEXT (JSON)", "", "Core skills matched in resume"]),
          tRow(["tools_found", "TEXT (JSON)", "", "Tools matched in resume"]),
          tRow(["projects_found", "TEXT (JSON)", "", "Project keywords matched"]),
          tRow(["internship_found", "TEXT (JSON)", "", "Internship keywords matched"]),
          tRow(["experience_found", "TEXT (JSON)", "", "Experience keywords matched"]),
          tRow(["core_score", "REAL", "DEFAULT 0", "Core skills section score (0–100)"]),
          tRow(["tools_score", "REAL", "DEFAULT 0", "Tools section score (0–100)"]),
          tRow(["projects_score", "REAL", "DEFAULT 0", "Projects section score (0–100)"]),
          tRow(["internship_score", "REAL", "DEFAULT 0", "Internship section score (0–100)"]),
          tRow(["experience_score", "REAL", "DEFAULT 0", "Experience section score (0–100)"]),
          tRow(["total_score", "REAL", "DEFAULT 0", "Weighted final score (0–100)"]),
          tRow(["status", "TEXT", "DEFAULT pending", "pending / shortlisted / rejected"]),
          tRow(["rejection_reason", "TEXT", "", "Human-readable rejection explanation"]),
          tRow(["email_sent", "INTEGER", "DEFAULT 0", "1 if interview email was sent"]),
          tRow(["email_sent_at", "TIMESTAMP", "", "Timestamp when email was sent"]),
          tRow(["filename", "TEXT", "", "Saved filename on server"]),
          tRow(["uploaded_at", "TIMESTAMP", "DEFAULT NOW", "Upload timestamp"])
        ]
      }),
      spacer(),

      h2("2.3 Table: email_settings"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 1560, 5400],
        rows: [
          tRow(["Column", "Type", "Description"], true),
          tRow(["id", "INTEGER PK", "Always ID=1 (single config row)"]),
          tRow(["smtp_host", "TEXT", "SMTP server hostname (e.g., smtp.gmail.com)"]),
          tRow(["smtp_port", "INTEGER", "SMTP port (587 for TLS, 465 for SSL)"]),
          tRow(["sender_email", "TEXT", "HR sender email address"]),
          tRow(["sender_password", "TEXT", "App password (Gmail) or SMTP password"]),
          tRow(["email_subject", "TEXT", "Subject template with {job_role} placeholder"]),
          tRow(["email_body", "TEXT", "Body template with {name} and {job_role} placeholders"])
        ]
      }),

      // ═══ 3. ALGORITHM ═══
      new Paragraph({ children: [new PageBreak()] }),
      h1("3. Algorithm Logic (Step-by-Step)"),
      
      h2("3.1 Resume Screening Pipeline"),
      
      h3("Step 1: File Upload & Validation"),
      bullet("HR selects a target job role from the dropdown"),
      bullet("Uploads one or more PDF/DOCX files (bulk supported)"),
      bullet("System validates file extensions (only .pdf and .docx allowed)"),
      bullet("Files saved with timestamp-prefixed names to prevent collisions"),
      spacer(),

      h3("Step 2: Text Extraction"),
      bullet("PDF files: pdfplumber extracts text page-by-page"),
      bullet("DOCX files: python-docx iterates over all paragraphs"),
      bullet("Text is concatenated into a single string for processing"),
      bullet("Empty or unreadable files are flagged as errors"),
      spacer(),

      h3("Step 3: Named Entity Extraction"),
      bullet("Name: First 5 lines are scanned; lines without email/phone/URLs and containing 2–5 title-case words are treated as the candidate name"),
      bullet("Email: Regex pattern extracts email — [\\w.+]+@[\\w.]+\\.[a-zA-Z]{2,}"),
      bullet("Phone: Regex extracts phone numbers of 8–15 digits with optional +, spaces, dashes"),
      spacer(),

      h3("Step 4: Keyword Matching"),
      codeBlock("For each keyword in [core_skills, tools, project_keywords, internship_keywords, experience_keywords]:"),
      codeBlock("    pattern = '\\b' + re.escape(keyword.lower()) + '\\b'"),
      codeBlock("    if re.search(pattern, resume_text.lower()):"),
      codeBlock("        add keyword to found_list"),
      bullet("Whole-word boundary matching prevents partial matches (e.g., 'Java' won't match 'JavaScript')"),
      bullet("Case-insensitive matching for robustness"),
      spacer(),

      h3("Step 5: Weighted Scoring"),
      infoBox("Formula:", "section_score = (keywords_matched / total_keywords) × 100"),
      spacer(),
      infoBox("Total Score:", "(core_score × 0.40) + (tools_score × 0.25) + (projects_score × 0.15) + (internship_score × 0.10) + (experience_score × 0.10)"),
      spacer(),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2800, 1600, 1600, 3360],
        rows: [
          tRow(["Section", "Default Weight", "Max Score", "Rationale"], true),
          tRow(["Core Skills", "40%", "40 pts", "Primary technical competency — highest impact"]),
          tRow(["Tools & Technologies", "25%", "25 pts", "Practical tool familiarity"]),
          tRow(["Projects", "15%", "15 pts", "Applied knowledge demonstration"]),
          tRow(["Internship", "10%", "10 pts", "Industry exposure (supports fresh graduates)"]),
          tRow(["Experience", "10%", "10 pts", "Professional work history"])
        ]
      }),
      spacer(),

      h3("Step 6: Decision — Shortlist or Reject"),
      bullet("If total_score ≥ min_threshold → Status = 'shortlisted'"),
      bullet("If total_score < min_threshold → Status = 'rejected'"),
      bullet("Rejection reason is auto-generated identifying weak sections"),
      bullet("Default threshold: 50% (HR-configurable per role)"),
      spacer(),

      h3("Step 7: Email Notification"),
      bullet("HR reviews results on the dashboard"),
      bullet("One-click 'Send Interview Invitation' for individual or bulk candidates"),
      bullet("System replaces {name} and {job_role} in the template"),
      bullet("SMTP sends HTML + plain-text multipart email securely over STARTTLS"),
      bullet("Email status and timestamp recorded in database"),

      // ═══ 4. KEYWORD STRUCTURE ═══
      new Paragraph({ children: [new PageBreak()] }),
      h1("4. Sample Keyword Structure — All Major IT Roles"),

      ...["Java Full Stack Developer", "Python Full Stack Developer", "MERN Stack Developer",
          "Data Analyst", "Data Scientist", "AI/ML Engineer",
          "DevOps Engineer", "Cloud Engineer", "Software Tester", "Database Developer"].map((role, i) => {
        const configs = {
          "Java Full Stack Developer": {
            core: "Java, Spring Boot, Spring MVC, Hibernate, JPA, REST API, Microservices, HTML, CSS, JavaScript, React, Angular",
            tools: "Maven, Gradle, Git, MySQL, PostgreSQL, Docker, Jenkins, Postman, Tomcat, Redis",
            proj: "spring boot, microservice, rest api, crud, ecommerce, banking, full stack, web application",
            intern: "java, spring, backend, full stack, software development, web development",
            exp: "java developer, full stack, spring boot, backend developer, software engineer"
          },
          "Python Full Stack Developer": {
            core: "Python, Django, Flask, FastAPI, REST API, HTML, CSS, JavaScript, React, Bootstrap, SQLAlchemy",
            tools: "Git, PostgreSQL, MySQL, Redis, Docker, Celery, Nginx, PyCharm, VS Code, Postman",
            proj: "django, flask, python web, rest api, fastapi, ecommerce, blog, full stack python",
            intern: "python, django, flask, web development, backend, full stack",
            exp: "python developer, django developer, flask developer, full stack, backend python"
          },
          "MERN Stack Developer": {
            core: "MongoDB, Express.js, React, Node.js, JavaScript, HTML, CSS, REST API, JWT, Redux",
            tools: "Git, npm, Postman, VS Code, Heroku, Netlify, Firebase, Mongoose, Axios, Webpack",
            proj: "mern, react, node.js, mongodb, express, full stack javascript, spa, web application",
            intern: "react, node, javascript, mern, frontend, backend, web development",
            exp: "mern developer, react developer, node.js developer, full stack javascript"
          },
          "Data Analyst": {
            core: "Python, SQL, Excel, Pandas, NumPy, Matplotlib, Seaborn, Power BI, Tableau, Statistics",
            tools: "MySQL, PostgreSQL, Jupyter Notebook, Google Sheets, Power BI, Tableau, Excel, Git",
            proj: "data analysis, dashboard, visualization, eda, sales analysis, business intelligence, reporting",
            intern: "data analysis, sql, python, excel, tableau, power bi, analytics",
            exp: "data analyst, business analyst, analytics, reporting analyst, sql developer"
          },
          "Data Scientist": {
            core: "Python, Machine Learning, Deep Learning, Statistics, SQL, Pandas, Scikit-learn, TensorFlow, Keras, NLP",
            tools: "Jupyter Notebook, Google Colab, Git, Power BI, AWS, Azure, Docker, Spark, Hadoop",
            proj: "machine learning, prediction, classification, regression, neural network, nlp, kaggle, model",
            intern: "data science, machine learning, python, ml, ai, deep learning, analytics",
            exp: "data scientist, machine learning engineer, ml engineer, ai developer, research scientist"
          },
          "AI/ML Engineer": {
            core: "Python, Machine Learning, Deep Learning, TensorFlow, PyTorch, Scikit-learn, NLP, Computer Vision, MLOps",
            tools: "Jupyter, Docker, Kubernetes, AWS SageMaker, Azure ML, MLflow, Kubeflow, Git, DVC, FastAPI",
            proj: "ai, machine learning, deep learning, model deployment, nlp, computer vision, chatbot, generative ai",
            intern: "machine learning, ai, deep learning, python, tensorflow, pytorch, nlp",
            exp: "ml engineer, ai engineer, machine learning engineer, deep learning engineer, research engineer"
          },
          "DevOps Engineer": {
            core: "Linux, Docker, Kubernetes, CI/CD, Jenkins, Git, Terraform, Ansible, Shell Scripting, Python, AWS",
            tools: "Jenkins, GitLab CI, GitHub Actions, Docker, Kubernetes, Terraform, Ansible, Prometheus, Grafana, ELK Stack",
            proj: "ci/cd, pipeline, docker, kubernetes, deployment, infrastructure, automation, monitoring",
            intern: "devops, linux, docker, ci/cd, cloud, automation, jenkins",
            exp: "devops engineer, site reliability engineer, sre, cloud engineer, infrastructure engineer"
          },
          "Cloud Engineer": {
            core: "AWS, Azure, GCP, Cloud Architecture, Linux, Networking, Security, Docker, Kubernetes, Terraform, Python",
            tools: "AWS EC2, S3, Lambda, RDS, Azure VM, GCP, Terraform, Ansible, CloudFormation, VPC, IAM",
            proj: "cloud migration, aws, azure, infrastructure, serverless, cloud architecture, lambda, s3, azure functions",
            intern: "cloud, aws, azure, gcp, linux, networking, cloud services",
            exp: "cloud engineer, aws architect, azure engineer, cloud architect, infrastructure engineer"
          },
          "Software Tester": {
            core: "Manual Testing, Automation Testing, Selenium, TestNG, JUnit, JIRA, SQL, API Testing, Postman, SDLC, STLC",
            tools: "Selenium WebDriver, Postman, JIRA, TestNG, Maven, Jenkins, Git, Appium, JMeter, Cucumber, BDD",
            proj: "test automation, selenium, manual testing, api testing, performance testing, test cases, bug report, qa project",
            intern: "testing, qa, quality assurance, selenium, manual testing, automation",
            exp: "software tester, qa engineer, test engineer, automation tester, quality analyst"
          },
          "Database Developer": {
            core: "SQL, MySQL, PostgreSQL, Oracle, MongoDB, Database Design, Normalization, Stored Procedures, Indexing, PL/SQL",
            tools: "MySQL Workbench, pgAdmin, Oracle SQL Developer, MongoDB Compass, Redis, Cassandra, Git, DBeaver, SSMS",
            proj: "database design, schema, sql queries, normalization, stored procedure, data warehouse, etl, database project",
            intern: "sql, database, mysql, postgresql, mongodb, pl/sql, data management",
            exp: "database developer, dba, database administrator, sql developer, data engineer"
          }
        };
        const cfg = configs[role];
        return [
          h3(`${i + 1}. ${role}`),
          new Table({
            width: { size: 9360, type: WidthType.DXA },
            columnWidths: [2400, 6960],
            rows: [
              tRow(["Category", "Keywords"], true),
              tRow(["Core Skills (40%)", cfg.core]),
              tRow(["Tools (25%)", cfg.tools]),
              tRow(["Project Keywords (15%)", cfg.proj]),
              tRow(["Internship Keywords (10%)", cfg.intern]),
              tRow(["Experience Keywords (10%)", cfg.exp])
            ]
          }),
          spacer()
        ];
      }).flat(),

      // ═══ 5. EMAIL INTEGRATION ═══
      new Paragraph({ children: [new PageBreak()] }),
      h1("5. Email Sending Integration Logic"),
      
      h2("5.1 SMTP Configuration"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 2400, 4560],
        rows: [
          tRow(["Provider", "SMTP Host", "Port / Notes"], true),
          tRow(["Gmail", "smtp.gmail.com", "587 (STARTTLS) — Use App Password, not main password"]),
          tRow(["Outlook/Office365", "smtp.office365.com", "587 (STARTTLS)"]),
          tRow(["Yahoo Mail", "smtp.mail.yahoo.com", "587 (STARTTLS)"]),
          tRow(["SendGrid", "smtp.sendgrid.net", "587 — For production high-volume sending"])
        ]
      }),
      spacer(),
      
      h2("5.2 Email Flow Algorithm"),
      bullet("Step 1: HR clicks 'Send Interview Invitation' (single or bulk)"),
      bullet("Step 2: System loads SMTP credentials from email_settings table"),
      bullet("Step 3: For each candidate, substitute {name} and {job_role} in template"),
      bullet("Step 4: Create MIMEMultipart('alternative') message with plain text + HTML"),
      bullet("Step 5: Connect to SMTP server: server = smtplib.SMTP(host, port)"),
      bullet("Step 6: Upgrade connection: server.ehlo() → server.starttls()"),
      bullet("Step 7: Authenticate: server.login(email, password)"),
      bullet("Step 8: Send: server.sendmail(sender, recipient, msg.as_string())"),
      bullet("Step 9: Update database: email_sent = 1, email_sent_at = NOW"),
      bullet("Step 10: Display success/failure flash message to HR"),
      spacer(),

      h2("5.3 Email Template Placeholders"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 3480, 3480],
        rows: [
          tRow(["Placeholder", "Replaced With", "Example"], true),
          tRow(["{name}", "Candidate's extracted name", "Rahul Sharma"]),
          tRow(["{job_role}", "Applied job role title", "Java Full Stack Developer"])
        ]
      }),

      // ═══ 6. FUTURE ENHANCEMENTS ═══
      new Paragraph({ children: [new PageBreak()] }),
      h1("6. Future Enhancements"),
      
      h2("Phase 2 — AI/NLP Integration"),
      bullet("spaCy NER for accurate name, organization, designation extraction"),
      bullet("Sentence-BERT embeddings for semantic similarity scoring (beyond keyword matching)"),
      bullet("Resume section detection using ML classifiers"),
      bullet("ChatGPT/Gemini API integration for candidate profile summarization"),
      spacer(),

      h2("Phase 3 — Advanced Features"),
      bullet("Candidate portal for self-submission of resumes"),
      bullet("Interview scheduling calendar with Google Calendar integration"),
      bullet("Multi-round screening with ATS (Applicant Tracking System) features"),
      bullet("Analytics dashboard with D3.js charts for hiring funnel visualization"),
      bullet("Duplicate detection using cosine similarity on resume vectors"),
      spacer(),

      h2("Phase 4 — Enterprise Features"),
      bullet("Multi-tenant architecture for multiple companies"),
      bullet("REST API backend with React/Next.js frontend (SPA)"),
      bullet("Role-based access control (HR, Manager, Admin)"),
      bullet("Export results to Excel/PDF reports"),
      bullet("SMS notifications using Twilio API"),
      bullet("PostgreSQL migration with SQLAlchemy ORM and Alembic migrations"),
      bullet("Docker containerization + Kubernetes deployment"),
      bullet("CI/CD pipeline with GitHub Actions"),

      // ═══ 7. VIVA QUESTIONS ═══
      new Paragraph({ children: [new PageBreak()] }),
      h1("7. Viva Questions & Answers"),
      
      ...[
        ["Q1. What is the core problem your system solves?",
         "The system addresses the challenge of manual resume screening in IT recruitment. When HR receives hundreds of resumes for roles like Java Developer or Data Scientist, manually reading each one is time-consuming and error-prone. Our system automates text extraction, keyword matching, and scoring — reducing screening time by up to 80% while maintaining objective, consistent evaluation criteria."],
        
        ["Q2. Explain the scoring algorithm in detail.",
         "The algorithm uses a 5-category weighted scoring model. Core Skills carry 40% weight (primary technical competency). Tools carry 25% weight (practical tool experience). Projects carry 15% (applied knowledge). Internship and Experience each carry 10% (industry exposure). Within each category, score = (keywords_matched / total_keywords) × 100. The final score is a weighted sum: (core×0.40) + (tools×0.25) + (projects×0.15) + (internship×0.10) + (experience×0.10). A candidate crossing the minimum threshold (default 50%) is shortlisted."],
        
        ["Q3. Why did you choose keyword-based matching instead of AI/ML?",
         "Keyword matching is transparent, explainable, and doesn't require a training dataset. For a Decision Support System, HR must understand and trust the screening logic. AI models (black-box) can produce biased or unexplainable decisions. Keyword matching is also lightweight, runs without GPU, and works offline. It aligns with Indian IT recruitment practices where specific tool/framework names are standard requirements. Future phases can layer semantic NLP on top."],
        
        ["Q4. What are the limitations of your system?",
         "Key limitations include: (1) Keyword matching cannot understand context — 'experience with Java' and 'Java is hard' would both match 'Java'. (2) Resume formatting affects text extraction quality. (3) The system cannot evaluate soft skills, communication, or cultural fit. (4) Candidates who use synonyms or abbreviations (e.g., 'ReactJS' vs 'React.js') may not match. (5) Extracted name may be incorrect if the resume has an unusual format. These are addressed in future phases using NLP and semantic similarity."],
        
        ["Q5. How do you ensure data privacy and security?",
         "Uploaded resumes are stored locally on the server. SMTP passwords are stored in the database and should be encrypted in production (e.g., using Fernet encryption). The system uses STARTTLS for secure email transmission. In production deployment, HTTPS (SSL/TLS) should be enforced. Uploaded files are given timestamp-prefixed names to prevent directory traversal attacks. Flask's werkzeug.utils.secure_filename sanitizes file names."],
        
        ["Q6. What is the role of Flask in this project?",
         "Flask is the Python web framework providing: routing (mapping URLs to functions), request handling (GET/POST), session management, template rendering via Jinja2, flash messaging, file upload handling, and a development server. Flask was chosen for its simplicity, minimal boilerplate, and suitability for projects that don't require the full weight of Django. Its lightweight nature makes it ideal for MCA final year projects."],
        
        ["Q7. How does SMTP email sending work?",
         "The system uses Python's smtplib module. Steps: (1) Create SMTP connection to the server (e.g., smtp.gmail.com:587). (2) Send EHLO to identify ourselves. (3) Upgrade to encrypted connection using STARTTLS. (4) Login with credentials. (5) Create a MIMEMultipart message with both plain text and HTML versions. (6) Replace {name} and {job_role} placeholders dynamically. (7) Send using sendmail(). (8) Close connection. Gmail requires App Passwords (not the main account password) when 2FA is enabled."],
        
        ["Q8. Why is this a 'Decision Support System' and not a fully automated system?",
         "A Decision Support System augments human decision-making rather than replacing it. Our system: (1) provides objective, consistent scoring, (2) highlights which keywords were found/missing, (3) gives rejection reasons, (4) still requires HR to review results and initiate emails. HR can override decisions. This design is intentional — hiring involves human judgment about culture fit, communication, and potential that algorithms cannot assess. Fully automated systems can also perpetuate biases."],
        
        ["Q9. Explain the database design choices.",
         "We use SQLite (zero-configuration, serverless) for development, easily upgradeable to PostgreSQL for production. Three tables: job_roles (stores keyword arrays as JSON, supports flexible keyword lists without schema changes), candidates (stores all extracted data and per-section scores), email_settings (single-row config table). JSON storage for keyword arrays provides flexibility to add/remove keywords without schema migrations. The schema uses proper foreign keys for referential integrity."],
        
        ["Q10. What technologies would you use to scale this to production?",
         "For production scaling: (1) Replace SQLite with PostgreSQL. (2) Use Flask with Gunicorn WSGI server + Nginx reverse proxy. (3) Add Redis for caching frequently accessed job roles. (4) Use Celery for async email sending (avoid blocking the web server). (5) Store resumes in AWS S3 or similar object storage instead of local filesystem. (6) Add proper logging with the Python logging module. (7) Use SendGrid or Amazon SES for reliable high-volume email. (8) Deploy on Docker + Kubernetes. (9) Add monitoring with Prometheus + Grafana."],
        
        ["Q11. How do you handle duplicate resumes?",
         "Currently the system does not detect duplicates — every uploaded file creates a new candidate record. For production, duplicate detection can be added using: (1) MD5/SHA256 hash of the raw text to detect identical files. (2) Cosine similarity between TF-IDF vectors of resume texts (>95% similarity flagged as duplicate). (3) Email-based deduplication (reject if candidate email already exists for the same role). This is listed as a future enhancement."],
        
        ["Q12. What is the significance of whole-word boundary matching (\\b) in your regex?",
         "The \\b (word boundary) assertion in regex ensures we match complete words. Without it, 'Java' would match inside 'JavaScript', 'Javadoc', or 'AvaSharma'. With \\b, only the exact standalone word 'Java' matches. This is critical for accurate keyword matching — without it, nearly every resume would match 'Java' simply because it contains 'JavaScript'. Similarly, 'SQL' with boundaries won't match 'MySQL' unless 'MySQL' is explicitly listed as a keyword."]
      ].map(([q, a]) => [
        new Paragraph({
          children: [new TextRun({ text: q, bold: true, size: 22, font: "Arial", color: DARK })],
          spacing: { before: 200, after: 60 }
        }),
        new Paragraph({
          children: [new TextRun({ text: a, size: 21, font: "Arial", color: "374151" })],
          shading: { fill: "F8FAFC", type: ShadingType.CLEAR },
          spacing: { before: 40, after: 160 },
          indent: { left: 360 },
          border: { left: { style: BorderStyle.SINGLE, size: 4, color: SUCCESS, space: 8 } }
        })
      ]).flat(),

      // ═══ 8. PROJECT STRUCTURE ═══
      new Paragraph({ children: [new PageBreak()] }),
      h1("8. Project File Structure"),
      
      codeBlock("resume_screener/"),
      codeBlock("├── app.py                    # Main Flask application + all routes"),
      codeBlock("├── resume_screener.db        # SQLite database (auto-created)"),
      codeBlock("├── uploads/                  # Uploaded resume files (PDF/DOCX)"),
      codeBlock("└── templates/"),
      codeBlock("    ├── base.html             # Layout with sidebar navigation"),
      codeBlock("    ├── index.html            # Dashboard with stats"),
      codeBlock("    ├── roles.html            # Job roles listing"),
      codeBlock("    ├── new_role.html         # Create job role form"),
      codeBlock("    ├── edit_role.html        # Edit job role form"),
      codeBlock("    ├── upload.html           # Resume upload page"),
      codeBlock("    ├── results.html          # Screening results + bulk email"),
      codeBlock("    ├── candidate_detail.html # Individual candidate analysis"),
      codeBlock("    └── email_settings.html   # SMTP configuration"),
      spacer(),

      h2("Setup & Run Instructions"),
      bullet("Step 1: Install Python 3.8+ and pip"),
      bullet("Step 2: pip install flask pdfplumber python-docx"),
      bullet("Step 3: cd resume_screener"),
      bullet("Step 4: python app.py"),
      bullet("Step 5: Open http://localhost:5000 in browser"),
      bullet("Step 6: Click 'Load Default IT Roles' to populate 10 default job roles"),
      bullet("Step 7: Configure SMTP in Email Settings"),
      bullet("Step 8: Upload resumes and start screening!"),
      spacer(),

      new Paragraph({
        children: [new TextRun({ text: "End of Documentation", bold: true, size: 24, color: GRAY, font: "Arial" })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 400 }
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("resume_screener_documentation.docx", buf);
  console.log("Documentation created!");
}).catch(console.error);
