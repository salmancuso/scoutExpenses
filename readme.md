# Troop 233 Expense Reimbursement System

A web-based application for creating professional PDF expense reimbursement reports for Troop 233. This Flask application allows users to submit expense information through a web form and generates a formatted PDF report that matches the organization's official reimbursement form.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)
- [Contributing](#contributing)

## ✨ Features

### Core Functionality
- **Web-Based Form Interface**: Clean, intuitive form for entering expense information
- **Event Information Tracking**: Capture event name, dates, descriptions, and submission date
- **Purchase Tracking**: Support for up to 5 purchase line items with date, location, description, and amount
- **Mileage Reimbursement**: Up to 4 mileage entries with automatic calculation at $0.625 per mile
- **Real-Time Calculations**: Live updates of totals as you enter data
- **Document Upload Support**: Attach receipts and supporting documents in multiple formats

### Document Management
- **Multi-Format Support**: Upload JPEG, JPG, PNG, TIFF, and PDF files
- **Automatic PDF Conversion**: PDFs are converted to images for seamless integration
- **Professional PDF Output**: Generated reports match the official Troop 233 format
- **Supporting Documents Section**: All uploaded documents are appended to the final report

### Maintenance & Security
- **Automatic Cleanup**: Files older than 7 days are automatically deleted
- **Secure File Handling**: Filename sanitization and type validation
- **File Size Limits**: 16MB maximum per upload to prevent abuse
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## 🔧 Prerequisites

Before installing the application, ensure your system has the following:

### Required Software
- **Python 3.8 or higher** ([Download](https://www.python.org/downloads/))
- **pip** (Python package manager - included with Python)
- **poppler-utils** (PDF processing library)

### Installing Poppler

Poppler is required for converting PDF documents to images.

#### Ubuntu/Debian Linux
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

#### macOS
```bash
brew install poppler
```

#### Windows
1. Download poppler for Windows: [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases/)
2. Extract the ZIP file to a location (e.g., `C:\Program Files\poppler`)
3. Add the `bin` folder to your system PATH:
   - Open System Properties → Environment Variables
   - Edit the PATH variable
   - Add the full path to the `bin` folder (e.g., `C:\Program Files\poppler\bin`)
   - Click OK and restart your terminal

### Verify Poppler Installation
```bash
pdftoppm -v
```
You should see version information if poppler is correctly installed.

## 📥 Installation

### Step 1: Create Project Directory

```bash
# Create the main project directory
mkdir expense-report
cd expense-report

# Create subdirectories
mkdir templates uploads reports
```

### Step 2: Download Project Files

Place the following files in their respective locations:

```
expense-report/
├── app.py                    # Main application file (root directory)
├── requirements.txt          # Python dependencies (root directory)
├── templates/
│   ├── expense_form.html    # Main form page
│   └── download.html        # Download confirmation page
├── uploads/                 # Auto-created for temporary file storage
└── reports/                 # Auto-created for generated PDFs
```

### Step 3: Create Virtual Environment (Recommended)

A virtual environment keeps your project dependencies isolated.

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt when activated.

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- ReportLab (PDF generation)
- Pillow (image processing)
- PyPDF2 (PDF manipulation)
- pdf2image (PDF to image conversion)
- Werkzeug (utilities)

### Step 5: Verify Installation

```bash
python -c "import flask, reportlab, PIL, PyPDF2, pdf2image; print('All packages installed successfully!')"
```

If you see the success message, you're ready to run the application!

## 🚀 Usage

### Starting the Application

1. **Navigate to the project directory:**
```bash
cd expense-report
```

2. **Activate the virtual environment** (if not already activated):
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Run the application:**
```bash
python app.py
```

4. **Open your web browser and visit:**
```
http://127.0.0.1:5000
```

You should see the Troop 233 Expense Reimbursement Form.

### Creating an Expense Report

#### 1. Event Information (Required)
Fill in the basic event details:
- **Event Name**: Name of the event (e.g., "Summer Camp 2025")
- **Event Date(s)**: Date range or specific dates (e.g., "June 15-17, 2025")
- **Reason/Description**: Brief description of the event and expenses
- **Date Submitted**: Automatically set to today's date (can be changed)

#### 2. Items Purchased (Optional - up to 5 items)
For each purchase, enter:
- **Date Purchased**: When the purchase was made
- **Place Purchased**: Store or vendor name
- **Items Purchased**: Description of what was bought
- **$ Amount**: Cost in dollars (e.g., 45.99)

**Note:** You must enter at least one purchase OR one mileage entry to submit the form.

#### 3. Mileage Reimbursement (Optional - up to 4 entries)
For each trip, enter:
- **Date**: When the trip occurred
- **Start Location**: Where you departed from
- **Destination**: Where you traveled to
- **Miles**: Distance traveled (accepts decimals like 45.72)

The mileage cost is automatically calculated at $0.625 per mile.

#### 4. Supporting Documents (Optional)
- Click "Choose Files" to select receipts or supporting documents
- You can select multiple files at once
- Accepted formats: JPEG, JPG, PNG, TIFF, PDF
- Maximum file size: 16MB per file

#### 5. Review Totals
The form automatically calculates:
- **Total Purchases**: Sum of all purchase amounts
- **Total Mileage**: Total miles × $0.625 per mile
- **Grand Total**: Sum of purchases and mileage

#### 6. Generate Report
- Click the "Generate Expense Report" button
- You'll be redirected to the download page
- Click "Download PDF Report" to save your report
- The report includes all your entries and supporting documents

### Stopping the Application

Press `Ctrl+C` in the terminal where the application is running.

## ⚙️ Configuration

### Changing the Mileage Rate

The current rate is $0.625 per mile. To change it:

**In `app.py` (line 17):**
```python
MILEAGE_RATE = 0.625  # Change to your desired rate
```

**In `templates/expense_form.html` (line 244):**
```html
<p><strong>Current Rate:</strong> $0.625 per mile</p>
```

**In `templates/expense_form.html` (line 418):**
```javascript
const mileageRate = 0.625;
```

### Adjusting File Retention Period

Files are deleted after 7 days by default. To change this:

**In `app.py` (line 26 in `cleanup_old_files()` function):**
```python
cutoff_date = datetime.now() - timedelta(days=7)  # Change days=7 to desired period
```

### Changing Maximum File Upload Size

The default is 16MB. To change it:

**In `app.py` (line 15):**
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Size in bytes
```

### Modifying Number of Line Items

To change the number of purchase or mileage rows:

1. **In `app.py`:**
   - Line 186: Change `range(5)` for purchases
   - Line 198: Change `range(4)` for mileage

2. **In `templates/expense_form.html`:**
   - Add or remove `<tr>` rows in the purchase and mileage tables
   - Update the range indices in the `name` attributes

## 📁 Project Structure

```
expense-report/
│
├── app.py                          # Main Flask application
│   ├── Route handlers (/,/submit, /download, /get_report)
│   ├── PDF generation logic
│   ├── File upload handling
│   └── Cleanup functions
│
├── requirements.txt                # Python package dependencies
│
├── templates/                      # HTML templates
│   ├── expense_form.html          # Main expense entry form
│   │   ├── Event information section
│   │   ├── Purchase items table
│   │   ├── Mileage reimbursement table
│   │   ├── File upload section
│   │   ├── Real-time total calculations
│   │   └── Form validation
│   │
│   └── download.html              # Download confirmation page
│       ├── Success message
│       ├── Download button
│       └── File retention warning
│
├── uploads/                        # Temporary storage for uploaded files
│   └── (Auto-cleaned after 7 days)
│
└── reports/                        # Generated PDF reports
    └── (Auto-cleaned after 7 days)
```

### Key Components

#### app.py Functions
- `allowed_file()`: Validates file extensions
- `cleanup_old_files()`: Removes files older than 7 days
- `convert_pdf_to_images()`: Converts PDF pages to images
- `generate_expense_report()`: Creates the final PDF report
- Route handlers: Process form submissions and serve files

#### Templates
- **expense_form.html**: User interface for data entry with live calculations
- **download.html**: Confirmation page with download link

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Issue: PDF Conversion Errors
**Error Message:** `pdf2image.exceptions.PDFInfoNotInstalledError`

**Solution:**
- Ensure poppler-utils is installed (see [Prerequisites](#prerequisites))
- On Windows, verify the poppler `bin` folder is in your PATH
- Restart your terminal after installing poppler

**Test poppler:**
```bash
pdftoppm -v
```

---

#### Issue: File Upload Fails
**Error Message:** "File too large" or uploads not working

**Solution:**
- Check that `uploads/` directory exists and has write permissions
- Verify files are under 16MB
- Ensure file format is supported (jpg, jpeg, png, tiff, pdf)

**Check directory permissions:**
```bash
# Windows
icacls uploads

# macOS/Linux
ls -la uploads/
```

---

#### Issue: Port Already in Use
**Error Message:** `Address already in use`

**Solution:**
Change the port in `app.py` (last line):
```python
app.run(debug=True, port=5001)  # Change to any available port
```

Or find and kill the process using port 5000:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# macOS/Linux
lsof -i :5000
kill -9 <process_id>
```

---

#### Issue: ImportError for Python Packages
**Error Message:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
- Ensure your virtual environment is activated
- Reinstall dependencies:
```bash
pip install -r requirements.txt
```

---

#### Issue: Mileage Not Appearing in PDF
**Symptoms:** Mileage entries don't show up in generated PDF

**Solution:**
- This was a known bug and has been fixed
- Ensure you're using the latest version of `app.py`
- Mileage rows now appear if ANY field is filled (date, start, destination, or miles)

---

#### Issue: Can't Enter Decimal Miles
**Symptoms:** Form only accepts whole numbers for mileage

**Solution:**
- This was a known bug and has been fixed
- The form now accepts decimal values (e.g., 45.72)
- Ensure you're using the latest version of `templates/expense_form.html`

## 🌐 Production Deployment

**⚠️ Warning:** The built-in Flask development server is not suitable for production use.

### Recommended Production Setup

#### 1. Use a Production WSGI Server

Install Gunicorn (Linux/macOS) or Waitress (Windows):
```bash
# Linux/macOS
pip install gunicorn

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Windows
pip install waitress

# Run with Waitress
waitress-serve --port=8000 app:app
```

#### 2. Set Environment Variables

```bash
# Disable debug mode
export FLASK_ENV=production

# Set a secret key for session security
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
```

Add to `app.py`:
```python
import os
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
```

#### 3. Configure a Reverse Proxy

Use nginx or Apache to proxy requests to Gunicorn.

**Example nginx configuration:**
```nginx
server {
    listen 80;
    server_name expense.troop233.org;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /uploads/ {
        deny all;
    }

    client_max_body_size 20M;
}
```

#### 4. Enable HTTPS

Use Let's Encrypt for free SSL certificates:
```bash
sudo certbot --nginx -d expense.troop233.org
```

#### 5. Set Up Automatic Cleanup

Add to crontab to run cleanup daily at 2 AM:
```bash
crontab -e

# Add this line:
0 2 * * * cd /path/to/expense-report && /path/to/venv/bin/python -c "from app import cleanup_old_files; cleanup_old_files()"
```

#### 6. Implement User Authentication (Optional)

For production, consider adding:
- User login/registration
- Role-based access (submitters, approvers, treasurers)
- Audit logging
- Database storage for reports

### Security Checklist

- [ ] Debug mode disabled (`FLASK_ENV=production`)
- [ ] Strong secret key set
- [ ] HTTPS enabled with valid SSL certificate
- [ ] File upload directory not publicly accessible
- [ ] Regular backups configured
- [ ] Rate limiting implemented
- [ ] User authentication added (if needed)
- [ ] Error logging configured
- [ ] Regular security updates scheduled

## 📝 Additional Notes

### File Retention Policy

All uploaded files and generated reports are automatically deleted after 7 days. This:
- Protects user privacy
- Saves storage space
- Complies with data retention best practices

**Important:** Users should download their reports promptly. Consider sending email notifications with download links for important reports.

### Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Data Privacy

- No data is stored in a database by default
- All information is only in temporary files
- Files are automatically cleaned up after 7 days
- Consider adding GDPR/privacy policy for production use

## 🤝 Contributing

To contribute improvements:

1. Test your changes thoroughly
2. Document any new features in this README
3. Ensure backward compatibility
4. Update version numbers if applicable

## 📄 License

This project is provided for use by Troop 233 and affiliated Scout organizations.

## 🆘 Support

For issues, questions, or feature requests:
- Contact your troop's technology coordinator
- Check the [Troubleshooting](#troubleshooting) section
- Review the [Flask documentation](https://flask.palletsprojects.com/)
- Review the [ReportLab documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [Poppler Documentation](https://poppler.freedesktop.org/)

---

**Version:** 1.1  
**Last Updated:** October 2025  
**Maintained by:** Troop 233 Technology Team