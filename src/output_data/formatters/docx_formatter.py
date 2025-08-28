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
    def improve_hebrew_punctuation(text: str) -> str:
        """Improve punctuation for Hebrew text"""
        if not text:
            return text
        
        import re
        
        # First, normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Hebrew punctuation improvements
        improvements = [
            # Fix spacing around Hebrew punctuation marks
            (r'([א-ת])\s*([,\.!?;:])', r'\1\2'),  # Remove space before punctuation
            (r'([,\.!?;:])\s*([א-ת])', r'\1 \2'),  # Add space after punctuation before Hebrew
            (r'([א-ת])\s*\.\s*([א-ת])', r'\1. \2'),  # Period between Hebrew words
            (r'([א-ת])\s*,\s*([א-ת])', r'\1, \2'),  # Comma between Hebrew words
            (r'([א-ת])\s*!\s*([א-ת])', r'\1! \2'),  # Exclamation between Hebrew words
            (r'([א-ת])\s*\?\s*([א-ת])', r'\1? \2'),  # Question mark between Hebrew words
            
            # Fix spacing around quotes
            (r'"([א-ת]+)"', r'"\1"'),
            (r"'([א-ת]+)'", r"'\1'"),
            
            # Fix spacing around numbers
            (r'([א-ת])\s*(\d+)', r'\1 \2'),
            (r'(\d+)\s*([א-ת])', r'\1 \2'),
            
            # Fix spacing around English letters
            (r'([א-ת])\s*([a-zA-Z])', r'\1 \2'),
            (r'([a-zA-Z])\s*([א-ת])', r'\1 \2'),
            
            # Fix common Hebrew text issues
            (r'([א-ת])\s*-\s*([א-ת])', r'\1-\2'),  # Hyphens in Hebrew words
            (r'([א-ת])\s*/\s*([א-ת])', r'\1/\2'),  # Slashes in Hebrew words
            
            # Clean up multiple spaces
            (r'\s+', ' '),
        ]
        
        for pattern, replacement in improvements:
            text = re.sub(pattern, replacement, text)
        
        return text.strip()
    
    @staticmethod
    def create_simple_document(
        full_text: str,
        audio_file: str,
        model: str,
        engine: str
    ) -> Optional[Document]:
        """Create a simple Word document with full text (no speaker segmentation)"""
        try:
            doc = Document()
            
            # Set document to RTL
            DocxFormatter._set_document_rtl(doc)
            
            # Add title
            title = doc.add_heading('דוח תמלול', 0)
            DocxFormatter._set_paragraph_rtl(title)
            
            # Add metadata table
            DocxFormatter._add_metadata_table(doc, audio_file, model, engine)
            
            # Add full text content
            DocxFormatter._add_full_text_content(doc, full_text)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error creating simple DOCX document: {e}")
            return None
    
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
            
            # Set bidirectional text
            bidi_elements = section._sectPr.xpath('./w:bidi')
            if bidi_elements:
                bidi_elements[0].val = '1'
            else:
                bidi = OxmlElement('w:bidi')
                bidi.set('val', '1')
                section._sectPr.append(bidi)
            
            # Set page margins for RTL
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)
            
            logger.info("Document RTL settings applied successfully")
        except Exception as e:
            logger.warning(f"Could not set RTL direction: {e}")
    
    @staticmethod
    def _set_paragraph_rtl(paragraph):
        """Set paragraph to RTL alignment"""
        try:
            # Set paragraph alignment to right
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
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
        
        # Set RTL for header cells
        for cell in header_cells:
            for paragraph in cell.paragraphs:
                DocxFormatter._set_paragraph_rtl(paragraph)
        
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
            
            # Set RTL for all cells
            for cell in row_cells:
                for paragraph in cell.paragraphs:
                    DocxFormatter._set_paragraph_rtl(paragraph)
    
    @staticmethod
    def _add_transcription_content(doc: Document, transcription_data: List[Dict[str, Any]]):
        """Add transcription content to document"""
        # Add heading with RTL
        heading = doc.add_heading('תמלול שיחה', level=1)
        DocxFormatter._set_paragraph_rtl(heading)
        
        # Validate input data
        if not transcription_data:
            para = doc.add_paragraph("אין נתוני תמלול זמינים")
            DocxFormatter._set_paragraph_rtl(para)
            return
        
        # Group segments by speaker for better conversation flow
        speakers_data = {}
        total_segments = 0
        total_words = 0
        
        for segment in transcription_data:
            if isinstance(segment, dict):
                speaker = segment.get('speaker', 'Unknown')
                text = segment.get('text', '').strip()
                
                # Only add segments with actual text content
                if text:
                    if speaker not in speakers_data:
                        speakers_data[speaker] = []
                    speakers_data[speaker].append(segment)
                    total_segments += 1
                    total_words += len(text.split())
        
        # Log content statistics
        logger.info(f"📄 DOCX Content Statistics:")
        logger.info(f"   - Total segments: {total_segments}")
        logger.info(f"   - Total words: {total_words}")
        logger.info(f"   - Speakers: {list(speakers_data.keys())}")
        
        if not speakers_data:
            para = doc.add_paragraph("אין תוכן תמלול זמין")
            DocxFormatter._set_paragraph_rtl(para)
            return
        
        # Add content by speaker
        for speaker_name, segments in speakers_data.items():
            # Add speaker header
            speaker_heading = doc.add_heading(f'🎤 {speaker_name}', level=2)
            DocxFormatter._set_paragraph_rtl(speaker_heading)
            
            # Sort segments by start time for chronological order
            segments.sort(key=lambda x: x.get('start', 0))
            
            # Add segments for this speaker
            speaker_words = 0
            for segment in segments:
                text = segment.get('text', '').strip()
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
                    
                    # Add text content
                    text_run = para.add_run(text)
                    text_run.font.size = Pt(12)
                    
                    speaker_words += len(text.split())
            
            # Log speaker statistics
            logger.info(f"   - {speaker_name}: {len(segments)} segments, {speaker_words} words")
            
            # Add spacing between speakers
            doc.add_paragraph()
        
        # Add summary at the end
        summary_heading = doc.add_heading('סיכום', level=2)
        DocxFormatter._set_paragraph_rtl(summary_heading)
        
        summary_para = doc.add_paragraph()
        DocxFormatter._set_paragraph_rtl(summary_para)
        summary_para.add_run(f"סה״כ קטעים: {total_segments}, סה״כ מילים: {total_words}")
    
    @staticmethod
    def _add_full_text_content(doc: Document, full_text: str):
        """Add full text content to document (no speaker segmentation)"""
        # Add heading with RTL
        heading = doc.add_heading('תמלול מלא', level=1)
        DocxFormatter._set_paragraph_rtl(heading)
        
        # Validate input text
        if not full_text or not full_text.strip():
            para = doc.add_paragraph("אין תוכן תמלול זמין")
            DocxFormatter._set_paragraph_rtl(para)
            return
        
        # Clean and improve the text
        cleaned_text = DocxFormatter.improve_hebrew_punctuation(full_text.strip())
        
        # Split text into paragraphs (split by double newlines or long sentences)
        paragraphs = []
        if '\n\n' in cleaned_text:
            paragraphs = cleaned_text.split('\n\n')
        else:
            # Split by sentences (roughly)
            sentences = cleaned_text.split('. ')
            paragraphs = [s.strip() + '.' for s in sentences if s.strip()]
        
        # If no natural paragraphs, create one
        if not paragraphs:
            paragraphs = [cleaned_text]
        
        # Add each paragraph to the document
        total_words = 0
        for paragraph_text in paragraphs:
            if paragraph_text.strip():
                para = doc.add_paragraph()
                DocxFormatter._set_paragraph_rtl(para)
                
                # Add text content
                text_run = para.add_run(paragraph_text.strip())
                text_run.font.size = Pt(12)
                
                total_words += len(paragraph_text.split())
        
        # Add summary
        summary_heading = doc.add_heading('סיכום', level=2)
        DocxFormatter._set_paragraph_rtl(summary_heading)
        
        summary_para = doc.add_paragraph()
        DocxFormatter._set_paragraph_rtl(summary_para)
        summary_para.add_run(f"סה״כ מילים: {total_words}")
        
        logger.info(f"📄 Simple DOCX Content Statistics:")
        logger.info(f"   - Total words: {total_words}")
        logger.info(f"   - Paragraphs: {len(paragraphs)}")
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds into MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}" 