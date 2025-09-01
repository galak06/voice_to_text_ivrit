#!/usr/bin/env python3
"""
DOCX Formatter
Handles Word document formatting and RTL support
ONLY generates high-quality DOCX from processed text files
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
    """DOCX formatting utilities with RTL support - ONLY for high-quality text-based DOCX"""
    
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
            
            # Clean up multiple spaces (but preserve word spacing)
            (r'[ \t]+', ' '),
        ]
        
        for pattern, replacement in improvements:
            text = re.sub(pattern, replacement, text)
        
        return text.strip()
    
    @staticmethod
    def create_docx_from_word_ready_text(
        text_file_path: str,
        output_docx_path: str,
        audio_file: str = "merged_chunks",
        model: str = "merged",
        engine: str = "merged"
    ) -> bool:
        """
        Create a DOCX file from the Word-ready text file
        
        This method reads the clean, formatted text file and creates a properly
        formatted Word document that maintains all the spacing and formatting
        from the text file.
        
        This is the ONLY DOCX generation method - it produces high-quality output
        from processed, cleaned text rather than raw chunk data.
        """
        try:
            # Read the Word-ready text file
            with open(text_file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            if not text_content.strip():
                logger.error("Text file is empty or contains only whitespace")
                return False
            
            # Create the document
            doc = Document()
            
            # Set document to RTL for Hebrew text
            DocxFormatter._set_document_rtl(doc)
            
            # Add title
            title = doc.add_heading('🎤 TRANSCRIPTION - READY FOR WORD', 0)
            DocxFormatter._set_paragraph_rtl(title)
            
            # Add metadata table
            DocxFormatter._add_metadata_table(doc, audio_file, model, engine)
            
            # Add the formatted text content
            DocxFormatter._add_word_ready_text_content(doc, text_content)
            
            # Save the document
            doc.save(output_docx_path)
            logger.info(f"✅ DOCX created successfully from Word-ready text: {output_docx_path}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Text file not found: {text_file_path}")
            return False
        except Exception as e:
            logger.error(f"Error creating DOCX from Word-ready text: {e}")
            return False
    
    @staticmethod
    def _add_word_ready_text_content(doc: Document, text_content: str) -> None:
        """Add the Word-ready text content to the document with proper formatting"""
        try:
            # Split content into lines
            lines = text_content.split('\n')
            
            # Process each line
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this is a header line
                if line.startswith('🎤') or line.startswith('=') or line.startswith('Generated:') or line.startswith('Total Chunks:') or line.startswith('Duration:'):
                    # Add header as a formatted paragraph
                    if line.startswith('🎤'):
                        header = doc.add_heading(line, level=1)
                        DocxFormatter._set_paragraph_rtl(header)
                    elif line.startswith('='):
                        # Add separator line
                        sep = doc.add_paragraph(line)
                        sep.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        DocxFormatter._set_paragraph_rtl(sep)
                    else:
                        # Add metadata line
                        meta = doc.add_paragraph(line)
                        meta.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        DocxFormatter._set_paragraph_rtl(meta)
                
                # Check if this is a timestamp line
                elif line.startswith('[') and ']' in line:
                    # Add timestamp as a formatted paragraph
                    timestamp = doc.add_paragraph(line)
                    timestamp.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    # Make timestamp bold
                    for run in timestamp.runs:
                        run.bold = True
                        run.font.size = Pt(11)
                    DocxFormatter._set_paragraph_rtl(timestamp)
                
                # Check if this is the end section
                elif line.startswith('End of Transcription') or line.startswith('Copy this text'):
                    # Add end section
                    end = doc.add_paragraph(line)
                    end.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    DocxFormatter._set_paragraph_rtl(end)
                
                # This is regular text content
                else:
                    # Add regular text content
                    text_para = doc.add_paragraph(line)
                    text_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT  # Right-aligned for Hebrew
                    DocxFormatter._set_paragraph_rtl(text_para)
            
            logger.info(f"✅ Added {len(lines)} lines of Word-ready text content to document")
            
        except Exception as e:
            logger.error(f"Error adding Word-ready text content: {e}")
            raise
    
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
    def create_docx_from_text_content(text_content: str, output_docx_path: str, model: str = "unknown", engine: str = "unknown") -> bool:
        """Create a DOCX file directly from text content with speaker alignment"""
        try:
            if not text_content.strip():
                logger.error("Text content is empty or contains only whitespace")
                return False
            
            # Create the document
            doc = Document()
            
            # Set document to RTL for Hebrew text
            DocxFormatter._set_document_rtl(doc)
            
            # Add title
            title = doc.add_heading('תמלול עם זיהוי דוברים', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            DocxFormatter._set_paragraph_rtl(title)
            
            # Add metadata table
            DocxFormatter._add_metadata_table(doc, "audio_file", model, engine)
            
            # Add spacing
            doc.add_paragraph()
            
            # Split content into lines and add to document
            lines = text_content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    # Add empty paragraph for spacing
                    doc.add_paragraph()
                    continue
                
                # Check if this is a section header
                if line.startswith('===') and line.endswith('==='):
                    # Add section header
                    header = doc.add_heading(line.strip('= '), level=1)
                    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    DocxFormatter._set_paragraph_rtl(header)
                elif line.startswith('SPEAKER_') and ':' in line:
                    # This is a speaker line - format it specially
                    speaker_para = doc.add_paragraph()
                    speaker_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    DocxFormatter._set_paragraph_rtl(speaker_para)
                    
                    # Add speaker name in bold
                    speaker_name = line.split(':', 1)[0]
                    speaker_text = line.split(':', 1)[1] if ':' in line else ''
                    
                    speaker_run = speaker_para.add_run(f"{speaker_name}: ")
                    speaker_run.bold = True
                    speaker_run.font.size = Pt(12)
                    
                    # Add speaker text
                    text_run = speaker_para.add_run(speaker_text)
                    text_run.font.size = Pt(12)
                else:
                    # Regular text content
                    text_para = doc.add_paragraph(line)
                    text_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    DocxFormatter._set_paragraph_rtl(text_para)
            
            # Save the document
            doc.save(output_docx_path)
            
            logger.info(f"✅ DOCX created successfully from text content: {output_docx_path}")
            logger.info(f"   - Document contains {len(lines)} lines of content")
            return True
            
        except Exception as e:
            logger.error(f"Error creating DOCX from text content: {e}")
            return False
    
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