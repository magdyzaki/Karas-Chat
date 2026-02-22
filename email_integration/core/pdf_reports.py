"""
نظام تقارير PDF المتقدمة
Advanced PDF Reports System
"""
import os
from datetime import datetime
from typing import Optional, List, Dict

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: reportlab not installed. PDF export will not be available.")

from .db import (
    get_connection,
    get_all_clients,
    get_client_by_id,
    get_client_messages
)


def export_client_report_to_pdf(client_id: int, file_path: str) -> bool:
    """
    تصدير تقرير عميل مفصل إلى PDF
    
    Args:
        client_id: معرف العميل
        file_path: مسار ملف PDF
    
    Returns:
        True في حالة النجاح، False في حالة الفشل
    """
    if not PDF_AVAILABLE:
        raise ImportError("reportlab is required for PDF export. Install it using: pip install reportlab")
    
    try:
        # الحصول على بيانات العميل
        client = get_client_by_id(client_id)
        if not client:
            return False
        
        (
            _id, company, country, contact, email,
            phone, website, date_added, status, score,
            classification, is_focus
        ) = client
        
        # إنشاء ملف PDF
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        
        # الأنماط
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#366092'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4ECDC4'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # العنوان
        story.append(Paragraph("Client Report", title_style))
        story.append(Paragraph(f"<b>Company:</b> {company}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # معلومات العميل
        story.append(Paragraph("Client Information", heading_style))
        client_data = [
            ['Field', 'Value'],
            ['Company Name', company or 'N/A'],
            ['Country', country or 'N/A'],
            ['Contact Person', contact or 'N/A'],
            ['Email', email or 'N/A'],
            ['Phone', phone or 'N/A'],
            ['Website', website or 'N/A'],
            ['Date Added', date_added or 'N/A'],
            ['Status', status or 'N/A'],
            ['Score', str(score) if score else '0'],
            ['Classification', classification or 'N/A'],
            ['Focus', 'Yes' if is_focus else 'No']
        ]
        
        client_table = Table(client_data, colWidths=[2*inch, 4*inch])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(client_table)
        story.append(Spacer(1, 0.3*inch))
        
        # الرسائل
        story.append(Paragraph("Messages", heading_style))
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT message_date, message_type, channel, client_response, score_effect
            FROM messages
            WHERE client_id = ?
            ORDER BY message_date DESC
            LIMIT 50
        """, (client_id,))
        messages = cur.fetchall()
        
        if messages:
            msg_data = [['Date', 'Type', 'Channel', 'Response', 'Score Effect']]
            for msg in messages:
                msg_data.append([
                    msg[0] or 'N/A',
                    msg[1] or 'N/A',
                    msg[2] or 'N/A',
                    (msg[3] or 'N/A')[:50] + '...' if msg[3] and len(msg[3]) > 50 else (msg[3] or 'N/A'),
                    str(msg[4]) if msg[4] else '0'
                ])
            
            msg_table = Table(msg_data, colWidths=[1*inch, 1*inch, 1*inch, 2*inch, 0.8*inch])
            msg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(msg_table)
        else:
            story.append(Paragraph("No messages found.", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # الطلبات
        story.append(Paragraph("Requests", heading_style))
        cur.execute("""
            SELECT request_type, status, reply_status, created_at
            FROM requests
            WHERE client_id = ?
            ORDER BY created_at DESC
        """, (client_id,))
        requests = cur.fetchall()
        conn.close()
        
        if requests:
            req_data = [['Type', 'Status', 'Reply Status', 'Created At']]
            for req in requests:
                req_data.append([
                    req[0] or 'N/A',
                    req[1] or 'N/A',
                    req[2] or 'N/A',
                    req[3] or 'N/A'
                ])
            
            req_table = Table(req_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            req_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFC000')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(req_table)
        else:
            story.append(Paragraph("No requests found.", styles['Normal']))
        
        # تاريخ التقرير
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"<i>Report generated on: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)
        ))
        
        # بناء PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return False


def export_full_report_to_pdf(file_path: str) -> bool:
    """
    تصدير تقرير شامل إلى PDF
    
    Args:
        file_path: مسار ملف PDF
    
    Returns:
        True في حالة النجاح، False في حالة الفشل
    """
    if not PDF_AVAILABLE:
        raise ImportError("reportlab is required for PDF export. Install it using: pip install reportlab")
    
    try:
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#366092'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # العنوان
        story.append(Paragraph("Complete Export Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # إحصائيات
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM clients")
        total_clients = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM messages")
        total_messages = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM requests")
        total_requests = cur.fetchone()[0]
        
        stats_data = [
            ['Metric', 'Count'],
            ['Total Clients', str(total_clients)],
            ['Total Messages', str(total_messages)],
            ['Total Requests', str(total_requests)]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.5*inch))
        
        # قائمة العملاء (ملخص)
        story.append(Paragraph("Clients Summary", styles['Heading2']))
        cur.execute("""
            SELECT company_name, country, status, seriousness_score, classification
            FROM clients
            ORDER BY seriousness_score DESC
            LIMIT 50
        """)
        clients = cur.fetchall()
        conn.close()
        
        if clients:
            client_data = [['Company', 'Country', 'Status', 'Score', 'Classification']]
            for client in clients:
                client_data.append([
                    client[0] or 'N/A',
                    client[1] or 'N/A',
                    client[2] or 'N/A',
                    str(client[3]) if client[3] else '0',
                    client[4] or 'N/A'
                ])
            
            client_table = Table(client_data, colWidths=[2*inch, 1*inch, 1*inch, 0.8*inch, 1.2*inch])
            client_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(client_table)
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"<i>Report generated on: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)
        ))
        
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error generating full PDF report: {e}")
        return False
