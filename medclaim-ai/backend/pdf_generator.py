"""
PDF Generation Service for Claim Forms
Generates PDFs for both synthetic and vendor-specific claim forms
"""
import os
import io
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import requests
from PIL import Image
import tempfile
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for claim forms."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ClaimTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.grey,
            borderPadding=5
        ))
        
        # Field label style
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))
        
        # Field value style
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            leftIndent=20
        ))
    
    def generate_synthetic_claim_pdf(self, form_data: Dict[str, Any], output_path: str) -> str:
        """Generate a synthetic claim form PDF."""
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        # Title
        story.append(Paragraph("MEDICAL INSURANCE CLAIM FORM", self.styles['ClaimTitle']))
        story.append(Spacer(1, 20))
        
        # Form Information
        info_data = [
            ['Claim ID:', form_data.get('claim_id', 'N/A')],
            ['Form Type:', 'Synthetic Form'],
            ['Generated Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Patient Information Section
        story.append(Paragraph("PATIENT INFORMATION", self.styles['SectionHeader']))
        patient_data = [
            ['Patient Name:', form_data.get('patient_name', 'N/A')],
            ['Policy Number:', form_data.get('policy_number', 'N/A')],
            ['Date of Birth:', form_data.get('date_of_birth', 'N/A')],
            ['Contact Number:', form_data.get('contact_number', 'N/A')],
            ['Email:', form_data.get('email', 'N/A')]
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        # Insurance Information Section
        story.append(Paragraph("INSURANCE INFORMATION", self.styles['SectionHeader']))
        insurance_data = [
            ['Insurance Company:', form_data.get('insurer_name', 'N/A')],
            ['Coverage Amount:', f"₹{form_data.get('coverage_amount', 'N/A')}"],
            ['Deductible:', f"₹{form_data.get('deductible', 'N/A')}"],
            ['Copay Percentage:', f"{form_data.get('copay_percentage', 'N/A')}%"]
        ]
        
        insurance_table = Table(insurance_data, colWidths=[2*inch, 4*inch])
        insurance_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(insurance_table)
        story.append(Spacer(1, 20))
        
        # Medical Information Section
        story.append(Paragraph("MEDICAL INFORMATION", self.styles['SectionHeader']))
        medical_data = [
            ['Hospital/Facility:', form_data.get('hospital_name', 'N/A')],
            ['Doctor Name:', form_data.get('doctor_name', 'N/A')],
            ['Service Date:', form_data.get('service_date', 'N/A')],
            ['Admission Date:', form_data.get('admission_date', 'N/A')],
            ['Discharge Date:', form_data.get('discharge_date', 'N/A')],
            ['Total Amount:', f"₹{form_data.get('total_amount', 'N/A')}"],
            ['Diagnosis:', form_data.get('diagnosis', 'N/A')],
            ['Room Type:', form_data.get('room_type', 'N/A')]
        ]
        
        medical_table = Table(medical_data, colWidths=[2*inch, 4*inch])
        medical_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(medical_table)
        story.append(Spacer(1, 20))
        
        # Procedures Section
        if form_data.get('procedures') and len(form_data['procedures']) > 0:
            story.append(Paragraph("PROCEDURES/TREATMENTS", self.styles['SectionHeader']))
            for i, procedure in enumerate(form_data['procedures'], 1):
                story.append(Paragraph(f"{i}. {procedure}", self.styles['FieldValue']))
            story.append(Spacer(1, 20))
        
        # Bank Details Section
        story.append(Paragraph("BANK DETAILS", self.styles['SectionHeader']))
        bank_details = form_data.get('bank_details', {})
        bank_data = [
            ['Account Holder Name:', bank_details.get('account_holder_name', 'N/A')],
            ['Account Number:', bank_details.get('account_number', 'N/A')],
            ['IFSC Code:', bank_details.get('ifsc_code', 'N/A')],
            ['Bank Name:', bank_details.get('bank_name', 'N/A')]
        ]
        
        bank_table = Table(bank_data, colWidths=[2*inch, 4*inch])
        bank_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(bank_table)
        story.append(Spacer(1, 20))
        
        # Signature Section
        story.append(Paragraph("SIGNATURE", self.styles['SectionHeader']))
        story.append(Paragraph("Patient/Policy Holder Signature: _________________________", self.styles['FieldValue']))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Date: _________________________", self.styles['FieldValue']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def generate_vendor_claim_pdf(self, form_data: Dict[str, Any], vendor_name: str, output_path: str) -> str:
        """Generate a vendor-specific claim form PDF."""
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        # Vendor-specific header
        story.append(Paragraph(f"{vendor_name.upper()} - MEDICAL INSURANCE CLAIM FORM", self.styles['ClaimTitle']))
        story.append(Spacer(1, 20))
        
        # Form Information
        info_data = [
            ['Claim ID:', form_data.get('claim_id', 'N/A')],
            ['Vendor:', vendor_name],
            ['Generated Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Rest of the form follows the same structure as synthetic form
        # Patient Information Section
        story.append(Paragraph("PATIENT INFORMATION", self.styles['SectionHeader']))
        patient_data = [
            ['Patient Name:', form_data.get('patient_name', 'N/A')],
            ['Policy Number:', form_data.get('policy_number', 'N/A')],
            ['Date of Birth:', form_data.get('date_of_birth', 'N/A')],
            ['Contact Number:', form_data.get('contact_number', 'N/A')],
            ['Email:', form_data.get('email', 'N/A')]
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        # Insurance Information Section
        story.append(Paragraph("INSURANCE INFORMATION", self.styles['SectionHeader']))
        insurance_data = [
            ['Insurance Company:', form_data.get('insurer_name', 'N/A')],
            ['Coverage Amount:', f"₹{form_data.get('coverage_amount', 'N/A')}"],
            ['Deductible:', f"₹{form_data.get('deductible', 'N/A')}"],
            ['Copay Percentage:', f"{form_data.get('copay_percentage', 'N/A')}%"]
        ]
        
        insurance_table = Table(insurance_data, colWidths=[2*inch, 4*inch])
        insurance_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(insurance_table)
        story.append(Spacer(1, 20))
        
        # Medical Information Section
        story.append(Paragraph("MEDICAL INFORMATION", self.styles['SectionHeader']))
        medical_data = [
            ['Hospital/Facility:', form_data.get('hospital_name', 'N/A')],
            ['Doctor Name:', form_data.get('doctor_name', 'N/A')],
            ['Service Date:', form_data.get('service_date', 'N/A')],
            ['Admission Date:', form_data.get('admission_date', 'N/A')],
            ['Discharge Date:', form_data.get('discharge_date', 'N/A')],
            ['Total Amount:', f"₹{form_data.get('total_amount', 'N/A')}"],
            ['Diagnosis:', form_data.get('diagnosis', 'N/A')],
            ['Room Type:', form_data.get('room_type', 'N/A')]
        ]
        
        medical_table = Table(medical_data, colWidths=[2*inch, 4*inch])
        medical_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(medical_table)
        story.append(Spacer(1, 20))
        
        # Procedures Section
        if form_data.get('procedures') and len(form_data['procedures']) > 0:
            story.append(Paragraph("PROCEDURES/TREATMENTS", self.styles['SectionHeader']))
            for i, procedure in enumerate(form_data['procedures'], 1):
                story.append(Paragraph(f"{i}. {procedure}", self.styles['FieldValue']))
            story.append(Spacer(1, 20))
        
        # Bank Details Section
        story.append(Paragraph("BANK DETAILS", self.styles['SectionHeader']))
        bank_details = form_data.get('bank_details', {})
        bank_data = [
            ['Account Holder Name:', bank_details.get('account_holder_name', 'N/A')],
            ['Account Number:', bank_details.get('account_number', 'N/A')],
            ['IFSC Code:', bank_details.get('ifsc_code', 'N/A')],
            ['Bank Name:', bank_details.get('bank_name', 'N/A')]
        ]
        
        bank_table = Table(bank_data, colWidths=[2*inch, 4*inch])
        bank_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(bank_table)
        story.append(Spacer(1, 20))
        
        # Signature Section
        story.append(Paragraph("SIGNATURE", self.styles['SectionHeader']))
        story.append(Paragraph("Patient/Policy Holder Signature: _________________________", self.styles['FieldValue']))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Date: _________________________", self.styles['FieldValue']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def download_star_health_template(self) -> str:
        """Download the Star Health template PDF."""
        template_url = "https://d28c6jni2fmamz.cloudfront.net/CLAIMFORM_89ec9742bd.pdf"
        template_path = os.path.join(os.path.dirname(__file__), "templates", "star_health_template.pdf")
        
        # Create templates directory if it doesn't exist
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        # Download template if not exists
        if not os.path.exists(template_path):
            try:
                response = requests.get(template_url, timeout=30)
                response.raise_for_status()
                with open(template_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded Star Health template to {template_path}")
            except Exception as e:
                print(f"Failed to download Star Health template: {e}")
                return None
        
        return template_path
    
    def generate_star_health_claim_pdf(self, form_data: Dict[str, Any], output_path: str) -> str:
        """Generate a Star Health claim form PDF using the actual template."""
        try:
            # Download the Star Health template
            template_path = self.download_star_health_template()
            if not template_path or not os.path.exists(template_path):
                print("Star Health template not available, falling back to synthetic form")
                return self.generate_synthetic_claim_pdf(form_data, output_path)
            
            # For now, we'll create a form that looks like the Star Health template
            # In a full implementation, you would use PyPDF2 or similar to fill the actual template
            return self.generate_star_health_style_pdf(form_data, output_path)
            
        except Exception as e:
            print(f"Error generating Star Health PDF: {e}")
            # Fallback to synthetic form
            return self.generate_synthetic_claim_pdf(form_data, output_path)
    
    def generate_star_health_style_pdf(self, form_data: Dict[str, Any], output_path: str) -> str:
        """Generate a PDF that mimics the Star Health form style."""
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        story = []
        
        # Star Health Header
        story.append(Paragraph("STAR HEALTH AND ALLIED INSURANCE CO. LTD.", self.styles['ClaimTitle']))
        story.append(Paragraph("MEDICAL INSURANCE CLAIM FORM", self.styles['ClaimTitle']))
        story.append(Spacer(1, 20))
        
        # Form Information
        info_data = [
            ['Policy No.:', form_data.get('policy_number', 'N/A')],
            ['Claim No.:', form_data.get('claim_id', 'N/A')],
            ['Date of Claim:', datetime.now().strftime('%d/%m/%Y')]
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Patient Information Section
        story.append(Paragraph("PATIENT DETAILS", self.styles['SectionHeader']))
        patient_data = [
            ['Name of Insured:', form_data.get('patient_name', 'N/A')],
            ['Date of Birth:', form_data.get('date_of_birth', 'N/A')],
            ['Age:', form_data.get('age', 'N/A')],
            ['Gender:', form_data.get('gender', 'N/A')],
            ['Address:', form_data.get('address', 'N/A')],
            ['Contact No:', form_data.get('contact_number', 'N/A')],
            ['Email ID:', form_data.get('email', 'N/A')]
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        # Hospital Information Section
        story.append(Paragraph("HOSPITAL DETAILS", self.styles['SectionHeader']))
        hospital_data = [
            ['Name of Hospital:', form_data.get('hospital_name', 'N/A')],
            ['Hospital Address:', form_data.get('hospital_address', 'N/A')],
            ['Doctor Name:', form_data.get('doctor_name', 'N/A')],
            ['Date of Admission:', form_data.get('admission_date', 'N/A')],
            ['Date of Discharge:', form_data.get('discharge_date', 'N/A')],
            ['Nature of Illness:', form_data.get('diagnosis', 'N/A')],
            ['Total Bill Amount:', f"₹{form_data.get('total_amount', 'N/A')}"]
        ]
        
        hospital_table = Table(hospital_data, colWidths=[2*inch, 4*inch])
        hospital_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(hospital_table)
        story.append(Spacer(1, 20))
        
        # Bank Details Section
        story.append(Paragraph("BANK DETAILS FOR REIMBURSEMENT", self.styles['SectionHeader']))
        bank_details = form_data.get('bank_details', {})
        bank_data = [
            ['Account Holder Name:', bank_details.get('account_holder_name', 'N/A')],
            ['Account Number:', bank_details.get('account_number', 'N/A')],
            ['IFSC Code:', bank_details.get('ifsc_code', 'N/A')],
            ['Bank Name:', bank_details.get('bank_name', 'N/A')],
            ['Branch:', bank_details.get('branch', 'N/A')]
        ]
        
        bank_table = Table(bank_data, colWidths=[2*inch, 4*inch])
        bank_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(bank_table)
        story.append(Spacer(1, 20))
        
        # Declaration Section
        story.append(Paragraph("DECLARATION", self.styles['SectionHeader']))
        declaration_text = """
        I hereby declare that the information provided above is true and correct to the best of my knowledge. 
        I understand that any false information may result in rejection of my claim.
        """
        story.append(Paragraph(declaration_text, self.styles['FieldValue']))
        story.append(Spacer(1, 20))
        
        # Signature Section
        signature_data = [
            ['Signature of Insured:', '_________________________', 'Date:', '_________________________'],
            ['', '', '', ''],
            ['Name:', form_data.get('patient_name', 'N/A'), 'Policy No:', form_data.get('policy_number', 'N/A')]
        ]
        
        signature_table = Table(signature_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1.5*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(signature_table)
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def generate_pdf_from_template(self, form_data: Dict[str, Any], template_url: str, output_path: str) -> str:
        """Generate PDF using a template from URL (like the Star Health form)."""
        try:
            # Check if it's the Star Health template
            if "d28c6jni2fmamz.cloudfront.net" in template_url and "CLAIMFORM_89ec9742bd.pdf" in template_url:
                return self.generate_star_health_claim_pdf(form_data, output_path)
            else:
                # For other templates, generate a synthetic form
                return self.generate_synthetic_claim_pdf(form_data, output_path)
        except Exception as e:
            print(f"Error generating PDF from template: {e}")
            # Fallback to synthetic form
            return self.generate_synthetic_claim_pdf(form_data, output_path)

# Global PDF generator instance
pdf_generator = PDFGenerator()
