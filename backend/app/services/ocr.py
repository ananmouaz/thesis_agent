from PIL import Image
from pix2tex.cli import LatexOCR
import sys


def image_to_latex(file_path: str) -> str:
    """Convert an image file to LaTeX code using pix2tex. """
    img = Image.open(file_path)
    model = LatexOCR()
    return model(img)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ocr.py <image_file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
    latex_code = image_to_latex(file_path)
    print(latex_code)
