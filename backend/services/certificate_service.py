"""
Certificate Generation Service
Service for generating PDF certificates for completed formations
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import io

from config import settings

logger = logging.getLogger(__name__)

# Try to import PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab is not installed. Install with: pip install reportlab")

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class CertificateService:
    """Service for generating certificates"""
    
    def __init__(self):
        """Initialize certificate service"""
        if not REPORTLAB_AVAILABLE:
            logger.error("reportlab is required for certificate generation")
        
        self.media_root = Path(settings.MEDIA_ROOT)
        self.certificates_dir = self.media_root / "certificates"
        self.certificates_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_certificate(
        self,
        user_name: str,
        formation_title: str,
        completion_date: datetime,
        user_id: int,
        formation_id: int,
        score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate a PDF certificate
        
        Args:
            user_name: Name of the user
            formation_title: Title of the completed formation
            completion_date: Date of completion
            user_id: User ID
            formation_id: Formation ID
            score: Optional final exam score
            
        Returns:
            Dictionary with certificate_url and file_path
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for certificate generation")
        
        try:
            # Create certificate filename
            filename = f"certificate_{user_id}_{formation_id}_{int(completion_date.timestamp())}.pdf"
            file_path = self.certificates_dir / filename
            
            # Create PDF
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Container for the 'Flowable' objects
            story = []
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=1,  # Center
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=16,
                textColor=colors.HexColor('#333333'),
                spaceAfter=20,
                alignment=1,  # Center
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#555555'),
                spaceAfter=12,
                alignment=1,  # Center
            )
            
            # Add content
            story.append(Spacer(1, 0.5*inch))
            
            # Certificate title
            story.append(Paragraph("CERTIFICAT DE COMPLÉTION", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Certificate text
            cert_text = f"""
            Ce certificat atteste que
            """
            story.append(Paragraph(cert_text, body_style))
            story.append(Spacer(1, 0.2*inch))
            
            # User name (highlighted)
            name_style = ParagraphStyle(
                'NameStyle',
                parent=styles['Heading2'],
                fontSize=20,
                textColor=colors.HexColor('#0066cc'),
                spaceAfter=20,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(user_name, name_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Completion text
            completion_text = f"""
            a complété avec succès la formation
            """
            story.append(Paragraph(completion_text, body_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Formation title
            formation_style = ParagraphStyle(
                'FormationStyle',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=colors.HexColor('#333333'),
                spaceAfter=30,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(formation_title, formation_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Date and score
            date_str = completion_date.strftime("%d %B %Y")
            details_text = f"Date de complétion: {date_str}"
            
            if score is not None:
                details_text += f"<br/>Score à l'examen final: {score:.1f}%"
            
            story.append(Paragraph(details_text, body_style))
            story.append(Spacer(1, 0.5*inch))
            
            # Signature line
            signature_text = """
            <br/><br/>
            _________________________<br/>
            Signature
            """
            story.append(Paragraph(signature_text, body_style))
            
            # Build PDF
            doc.build(story)
            
            # Generate URL
            certificate_url = f"{settings.MEDIA_URL}certificates/{filename}"
            
            logger.info(f"Generated certificate: {file_path}")
            
            return {
                "certificate_url": certificate_url,
                "file_path": str(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error generating certificate: {e}")
            raise RuntimeError(f"Failed to generate certificate: {e}")


# Singleton instance
certificate_service = CertificateService()

