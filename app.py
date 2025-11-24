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
import re

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

def sanitize_filename(text):
    """Remove special characters and spaces from filename"""
    # Remove any characters that aren't alphanumeric, hyphen, or underscore
    text = re.sub(r'[^\w\-]', '', text)
    return text

def generate_expense_report(data, purchase_documents, signature_data):
    """Generate PDF expense report"""
    report_id = str(uuid.uuid4())
    
    # Create sanitized filename
    last_name = sanitize_filename(data['requestor_last'])
    event_name = sanitize_filename(data['event_name'])
    event_date = sanitize_filename(data['event_date'].replace('-', ''))
    
    report_filename = f"{last_name}_{event_name}_{event_date}.pdf"
    report_path = os.path.join(app.config['REPORT_FOLDER'], report_filename)
    
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
    
    warning_style = ParagraphStyle(
        'WarningStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#a70000'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph("TROOP 233/2233 EXPENSE REIMBURSEMENT", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Warning about reimbursement
    story.append(Paragraph("⚠️ IMPORTANT: Reimbursement will go to Requestor's account", warning_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("NEXT STEPS: You MUST email this expense report to the treasurer through Troopweb Host in order to be reimbursed.", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Event Information
    requestor_name = f"{data['requestor_first']} {data['requestor_last']}"
    event_data = [
        ['Requestor:', requestor_name],
        ['Email:', data['email']],
        ['Troop #:', data['troop_number']],
        ['Event Name:', data['event_name']],
        ['Event Date:', data['event_date']],
        ['Reason / Description:', Paragraph(data['reason'], header_style)],
        ['Date Created:', data['date_created']]
    ]
    
    event_table = Table(event_data, colWidths=[2*inch, 4.5*inch])
    event_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
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
    
    for purchase in data['purchases']:
        if purchase['date']:
            amount = float(purchase['amount']) if purchase['amount'] else 0.0
            total_purchases += amount
            purchase_data.append([
                purchase['date'],
                purchase['place'],
                purchase['items'],
                f"${amount:.2f}"
            ])
    
    # Add empty row if no purchases
    if len(purchase_data) == 1:
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
    
    for mileage in data['mileage']:
        if mileage['date']:
            miles = float(mileage['miles']) if mileage['miles'] else 0.0
            cost = miles * MILEAGE_RATE
            total_miles += miles
            total_mileage_cost += cost
            mileage_data.append([
                mileage['date'],
                mileage['start'],
                mileage['destination'],
                f"{miles:.2f}" if miles else '',
                f"${cost:.2f}"
            ])
    
    # Add empty row if no mileage
    if len(mileage_data) == 1:
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
    story.append(Spacer(1, 0.3*inch))
    
    # Signature Section
    if signature_data:
        signature_style = ParagraphStyle(
            'SignatureStyle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8
        )
        
        story.append(Paragraph("SIGNATURE AND ACKNOWLEDGMENT", title_style))
        story.append(Spacer(1, 0.15*inch))
        
        story.append(Paragraph("By submitting this expense reimbursement report, I affirm that:", signature_style))
        story.append(Paragraph("• All information provided is true, honest, and accurate to the best of my knowledge", signature_style))
        story.append(Paragraph("• All expenses listed were incurred for legitimate Troop 233/2233 activities", signature_style))
        story.append(Paragraph("• I have provided accurate receipts and supporting documentation", signature_style))
        story.append(Paragraph("• I understand this submission is made in accordance with the Scout Law", signature_style))
        story.append(Spacer(1, 0.15*inch))
        
        scout_law_text = "<b>Scout Law:</b> <i>A Scout is Trustworthy, Loyal, Helpful, Friendly, Courteous, Kind, Obedient, Cheerful, Thrifty, Brave, Clean, and Reverent.</i>"
        story.append(Paragraph(scout_law_text, signature_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Signature table
        signature_table_data = [
            ['Electronic Signature:', signature_data['name']],
            ['Date Signed:', signature_data['date']],
            ['Acknowledgment:', 'Confirmed in accordance with Scout Law']
        ]
        
        sig_table = Table(signature_table_data, colWidths=[2*inch, 4.5*inch])
        sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(sig_table)
    
    # Supporting Documents - organized by purchase
    if purchase_documents:
        story.append(PageBreak())
        story.append(Paragraph("SUPPORTING DOCUMENTS", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Iterate through purchases and their documents
        for purchase_index, purchase in enumerate(data['purchases']):
            if purchase['date'] and purchase_index in purchase_documents:
                # Add purchase info header
                purchase_header = f"Purchase #{purchase_index + 1}: {purchase['items']} - ${purchase['amount']}"
                purchase_header_para = Paragraph(purchase_header, ParagraphStyle(
                    'PurchaseHeader',
                    parent=styles['Normal'],
                    fontSize=12,
                    fontName='Helvetica-Bold',
                    textColor=colors.HexColor('#003f87'),
                    spaceAfter=10
                ))
                story.append(purchase_header_para)
                
                file_path = purchase_documents[purchase_index]
                try:
                    # Handle images
                    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                        img = PILImage.open(file_path)
                        img_width, img_height = img.size
                        
                        # Scale image to fit page
                        max_width = 6.5 * inch
                        max_height = 7 * inch
                        
                        aspect = img_height / float(img_width)
                        if img_width > max_width:
                            img_width = max_width
                            img_height = img_width * aspect
                        
                        if img_height > max_height:
                            img_height = max_height
                            img_width = img_height / aspect
                        
                        story.append(Image(file_path, width=img_width, height=img_height))
                        story.append(Spacer(1, 0.3*inch))
                    
                    # Handle PDFs converted to images
                    elif file_path.lower().endswith('.pdf'):
                        pdf_images = convert_pdf_to_images(file_path, app.config['UPLOAD_FOLDER'])
                        for pdf_img in pdf_images:
                            img = PILImage.open(pdf_img)
                            img_width, img_height = img.size
                            
                            max_width = 6.5 * inch
                            max_height = 7 * inch
                            
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
                
                # Add page break between purchases if not the last one
                if purchase_index < len([p for p in data['purchases'] if p['date']]) - 1:
                    story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    return report_id, report_filename

@app.route('/')
def index():
    cleanup_old_files()
    return render_template('expense_form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Collect form data
        data = {
            'requestor_first': request.form.get('requestor_first', ''),
            'requestor_last': request.form.get('requestor_last', ''),
            'email': request.form.get('email', ''),
            'troop_number': request.form.get('troop_number', ''),
            'event_name': request.form.get('event_name', ''),
            'event_date': request.form.get('event_date', ''),
            'reason': request.form.get('reason', ''),
            'date_created': request.form.get('date_created', ''),
            'purchases': [],
            'mileage': []
        }
        
        # Collect signature data
        signature_data = {
            'name': request.form.get('signature_name', ''),
            'date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            'acknowledgment': request.form.get('signature_acknowledgment', '') == 'on'
        }
        
        # Dictionary to store purchase documents mapped to their index
        purchase_documents = {}
        
        # Collect purchase data and associated files
        i = 0
        while True:
            date = request.form.get(f'purchase_date_{i}', None)
            if date is None:
                break
            
            if date:  # Only add if date is provided
                data['purchases'].append({
                    'date': date,
                    'place': request.form.get(f'purchase_place_{i}', ''),
                    'items': request.form.get(f'items_summary_{i}', ''),
                    'amount': request.form.get(f'purchase_amount_{i}', '')
                })
                
                # Handle file upload for this specific purchase
                file_key = f'purchase_doc_{i}'
                if file_key in request.files:
                    file = request.files[file_key]
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(filepath)
                        # Map the file to this purchase index
                        purchase_documents[len(data['purchases']) - 1] = filepath
            i += 1
        
        # Collect mileage data (dynamic number of rows)
        i = 0
        while True:
            date = request.form.get(f'mileage_date_{i}', None)
            if date is None:
                break
            
            if date:  # Only add if date is provided
                data['mileage'].append({
                    'date': date,
                    'start': request.form.get(f'mileage_start_{i}', ''),
                    'destination': request.form.get(f'mileage_dest_{i}', ''),
                    'miles': request.form.get(f'mileage_miles_{i}', '')
                })
            i += 1
        
        # Generate PDF
        report_id, report_filename = generate_expense_report(data, purchase_documents, signature_data)
        
        return redirect(url_for('download', report_id=report_id, filename=report_filename))
    
    except Exception as e:
        return f"Error generating report: {str(e)}", 500

@app.route('/download/<report_id>')
def download(report_id):
    filename = request.args.get('filename', f'expense_report_{report_id}.pdf')
    return render_template('download.html', report_id=report_id, filename=filename)

@app.route('/get_report/<filename>')
def get_report(filename):
    report_path = os.path.join(app.config['REPORT_FOLDER'], filename)
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True, download_name=filename)
    return "Report not found", 404

if __name__ == '__main__':
    app.run(debug=True)
