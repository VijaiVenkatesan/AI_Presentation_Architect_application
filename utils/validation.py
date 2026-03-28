"""Slide validation"""
import logging

logger = logging.getLogger(__name__)


class SlideValidator:

    @staticmethod
    def validate_slides(slides):
        errors = []
        warnings = []

        for s in slides:
            if not isinstance(s, dict):
                errors.append(f"Slide: not a dictionary")
                continue

            sn = s.get('slide_number', '?')
            content = s.get('content', {})

            if not isinstance(content, dict):
                content = {}

            layout = s.get('layout', 'content')

            if layout == 'chart' and not content.get('chart'):
                warnings.append(f"Slide {sn}: chart layout but no chart data")
            if layout == 'table' and not content.get('table'):
                warnings.append(f"Slide {sn}: table layout but no table data")
            if layout == 'metrics' and not content.get('key_metrics'):
                warnings.append(f"Slide {sn}: metrics layout but no metrics")
            if layout == 'image' and not content.get('image'):
                warnings.append(f"Slide {sn}: image layout but no image")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_slides': len(slides)
        }
