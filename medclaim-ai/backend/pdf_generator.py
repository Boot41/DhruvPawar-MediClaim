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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import requests
from PIL import Image
import tempfile

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
    
    def generate_pdf_from_template(self, form_data: Dict[str, Any], template_url: str, output_path: str) -> str:
        """Generate PDF using a template from URL (like the Star Health form)."""
        try:
            # For now, we'll generate a synthetic form but mention it's based on the template
            # In a full implementation, you would parse the template PDF and fill it
            return self.generate_synthetic_claim_pdf(form_data, output_path)
        except Exception as e:
            print(f"Error generating PDF from template: {e}")
            # Fallback to synthetic form
            return self.generate_synthetic_claim_pdf(form_data, output_path)

# Global PDF generator instance
pdf_generator = PDFGenerator()
