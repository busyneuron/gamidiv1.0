import pygame
import os
import colorsys

class Grid:
    def __init__(self, size=736, divisions=16):
        self.size = size
        self.divisions = divisions
        self.cell_size = size // divisions # 46 pixels

    def get_rect(self, col, row, w_cells, h_cells):
        """Returns a pygame.Rect based on grid coordinates."""
        return pygame.Rect(
            int(col * self.cell_size),
            int(row * self.cell_size),
            int(w_cells * self.cell_size),
            int(h_cells * self.cell_size)
        )

class Theme:
    def __init__(self):
        
        # Base Colors
        self.bg = (255, 255, 255)
        self.accent = (95, 193, 201) 
        self.complementary = (201, 139, 95) 
        self.bright = (207, 244, 255) 
        self.secondary = (155, 75, 52) 
        self.dark = (95, 112, 97)
        self.neutral = (61,73,74)

        #to get a triad
        self.color2 = (201,95,156)
        self.color3 = (201,188,95)

        self.plate_bg = (25, 25, 30, 180) # Semi-transparent
        
        # UI Element Colors (Using your concept colors)
        self.color_kb = (255, 255, 0, 120)        # Yellow lot
        self.color_voice = (30, 60, 60, 180)      # Teal/Cyan
        self.color_faders = (60, 30, 30, 180)     # Reddish
        self.color_fifths = (20, 20, 30, 150)     # Dark Blue
        self.color_console = (123, 100, 15, 200)  # Brown/Gold

        self.fonts = FontManager()

    @staticmethod
    def _rgb_to_hsl(rgb):
        r, g, b = [x / 255.0 for x in rgb]
        h, l, s = colorsys.rgb_to_hls(r, g, b)   # returns (h, l, s)
        return (h * 360, s, l)   # convert h to degrees, s and l remain 0..1

    @staticmethod
    def _hsl_to_rgb(hsl):
        h, s, l = hsl
        h = h / 360.0
        r, g, b = colorsys.hls_to_rgb(h, l, s)   # expects (h, l, s)
        return tuple(int(round(c * 255)) for c in (r, g, b))

    def hue_shift(self, degrees):
        """Return a new Theme instance with all colors hue‑shifted by the given degrees."""
        new_theme = Theme()
        for attr in dir(self):
            if attr.startswith('_'):
                continue
            val = getattr(self, attr)
            if isinstance(val, tuple) and len(val) == 3 and all(isinstance(v, int) for v in val):
                # This is likely an RGB color
                h, s, l = self._rgb_to_hsl(val)
                h = (h + degrees) % 360
                new_val = self._hsl_to_rgb((h, s, l))
                setattr(new_theme, attr, new_val)
            else:
                # Copy non‑color attributes as is
                setattr(new_theme, attr, val)
        return new_theme


class FontManager:
    def __init__(self, fonts_folder="fonts"):
        self.fonts_folder = fonts_folder
        self.cache = {}  # (path, size) -> pygame.font.Font
        self.default_font = None
        self._load_default()

    def _load_default(self):
        # Fallback to system font if custom font not found
        self.default_font = pygame.font.SysFont("Arial", 12)

    def get_font(self, filename, size, bold=False, italic=False):
        """
        Load a font from the fonts folder.
        filename: e.g., "Roboto-Regular.ttf"
        size: font size in pixels
        bold, italic: if the font file doesn't have separate bold/italic variants,
                      you can use pygame's built-in styling (but it's better to load a specific file).
        For simplicity, we ignore bold/italic here and rely on the filename.
        """
        key = (filename, size)
        if key in self.cache:
            return self.cache[key]
        
        path = os.path.join(self.fonts_folder, filename)
        if os.path.exists(path):
            font = pygame.font.Font(path, size)
        else:
            # Fallback to system font with style
            font = pygame.font.SysFont("Arial", size, bold, italic)
        self.cache[key] = font
        return font

    def get_black(self, size):
        return self.get_font("NotoSerifDisplay-Black.ttf", size)

    def get_black_italic(self, size):
        return self.get_font("NotoSerifDisplay-BlackItalic.ttf", size)

    def get_bold(self, size):
        return self.get_font("NotoSerifDisplay-Bold.ttf", size)

    def get_light(self, size):
        return self.get_font("NotoSerifDisplay-Light.ttf", size)

    def get_regular(self, size):
        return self.get_font("NotoSerifDisplay-Regular.ttf", size)

    def get_thin(self, size):
        return self.get_font("NotoSerifDisplay-Thin.ttf", size)

    ## monos
    def get_mono_reg(self, size):
        return self.get_font("SpaceMono-Regular.ttf", size)
    
    def get_mono_bold(self, size):
        return self.get_font("SpaceMono-Bold.ttf", size)
    
    def get_mono_bold_italic(self, size):
        return self.get_font("SpaceMono-BoldItalic.ttf", size)
        
    def get_mono_italic(self, size):
        return self.get_font("SpaceMono-Italic.ttf", size)
    
    def get_music_notation(self, size):
        return self.get_font("NotoMusic-Regular.ttf", size)
    
    def get_symbol_font(self, size):
        return self.get_font("segoe-ui-symbol.ttf", size)