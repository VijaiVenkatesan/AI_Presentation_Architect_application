"""Slide validation and quality checks"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SlideValidator:
    """Validates slide data before generation/export"""
    
    REQUIRED_FIELDS = ['slide_number', 'layout', 'title', 'content']
    
    @staticmethod
    def validate_slides(slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate all slides and return validation report"""
        errors = []
        warnings = []
        
        for slide in slides:
            slide_num = slide.get('slide_number', 'Unknown')
            layout = slide.get('layout', 'content')
            
            # Check required fields
            for field in SlideValidator.REQUIRED_FIELDS:
                if field not in slide:
                    errors.append(f"Slide {slide_num}: Missing required field '{field}'")
            
            # Layout-specific validation
            content = slide.get('content', {})
            
            if layout == 'chart':
                if not content.get('chart'):
                    warnings.append(f"Slide {slide_num}: Chart layout but missing chart data")
                elif not content['chart'].get('data'):
                    errors.append(f"Slide {slide_num}: Chart missing required 'data' field")
            
            elif layout == 'table':
                table = content.get('table', {})
                if not table.get('headers') or not table.get('data'):
                    errors.append(f"Slide {slide_num}: Table missing 'headers' or 'data'")
            
            elif layout == 'metrics':
                if not content.get('key_metrics'):
                    warnings.append(f"Slide {slide_num}: Metrics layout but no metrics data")
            
            elif layout == 'image':
                if not content.get('image'):
                    warnings.append(f"Slide {slide_num}: Image layout but no image data")
            
            elif layout == 'two_column':
                if not content.get('left_column') and not content.get('right_column'):
                    warnings.append(f"Slide {slide_num}: Two-column layout but both columns empty")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_slides': len(slides)
        }
