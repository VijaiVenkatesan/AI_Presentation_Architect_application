
from pptx import Presentation
import os

path = r'D:\Antigravity_Projects\AI_Presentation_Architecture_App\assets\Datamatics-Presentation-Template-Light-Test.pptx'
prs = Presentation(path)
for i, layout in enumerate(prs.slide_layouts):
    print(f"Layout {i}: {layout.name}")
