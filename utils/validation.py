"""
Slide validation and quality checks
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SlideValidator:
    """Validates slide data before generation"""
    
    @staticmethod
    def validate_slides(slides_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate all slides and return validation report
        
        Returns:
            Dict with 'valid', 'errors', 'warnings' keys
        """
        errors = []
        warnings = []
        
        for slide in slides_data:
            slide_num = slide.get('slide_number', 'Unknown')
            layout = slide.get('layout', 'content')
            
            # Check required fields
            if 'layout' not in slide:
                errors.append(f"Slide {slide_num}: Missing 'layout' field")
            
            # Check content based on layout
            content = slide.get('content', {})
            
            if layout == 'chart' and not content.get('chart'):
                warnings.append(f"Slide {slide_num}: Chart layout but no chart data")
            
            if layout == 'table' and not content.get('table'):
                warnings.append(f"Slide {slide_num}: Table layout but no table data")
            
            if layout == 'image' and not content.get('image'):
                warnings.append(f"Slide {slide_num}: Image layout but no image data")
            
            if layout == 'metrics' and not content.get('key_metrics'):
                warnings.append(f"Slide {slide_num}: Metrics layout but no metrics data")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_slides': len(slides_data)
        }
