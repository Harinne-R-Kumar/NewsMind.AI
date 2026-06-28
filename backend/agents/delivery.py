"""
NewsMind AI - Delivery Agent
Generates PDF and sends email.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
from backend.config import settings
from backend.graph.state import NewspaperState, Article
from backend.utils.logging import setup_logger
from backend.database.connection import async_session
from backend.models.models import GeneratedReport
from datetime import datetime

logger = setup_logger("delivery")


class DeliveryAgent:
    """Handles PDF generation and email delivery."""
    
    def __init__(self):
        self.pdf_dir = "generated_pdfs"
        os.makedirs(self.pdf_dir, exist_ok=True)
    
    def generate_pdf(self, state: NewspaperState, articles: list) -> str:
        """Generate PDF from articles."""
        user_name = state.get("user_name", "Reader")
        date_str = state.get("started_at", "")[:10]
        run_id = state.get("run_id", "unknown")
        
        pdf_path = os.path.join(self.pdf_dir, f"newspaper_{run_id}.pdf")
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=30,
            textColor=HexColor('#0ea0ea'),
            alignment=1  # Center
        )
        
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=HexColor('#666666'),
            alignment=1,
            spaceAfter=20
        )
        
        greeting_style = ParagraphStyle(
            'Greeting',
            parent=styles['Normal'],
            fontSize=14,
            textColor=HexColor('#0ea0ea'),
            spaceAfter=30,
            alignment=1
        )
        
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#0ea0ea'),
            spaceBefore=20,
            spaceAfter=10,
            borderPadding=5,
        )
        
        article_title_style = ParagraphStyle(
            'ArticleTitle',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=HexColor('#1a1a2e'),
            spaceBefore=10,
            spaceAfter=5
        )
        
        article_body_style = ParagraphStyle(
            'ArticleBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#444444'),
            spaceAfter=15,
            leading=14
        )
        metadata_style = ParagraphStyle(
            "Metadata",
            parent=styles["Normal"],
            fontSize=8,
            textColor=HexColor("#666666"),
            spaceAfter=3,
            leading=10
        )
        story = []
        
        # Header
        story.append(Paragraph("📰 NewsMind AI", title_style))
        story.append(Paragraph(date_str, date_style))
        story.append(Paragraph(f"Good morning, {user_name}!", greeting_style))
        story.append(Spacer(1, 20))
        
        # Organize by section
        sections = {}
        for article in articles:
            section = article.get("section", "General")
            if section not in sections:
                sections[section] = []
            sections[section].append(article)
        
        # Add articles
        for section_name, section_articles in sections.items():

            story.append(Paragraph(section_name, section_style))

            for article in section_articles[:5]:

                title = article.get("title", "Untitled")
                summary = article.get("summary", "")

                source = article.get("source", "Unknown")
                url = article.get("url", "")
                published = article.get("published_at", "")

                # Escape special characters
                title = (
                    title.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                )

                summary = (
                    summary.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                )

                url = (
                    url.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )

                # Article title
                story.append(
                    Paragraph(title, article_title_style)
                )

                # Published time
                if published:
                    story.append(
                        Paragraph(
                            f"<b>🕒 Published:</b> {published}",
                            metadata_style,
                        )
                    )

                # Source
                story.append(
                    Paragraph(
                        f"<b>📰 Source:</b> {source}",
                        metadata_style,
                    )
                )

                # Original link
                if url:
                    story.append(
                    Paragraph(
                        f'<b>🔗 <link href="{url}">Read Original Article</link></b>',
                        metadata_style,
                    )
                )

                # Summary
                if summary:
                    story.append(
                        Paragraph(summary[:350], article_body_style)
                    )

                # Divider between articles
                story.append(Spacer(1, 8))

            story.append(Spacer(1, 15))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#888888'),
            alignment=1
        )
        story.append(Paragraph("Generated by NewsMind AI • Your Personal Intelligence Agent", footer_style))
        
        doc.build(story)
        logger.info(f"Generated PDF: {pdf_path}")
        
        return pdf_path
    
    def generate_email_html(self, state: NewspaperState) -> str:
        """Generate HTML email content."""
        return state.get("html_content", "<p>No content available</p>")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        pdf_path: Optional[str] = None
    ) -> bool:
        """Send email with optional PDF attachment."""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # HTML body
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)
            
            # PDF attachment
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(pdf_path)
                    )
                    msg.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def deliver(self, state: NewspaperState) -> NewspaperState:
        """Main delivery method called by LangGraph."""
        logger.info(f"Delivery agent processing for user {state['user_id']}")
        
        articles = state.get("articles", [])
        user_email = state.get("user_email", "")
        user_name = state.get("user_name", "Reader")
        
        # Generate PDF
        pdf_path = self.generate_pdf(state, articles)

        html_content = ""

        # -----------------------------------
        # SAVE REPORT BEFORE SENDING EMAIL
        # -----------------------------------

        async with async_session() as db:

            report = GeneratedReport(
                user_id=state["user_id"],
                html_content="",
                pdf_path=pdf_path,
                generated_at=datetime.utcnow()
            )

            db.add(report)

            await db.commit()

            await db.refresh(report)

        # Store report_id in workflow state
        state["report_id"] = report.id

        # -----------------------------------
        # Regenerate HTML so feedback links
        # contain the report_id
        # -----------------------------------

        from backend.agents.editorial import EditorialAgent

        editor = EditorialAgent()

        html_content = await editor.generate_html(
            state,
            articles
        )
        async with async_session() as db:

            report = await db.get(GeneratedReport, state["report_id"])

            report.html_content = html_content

            await db.commit()

        email_sent = False
        if user_email and settings.SMTP_USER != "dummy@gmail.com":
            date_str = state.get("started_at", "")[:10]
            subject = f"📰 Your NewsMind AI Daily Brief - {date_str}"
            email_sent = await self.send_email(user_email, subject, html_content, pdf_path)
        else:
            logger.info("Email delivery skipped - SMTP not configured")
        
        
        logger.info(f"Delivery complete: PDF={pdf_path}, Email={email_sent}")

        return {
            **state,
            "report_id": state["report_id"],     # <-- Add this line
            "pdf_path": pdf_path,
            "email_sent": email_sent,
            "current_step": "complete",
            "completed_at": datetime.utcnow().isoformat()
        }


# LangGraph node function
async def delivery_node(state: NewspaperState) -> NewspaperState:
    """LangGraph node for delivery agent."""
    agent = DeliveryAgent()
    return await agent.deliver(state)
