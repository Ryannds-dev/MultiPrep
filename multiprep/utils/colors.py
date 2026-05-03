from __future__ import annotations

from colorsys import hls_to_rgb


def build_source_colors(count: int = 100) -> list[str]:
    colors: list[str] = []
    golden_ratio = 0.61803398875
    hue = 0.58
    for index in range(count):
        hue = (hue + golden_ratio) % 1.0
        lightness = 0.74 if index % 2 == 0 else 0.66
        saturation = 0.62 if index % 3 else 0.72
        red, green, blue = hls_to_rgb(hue, lightness, saturation)
        colors.append(f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}")
    return colors


SOURCE_COLORS = build_source_colors()
