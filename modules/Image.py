from io import BytesIO
from typing import Final

import discord
import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont

from config import Config


class CardConfig:
    WIDTH: Final[int] = 1000
    HEIGHT: Final[int] = 320
    AVATAR_SIZE: Final[int] = 200
    AVATAR_POSITION: Final[tuple[int, int]] = (60, 60)
    AVATAR_DOWNLOAD_SIZE: Final[int] = 256
    TEXT_START_X: Final[int] = 300
    TEXT_MARGIN_RIGHT: Final[int] = 40
    TITLE_Y: Final[int] = 90
    SUBTITLE_Y: Final[int] = 170
    TITLE_FONT_SIZE: Final[int] = 100
    SUBTITLE_FONT_SIZE: Final[int] = 64
    MIN_FONT_SIZE: Final[int] = 10
    FONT_SIZE_STEP: Final[int] = 5
    BACKGROUND_COLOR: Final[str] = "#0f172a"
    OVERLAY_COLOR_JOIN: Final[tuple[int, int, int]] = (88, 101, 242)
    OVERLAY_COLOR_LEAVE: Final[tuple[int, int, int]] = (88, 101, 242)
    OVERLAY_ALPHA_JOIN: Final[int] = 255
    OVERLAY_ALPHA_LEAVE: Final[int] = 120
    TITLE_COLOR: Final[str] = "#f8fafc"
    SUBTITLE_COLOR: Final[str] = "#e2e8f0"
    FONT_REGULAR: Final[str] = "assets/font/Ubuntu-Regular.ttf"
    FONT_BOLD: Final[str] = "assets/font/Ubuntu-Bold.ttf"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_path = CardConfig.FONT_BOLD if bold else CardConfig.FONT_REGULAR
    try:
        return ImageFont.truetype(font_path, size=size)
    except (OSError, IOError):
        return ImageFont.load_default()


def _calculate_text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont
) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _fit_text_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    initial_size: int,
    bold: bool = False
) -> ImageFont.FreeTypeFont:
    size = initial_size
    while size > CardConfig.MIN_FONT_SIZE:
        font = _load_font(size, bold=bold)
        if _calculate_text_width(draw, text, font) <= max_width:
            return font
        size -= CardConfig.FONT_SIZE_STEP
    
    return _load_font(CardConfig.MIN_FONT_SIZE, bold=bold)


def _create_gradient_overlay(
    width: int,
    height: int,
    color: tuple[int, int, int],
    alpha: int
) -> PILImage.Image:
    overlay = PILImage.new("RGBA", (width, height), (*color, alpha))
    gradient = np.linspace(255, 0, width, dtype=np.uint8)
    gradient_array = np.tile(gradient, (height, 1))
    alpha_channel = PILImage.fromarray(gradient_array, mode='L')
    overlay.putalpha(alpha_channel)
    return overlay


def _create_circular_mask(size: int) -> PILImage.Image:
    mask = PILImage.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    return mask


async def _get_avatar_image(
    member: discord.Member,
    size: int
) -> PILImage.Image:
    avatar_bytes = await member.display_avatar.replace(
        size=CardConfig.AVATAR_DOWNLOAD_SIZE
    ).read()
    avatar_img = PILImage.open(BytesIO(avatar_bytes))
    return avatar_img.convert("RGBA").resize((size, size), PILImage.Resampling.LANCZOS)


def _draw_text_content(
    draw: ImageDraw.ImageDraw,
    member: discord.Member,
    title: str,
    available_width: int
) -> None:
    title_text = f"{title}, {member.display_name} !"
    title_font = _fit_text_to_width(
        draw,
        title_text,
        available_width,
        CardConfig.TITLE_FONT_SIZE,
        bold=True
    )
    draw.text(
        (CardConfig.TEXT_START_X, CardConfig.TITLE_Y),
        title_text,
        font=title_font,
        fill=CardConfig.TITLE_COLOR
    )
    
    subtitle_text = f"Sur le serveur {Config.ServerName}"
    subtitle_font = _fit_text_to_width(
        draw,
        subtitle_text,
        available_width,
        CardConfig.SUBTITLE_FONT_SIZE,
        bold=True
    )
    draw.text(
        (CardConfig.TEXT_START_X, CardConfig.SUBTITLE_Y),
        subtitle_text,
        font=subtitle_font,
        fill=CardConfig.SUBTITLE_COLOR
    )


async def render_card(member: discord.Member, title: str, join: bool) -> BytesIO:
    base = PILImage.new(
        "RGB",
        (CardConfig.WIDTH, CardConfig.HEIGHT),
        CardConfig.BACKGROUND_COLOR
    )
    
    overlay_color = (
        CardConfig.OVERLAY_COLOR_JOIN if join
        else CardConfig.OVERLAY_COLOR_LEAVE
    )
    overlay_alpha = (
        CardConfig.OVERLAY_ALPHA_JOIN if join
        else CardConfig.OVERLAY_ALPHA_LEAVE
    )
    overlay = _create_gradient_overlay(
        CardConfig.WIDTH,
        CardConfig.HEIGHT,
        overlay_color,
        overlay_alpha
    )
    base.paste(overlay, (0, 0), overlay)
    
    avatar_img = await _get_avatar_image(member, CardConfig.AVATAR_SIZE)
    mask = _create_circular_mask(CardConfig.AVATAR_SIZE)
    base.paste(avatar_img, CardConfig.AVATAR_POSITION, mask)
    
    draw = ImageDraw.Draw(base)
    available_width = (
        CardConfig.WIDTH - CardConfig.TEXT_START_X - CardConfig.TEXT_MARGIN_RIGHT
    )
    _draw_text_content(draw, member, title, available_width)
    
    buffer = BytesIO()
    base.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    
    return buffer
