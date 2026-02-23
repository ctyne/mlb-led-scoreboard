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

        # Create geometry - use total display dimensions
        # For a single 64x32 panel: width=64, height=32
        # PioMatter's geometry describes the overall display configuration
        print(f"DEBUG: Creating geometry - width={width}, height={height}, n_addr_lines={n_addr_lines}")
        self._geometry = piomatter.Geometry(
            width=width,  # Total width (cols * chain)
            height=height,  # Total height (rows * parallel)
            n_addr_lines=n_addr_lines,
            rotation=piomatter.Orientation.Normal
        )
        print("DEBUG: Geometry created successfully")

        # Create PIL canvas
        print("DEBUG: Creating PIL canvas")
        self._canvas = Image.new('RGB', (width, height), (0, 0, 0))
        self._draw = ImageDraw.Draw(self._canvas)

        # Create framebuffer
        print("DEBUG: Creating framebuffer")
        self._framebuffer = np.asarray(self._canvas).copy()

        # Initialize PioMatter (chain/parallel handled by geometry)
        print("DEBUG: Initializing PioMatter display")
        self._matrix = piomatter.PioMatter(
            colorspace=piomatter.Colorspace.RGB888Packed,
            pinout=piomatter.Pinout.AdafruitMatrixBonnet,
            framebuffer=self._framebuffer,
            geometry=self._geometry
        )
        print("DEBUG: PioMatter display initialized successfully")

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
        print("DEBUG: SwapOnVSync called")
        if isinstance(canvas, PioMatterCanvas):
            try:
                # Copy canvas content to framebuffer
                print("DEBUG: Copying canvas to framebuffer")
                self._framebuffer[:] = np.asarray(canvas._image)
                # Update the display
                print("DEBUG: Calling matrix.show()")
                self._matrix.show()
                print("DEBUG: matrix.show() completed")
            except Exception as e:
                print(f"ERROR in SwapOnVSync: {e}")
                import traceback
                traceback.print_exc()
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

    def Fill(self, r, g, b):
        """Fill the entire canvas with a color."""
        print(f"DEBUG: Fill called with RGB({r}, {g}, {b})")
        self._image.paste(Image.new('RGB', (self.width, self.height), (r, g, b)))

    def SetPixel(self, x, y, r, g, b):
        """Set a single pixel."""
        self._draw.point((x, y), fill=(r, g, b))


class PioMatterColor:
    """Color object for PioMatter that mimics hzeller Color."""

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        # Aliases for compatibility
        self.red = r
        self.green = g
        self.blue = b

    def to_tuple(self):
        return (self.r, self.g, self.b)


class PioMatterFont:
    """Font object for PioMatter that mimics hzeller Font."""

    def __init__(self):
        self._font = None
        self._font_path = None

    def LoadFont(self, path):
        """Load a BDF font. Convert to PIL font."""
        print(f"DEBUG: LoadFont called with path={path}")
        # Store the path for reference
        self._font_path = path

        # Try to find a similar TrueType font
        # For now, use a default PIL font
        # Users may need to install specific fonts
        try:
            # Try to load as BDF (PIL supports BDF)
            from PIL import ImageFont
            print(f"DEBUG: Attempting to load BDF font: {path}")
            self._font = ImageFont.load(path)
            print(f"DEBUG: BDF font loaded successfully")
        except Exception as e:
            print(f"DEBUG: BDF load failed ({e}), trying TrueType fallback")
            # Fall back to default font
            try:
                # Try DejaVu Sans Mono which is commonly available
                self._font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
                print(f"DEBUG: Using DejaVu Sans Mono fallback")
            except Exception as e2:
                print(f"DEBUG: TrueType fallback failed ({e2}), using default font")
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
        print(f"DEBUG: DrawText called - text='{text}', x={x}, y={y}")
        if isinstance(canvas, PioMatterCanvas):
            try:
                pil_color = color.to_tuple() if isinstance(color, PioMatterColor) else color
                print(f"DEBUG: Drawing text with color={pil_color}, font={font._font if hasattr(font, '_font') else None}")
                # Note: PIL text baseline is different from hzeller, may need adjustment
                canvas._draw.text((x, y - 10), text, fill=pil_color, font=font._font if hasattr(font, '_font') else None)
                print(f"DEBUG: Text drawn successfully")
                return len(text) * 6  # Approximate width
            except Exception as e:
                print(f"ERROR in DrawText: {e}")
                import traceback
                traceback.print_exc()
                return 0

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
