"""
Adapter for the Adafruit PioMatter library for Raspberry Pi 5.
This provides compatibility with the mlb-led-scoreboard using the new Pi 5 driver.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from driver.base import MatrixDriverBase, GraphicsBase


class PioMatterMatrixAdapter(MatrixDriverBase):
    """Adapter for the Adafruit PioMatter library (Raspberry Pi 5)."""

    def __init__(self, options):
        """Initialize using the PioMatter library."""
        import adafruit_blinka_raspberry_pi5_piomatter as piomatter

        # Extract dimensions from options
        width = options.cols * options.chain_length
        height = options.rows * options.parallel

        # Determine number of address lines based on panel rows
        # 64x32 panels typically use 1/16 scan = 4 address lines
        # 64x64 panels typically use 1/32 scan = 5 address lines
        panel_rows = options.rows  # Single panel height
        n_addr_lines = {
            16: 4,   # 1/16 scan
            32: 4,   # 1/16 scan (most common for 64x32 panels)
            64: 5    # 1/32 scan
        }.get(panel_rows, 4)  # Default to 4 address lines

        # Create geometry - PioMatter expects dimensions of a SINGLE panel
        # The library handles chaining and parallel internally
        self._geometry = piomatter.Geometry(
            width=options.cols,  # Single panel width
            height=panel_rows,    # Single panel height
            n_addr_lines=n_addr_lines,
            rotation=piomatter.Orientation.Normal
        )

        # Create PIL canvas
        self._canvas = Image.new('RGB', (width, height), (0, 0, 0))
        self._draw = ImageDraw.Draw(self._canvas)

        # Create framebuffer
        self._framebuffer = np.asarray(self._canvas).copy()

        # Initialize PioMatter with single panel geometry
        self._matrix = piomatter.PioMatter(
            colorspace=piomatter.Colorspace.RGB888Packed,
            pinout=piomatter.Pinout.AdafruitMatrixBonnet,
            framebuffer=self._framebuffer,
            geometry=self._geometry,
            chain=options.chain_length,
            parallel=options.parallel
        )

        self._width = width
        self._height = height
        self._double_buffer = None

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def CreateFrameCanvas(self):
        """Create a double-buffer canvas."""
        if self._double_buffer is None:
            self._double_buffer = PioMatterCanvas(self._width, self._height)
        return self._double_buffer

    def SwapOnVSync(self, canvas):
        """Swap buffers and update the display."""
        if isinstance(canvas, PioMatterCanvas):
            # Copy canvas content to framebuffer
            self._framebuffer[:] = np.asarray(canvas._image)
            # Update the display
            self._matrix.show()
        return canvas

    def SetImage(self, image, offset_x=0, offset_y=0):
        """Display an image on the matrix."""
        # Paste image onto canvas
        self._canvas.paste(image, (offset_x, offset_y))
        # Update framebuffer
        self._framebuffer[:] = np.asarray(self._canvas)
        # Show on display
        self._matrix.show()

    def Clear(self):
        """Clear the display."""
        self._canvas.paste(Image.new('RGB', (self._width, self._height), (0, 0, 0)))
        self._framebuffer[:] = np.asarray(self._canvas)
        self._matrix.show()


class PioMatterCanvas:
    """
    Canvas object that mimics the hzeller canvas interface but uses PIL.
    """

    def __init__(self, width, height):
        self._image = Image.new('RGB', (width, height), (0, 0, 0))
        self._draw = ImageDraw.Draw(self._image)
        self.width = width
        self.height = height

    def Clear(self):
        """Clear the canvas."""
        self._image.paste(Image.new('RGB', (self.width, self.height), (0, 0, 0)))

    def SetPixel(self, x, y, r, g, b):
        """Set a single pixel."""
        self._draw.point((x, y), fill=(r, g, b))


class PioMatterColor:
    """Color object for PioMatter that mimics hzeller Color."""

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def to_tuple(self):
        return (self.r, self.g, self.b)


class PioMatterFont:
    """Font object for PioMatter that mimics hzeller Font."""

    def __init__(self):
        self._font = None
        self._font_path = None

    def LoadFont(self, path):
        """Load a BDF font. Convert to PIL font."""
        # Store the path for reference
        self._font_path = path

        # Try to find a similar TrueType font
        # For now, use a default PIL font
        # Users may need to install specific fonts
        try:
            # Try to load as BDF (PIL supports BDF)
            from PIL import ImageFont
            self._font = ImageFont.load(path)
        except Exception:
            # Fall back to default font
            try:
                # Try DejaVu Sans Mono which is commonly available
                self._font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
            except Exception:
                # Ultimate fallback to default
                self._font = ImageFont.load_default()

        return True

    def CharacterWidth(self, char):
        """Get character width."""
        if self._font:
            bbox = self._font.getbbox(char)
            return bbox[2] - bbox[0]
        return 6  # Default fallback


class PioMatterGraphicsAdapter(GraphicsBase):
    """Graphics adapter for PioMatter using PIL drawing."""

    def __init__(self):
        pass

    def DrawText(self, canvas, font, x, y, color, text):
        """Draw text using PIL."""
        if isinstance(canvas, PioMatterCanvas):
            pil_color = color.to_tuple() if isinstance(color, PioMatterColor) else color
            # Note: PIL text baseline is different from hzeller, may need adjustment
            canvas._draw.text((x, y - 10), text, fill=pil_color, font=font._font if hasattr(font, '_font') else None)
            return len(text) * 6  # Approximate width

    def DrawLine(self, canvas, x1, y1, x2, y2, color):
        """Draw a line using PIL."""
        if isinstance(canvas, PioMatterCanvas):
            pil_color = color.to_tuple() if isinstance(color, PioMatterColor) else color
            canvas._draw.line([(x1, y1), (x2, y2)], fill=pil_color, width=1)

    def Color(self, r, g, b):
        """Create a color object."""
        return PioMatterColor(r, g, b)

    def Font(self):
        """Create a font object."""
        return PioMatterFont()
