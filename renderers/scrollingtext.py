from driver import graphics

from utils import center_text_position


def render_text(canvas, x, y, width, font, text_color, bg_color, text, scroll_pos, center=True):
    if __text_should_scroll(text, font, width):

        w = font["size"]["width"]
        total_width = w * len(text)

        # Simply draw the text at the scroll position
        # TODO: Optimize by trimming offscreen characters
        graphics.DrawText(canvas, font["font"], scroll_pos, y, text_color, text)

        # draw one-letter boxes to left and right to hide previous and next letters
        top = y + 1
        bottom = top - font["size"]["height"]
        for xi in range(0, w):
            left = x - xi - 1
            graphics.DrawLine(canvas, left, top, left, bottom, bg_color)
            right = x + width + xi
            graphics.DrawLine(canvas, right, top, right, bottom, bg_color)

        return total_width
    else:
        draw_x = __center_position(text, font, width, x) if center else x
        graphics.DrawText(canvas, font["font"], draw_x, y, text_color, text)
        return 0


# Maybe the text is too short and we should just center it instead?
def __text_should_scroll(text, font, width):
    return len(text) * font["size"]["width"] > width


def __center_position(text, font, width, x):
    return center_text_position(text, abs(width // 2) + x, font["size"]["width"])
