#!/usr/bin/env python3
"""
DOCX Formatter
Handles Word document formatting and RTL support
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path  
from datetime import datetime  

from docx import Document  
from docx.shared import Inches, Pt, RGBColor 
from docx.enum.text import WD_ALIGN_PARAGRAPH  
from docx.oxml import OxmlElement

logger = logging.getLogger(__name__)

class DocxFormatter:
    """DOCX formatting utilities with RTL support"""
    
    @staticmethod
    def create_transcription_document(
        transcription_data: List[Dict[str, Any]],
        audio_file: str,
        model: str,
        engine: str
    ) -> Optional[Document]:
        """Create a Word document with transcription data"""
        try:
            doc = Document()
            
            # Set document to RTL
            DocxFormatter._set_document_rtl(doc)
            
            # Add title
            title = doc.add_heading('דוח תמלול', 0)
            DocxFormatter._set_paragraph_rtl(title)
            
            # Add metadata table
            DocxFormatter._add_metadata_table(doc, audio_file, model, engine)
            
            # Add transcription content
            DocxFormatter._add_transcription_content(doc, transcription_data)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error creating DOCX document: {e}")
            return None
    
    @staticmethod
    def _set_document_rtl(doc: Document):
        """Set document to RTL direction"""
        try:
            section = doc.sections[0]
            bidi_elements = section._sectPr.xpath('./w:bidi')
            if bidi_elements:
                bidi_elements[0].val = '1'
            else:
                bidi = OxmlElement('w:bidi')
                bidi.set('val', '1')
                section._sectPr.append(bidi)
            
            # Add text flow
            textFlow = OxmlElement('w:textFlow')
            textFlow.set('val', 'rl-tb')
            section._sectPr.append(textFlow)
        except Exception as e:
            logger.warning(f"Could not set RTL direction: {e}")
    
    @staticmethod
    def _set_paragraph_rtl(paragraph):
        """Set paragraph to RTL alignment"""
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        try:
            bidi = OxmlElement('w:bidi')
            bidi.set('val', '1')
            paragraph._element.get_or_add_pPr().append(bidi)
        except Exception as e:
            logger.warning(f"Could not set paragraph RTL: {e}")
    
    @staticmethod
    def _add_metadata_table(doc: Document, audio_file: str, model: str, engine: str):
        """Add metadata table to document"""
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        # Add headers
        header_cells = table.rows[0].cells
        header_cells[0].text = 'מטא-דאטה'
        header_cells[1].text = 'ערך'
        
        # Add data rows
        data = [
            ('קובץ שמע', Path(audio_file).name),
            ('מודל', model),
            ('מנוע', engine),
            ('תאריך', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ]
        
        for key, value in data:
            row_cells = table.add_row().cells
            row_cells[0].text = key
            row_cells[1].text = str(value)
            
            # Set RTL for cells
            for cell in row_cells:
                for paragraph in cell.paragraphs:
                    DocxFormatter._set_paragraph_rtl(paragraph)
    
    @staticmethod
    def _add_transcription_content(doc: Document, transcription_data: List[Dict[str, Any]]):
        """Add transcription content to document"""
        doc.add_heading('תמלול שיחה', level=1)
        
        for segment in transcription_data:
            if isinstance(segment, dict):
                text = segment.get('text', '')
                speaker = segment.get('speaker', 'Unknown')
                start_time = segment.get('start', 0)
                
                if text:
                    # Create paragraph with RTL alignment
                    para = doc.add_paragraph()
                    DocxFormatter._set_paragraph_rtl(para)
                    
                    # Add timestamp
                    timestamp = DocxFormatter._format_timestamp(start_time)
                    timestamp_run = para.add_run(f"{timestamp} ")
                    timestamp_run.font.size = Pt(8)
                    timestamp_run.font.color.rgb = RGBColor(128, 128, 128)
                    
                    # Add speaker name
                    speaker_run = para.add_run(f"{speaker}: ")
                    speaker_run.bold = True
                    speaker_run.font.size = Pt(12)
                    
                    # Add text content
                    text_run = para.add_run(text)
                    text_run.font.size = Pt(12)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds into MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}" 