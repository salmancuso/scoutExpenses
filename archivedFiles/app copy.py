#!/usr/bin/python3

from flask import Flask, render_template, request, send_file, url_for, redirect
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image as PILImage
from PyPDF2 import PdfReader
import os
import uuid
from pdf2image import convert_from_path
import sys
import logging
import os
from pathlib import Path

# Get the absolute path of the app directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(stream=sys.stderr)

app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/tools/scoutExpenses'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['REPORT_FOLDER'] = os.path.join(BASE_DIR, 'reports')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'tiff', 'pdf'}

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

MILEAGE_RATE = 0.625

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cleanup_old_files():
    """Remove files older than 7 days"""
    cutoff_date = datetime.now() - timedelta(days=7)
    
    for folder in [app.config['UPLOAD_FOLDER'], app.config['REPORT_FOLDER']]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    os.remove(filepath)

def convert_pdf_to_images(pdf_path, output_folder):
    """Convert PDF pages to images"""
    try:
        images = convert_from_path(pdf_path, dpi=150)
        image_paths = []
        
        for i, image in enumerate(images):
            image_path = os.path.join(output_folder, f"{uuid.uuid4()}_page{i}.png")
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
        
        return image_paths
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return []

def generate_expense_report(data, supporting_files):
    """Generate PDF expense report"""
    report_id = str(uuid.uuid4())
    report_path = os.path.join(app.config['REPORT_FOLDER'], f"expense_report_{report_id}.pdf")
    
    doc = SimpleDocTemplate(report_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#000000'),
        spaceAfter=10,
        alignment=TA_CENTER
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph("TROOP 233/2233 EXPENSE REIMBURSEMENT", title_style))
    story.append(Paragraph("NEXT STEPS: After you create your Expense Report PDF, please remember to email it to the treasurer through Troopweb Host.",title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Event Information
    event_data = [
        ['Requested From:', data['requester']],
        ['Event Details:', Paragraph(data['event_dates'], header_style)],
        ['Reason / Description:', Paragraph(data['reason'], header_style)],
        ['Date Created:', data['date_submitted']]
    ]
    
    event_table = Table(event_data, colWidths=[2*inch, 4.5*inch])
    event_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Add this line
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))

    story.append(event_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Purchases Table
    purchase_data = [['Date Purchased', 'Place Purchased', 'Items Purchased', '$ Amount']]
    total_purchases = 0.0
    
    for i in range(5):
        if data['purchases'][i]['date']:
            amount = float(data['purchases'][i]['amount']) if data['purchases'][i]['amount'] else 0.0
            total_purchases += amount
            purchase_data.append([
                data['purchases'][i]['date'],
                data['purchases'][i]['place'],
                data['purchases'][i]['items'],
                f"${amount:.2f}"
            ])
        else:
            purchase_data.append(['', '', '', ''])
    
    purchase_data.append(['', '', 'Total All Items Purchased', f"${total_purchases:.2f}"])
    
    purchase_table = Table(purchase_data, colWidths=[1.2*inch, 1.8*inch, 3*inch, 1*inch])
    purchase_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(purchase_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Mileage Table
    mileage_data = [['Date', 'Start Location', 'Destination', 'Miles', f'Total x ${MILEAGE_RATE}/Mi']]
    total_miles = 0.0
    total_mileage_cost = 0.0
    
    for i in range(4):
        # Check if any mileage field is filled
        if (data['mileage'][i]['date'] or data['mileage'][i]['start'] or 
            data['mileage'][i]['destination'] or data['mileage'][i]['miles']):
            miles = float(data['mileage'][i]['miles']) if data['mileage'][i]['miles'] else 0.0
            cost = miles * MILEAGE_RATE
            total_miles += miles
            total_mileage_cost += cost
            mileage_data.append([
                data['mileage'][i]['date'],
                data['mileage'][i]['start'],
                data['mileage'][i]['destination'],
                f"{miles:.2f}" if miles else '',
                f"${cost:.2f}"
            ])
        else:
            mileage_data.append(['', '', '', '', ''])
    
    mileage_data.append(['', '', 'All Miles Total', f"{total_miles:.2f}", f"${total_mileage_cost:.2f}"])
    
    mileage_table = Table(mileage_data, colWidths=[1*inch, 1.8*inch, 1.8*inch, 0.8*inch, 1.6*inch])
    mileage_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(mileage_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Grand Total
    grand_total = total_purchases + total_mileage_cost
    total_data = [['Grand Total Amount', f"${grand_total:.2f}"]]
    total_table = Table(total_data, colWidths=[5*inch, 2*inch])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(total_table)
    
    # Supporting Documents
    if supporting_files:
        story.append(PageBreak())
        story.append(Paragraph("SUPPORTING DOCUMENTS", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        for file_path in supporting_files:
            try:
                # Handle images
                if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                    img = PILImage.open(file_path)
                    img_width, img_height = img.size
                    
                    # Scale image to fit page
                    max_width = 6.5 * inch
                    max_height = 8 * inch
                    
                    aspect = img_height / float(img_width)
                    if img_width > max_width:
                        img_width = max_width
                        img_height = img_width * aspect
                    
                    if img_height > max_height:
                        img_height = max_height
                        img_width = img_height / aspect
                    
                    story.append(Image(file_path, width=img_width, height=img_height))
                    story.append(Spacer(1, 0.2*inch))
                
                # Handle PDFs converted to images
                elif file_path.lower().endswith('.pdf'):
                    pdf_images = convert_pdf_to_images(file_path, app.config['UPLOAD_FOLDER'])
                    for pdf_img in pdf_images:
                        img = PILImage.open(pdf_img)
                        img_width, img_height = img.size
                        
                        max_width = 6.5 * inch
                        max_height = 8 * inch
                        
                        aspect = img_height / float(img_width)
                        if img_width > max_width:
                            img_width = max_width
                            img_height = img_width * aspect
                        
                        if img_height > max_height:
                            img_height = max_height
                            img_width = img_height / aspect
                        
                        story.append(Image(pdf_img, width=img_width, height=img_height))
                        story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                print(f"Error adding file {file_path}: {e}")
    
    # Build PDF
    doc.build(story)
    return report_id

@app.route('/')
def index():
    cleanup_old_files()
    return render_template('expense_form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Collect form data
        data = {
            'requester': request.form.get('requester', ''),
            'event_dates': request.form.get('event_dates', ''),
            'reason': request.form.get('reason', ''),
            'date_submitted': request.form.get('date_submitted', ''),
            'purchases': [],
            'mileage': []
        }
        
        # Collect purchase data
        for i in range(5):
            data['purchases'].append({
                'date': request.form.get(f'purchase_date_{i}', ''),
                'place': request.form.get(f'purchase_place_{i}', ''),
                'items': request.form.get(f'purchase_items_{i}', ''),
                'amount': request.form.get(f'purchase_amount_{i}', '')
            })
        
        # Collect mileage data
        for i in range(4):
            data['mileage'].append({
                'date': request.form.get(f'mileage_date_{i}', ''),
                'start': request.form.get(f'mileage_start_{i}', ''),
                'destination': request.form.get(f'mileage_dest_{i}', ''),
                'miles': request.form.get(f'mileage_miles_{i}', '')
            })
        
        # Handle file uploads
        uploaded_files = []
        files = request.files.getlist('supporting_docs')
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                uploaded_files.append(filepath)
        
        # Generate PDF
        report_id = generate_expense_report(data, uploaded_files)
        
        return redirect(url_for('download', report_id=report_id))
    
    except Exception as e:
        return f"Error generating report: {str(e)}", 500

@app.route('/download/<report_id>')
def download(report_id):
    return render_template('download.html', report_id=report_id)

@app.route('/get_report/<report_id>')
def get_report(report_id):
    report_path = os.path.join(app.config['REPORT_FOLDER'], f"expense_report_{report_id}.pdf")
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True, download_name=f"Troop233_Expense_Report_{report_id[:8]}.pdf")
    return "Report not found", 404

if __name__ == '__main__':
    app.run(debug=True)
