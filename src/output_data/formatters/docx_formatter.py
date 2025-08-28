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
        """Set document to RTL direction with comprehensive Hebrew support"""
        try:
            section = doc.sections[0]
            
            # Set bidirectional text support
            bidi_elements = section._sectPr.xpath('./w:bidi')
            if bidi_elements:
                bidi_elements[0].val = '1'
            else:
                bidi = OxmlElement('w:bidi')
                bidi.set('val', '1')
                section._sectPr.append(bidi)
            
            # Set page margins for RTL (right margin smaller for Hebrew text)
            section.left_margin = Inches(0.5)   # Smaller left margin
            section.right_margin = Inches(1.5)  # Larger right margin for Hebrew text
            
            # Note: w:textDirection is not valid in section properties
            # RTL direction is handled at paragraph and text run levels
            
            logger.info("Document RTL settings applied successfully")
        except Exception as e:
            logger.warning(f"Could not set RTL direction: {e}")
    
    @staticmethod
    def _set_paragraph_rtl(paragraph):
        """Set paragraph to RTL alignment with Hebrew text support"""
        try:
            # Set paragraph alignment to right for RTL
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
            # Set paragraph direction to RTL
            try:
                paragraph._p.get_or_add_pPr().get_or_add_bidi()
                paragraph._p.pPr.bidi.val = '1'
            except Exception as e:
                logger.debug(f"Could not set paragraph RTL direction: {e}")
            
        except Exception as e:
            logger.warning(f"Could not set paragraph RTL: {e}")
    
    @staticmethod
    def _set_text_run_rtl(text_run):
        """Set text run to RTL direction for Hebrew text"""
        try:
            # Set text direction to RTL
            text_run._r.get_or_add_rPr().get_or_add_rtl()
            text_run._r.rPr.rtl.val = '1'
        except Exception as e:
            logger.debug(f"Could not set text run RTL: {e}")
    
    @staticmethod
    def _add_hebrew_text_with_rtl(paragraph, text: str):
        """Add Hebrew text with proper RTL formatting and punctuation at the end"""
        try:
            # Clean and improve Hebrew punctuation
            cleaned_text = DocxFormatter.improve_hebrew_punctuation(text)
            
            # Split text into parts (text and punctuation)
            import re
            
            # Find Hebrew text and punctuation
            hebrew_pattern = r'[א-ת\s]+'
            
            # Split the text into Hebrew and punctuation parts
            parts = []
            current_pos = 0
            
            while current_pos < len(cleaned_text):
                # Find next Hebrew text
                hebrew_match = re.search(hebrew_pattern, cleaned_text[current_pos:])
                if hebrew_match:
                    hebrew_start = current_pos + hebrew_match.start()
                    hebrew_end = current_pos + hebrew_match.end()
                    
                    # Add text before Hebrew (if any)
                    if hebrew_start > current_pos:
                        parts.append(('text', cleaned_text[current_pos:hebrew_start]))
                    
                    # Add Hebrew text
                    hebrew_text = cleaned_text[hebrew_start:hebrew_end].strip()
                    if hebrew_text:
                        parts.append(('hebrew', hebrew_text))
                    
                    current_pos = hebrew_end
                else:
                    # Add remaining text
                    if current_pos < len(cleaned_text):
                        parts.append(('text', cleaned_text[current_pos:]))
                    break
            
            # For RTL, we need to reverse the order of parts so punctuation appears at the end
            # This ensures proper Hebrew text flow
            rtl_parts = []
            hebrew_text_parts = []
            punctuation_parts = []
            
            for part_type, part_text in parts:
                if part_type == 'hebrew':
                    hebrew_text_parts.append(('hebrew', part_text))
                else:
                    punctuation_parts.append(('text', part_text))
            
            # Add Hebrew text first, then punctuation (for RTL flow)
            rtl_parts.extend(hebrew_text_parts)
            rtl_parts.extend(punctuation_parts)
            
            # Add parts to paragraph with proper RTL
            for part_type, part_text in rtl_parts:
                if part_text.strip():
                    if part_type == 'hebrew':
                        # Add Hebrew text with RTL
                        hebrew_run = paragraph.add_run(part_text)
                        hebrew_run.font.size = Pt(12)
                        DocxFormatter._set_text_run_rtl(hebrew_run)
                    else:
                        # Add punctuation/regular text
                        text_run = paragraph.add_run(part_text)
                        text_run.font.size = Pt(12)
            
        except Exception as e:
            logger.warning(f"Could not add Hebrew text with RTL: {e}")
            # Fallback to simple text addition
            text_run = paragraph.add_run(text)
            text_run.font.size = Pt(12)
    
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
                    DocxFormatter._add_hebrew_text_with_rtl(para, text)
                    
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
                DocxFormatter._add_hebrew_text_with_rtl(para, paragraph_text.strip())
                
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