import numpy as np
import math


def get_diagonal(width, height):
    return math.sqrt(width ** 2 + height ** 2)


def get_positional_bounds(image_size, watermark_size, position, padding):
    image_width, image_height = image_size
    watermark_width, watermark_height = watermark_size
    vertical_position = position[0]
    horizontal_position = position[1]
    horizontal_bounds = ()
    vertical_bounds = ()
    if vertical_position == "T":
        vertical_bounds = (max(padding, 0), min(watermark_height + padding, image_height))
    elif vertical_position == "B":
        vertical_bounds = (max(image_height - watermark_height - padding, 0), min(image_height - padding, image_height))
    elif vertical_position == "C":
        image_center_y = image_height // 2
        top_bound = max(image_center_y - watermark_height // 2, 0)
        bottom_bound = min(top_bound + watermark_height, image_height)
        vertical_bounds = (top_bound, bottom_bound)
    if horizontal_position == "L":
        horizontal_bounds = (max(padding, 0), min(watermark_width + padding, image_width))
    elif horizontal_position == "R":
        horizontal_bounds = (max(image_width - watermark_width - padding, 0), min(image_width - padding, image_width))
    elif horizontal_position == "C":
        image_center_x = image_width // 2
        left_bound = max(image_center_x - watermark_width // 2, 0)
        right_bound = min(left_bound + watermark_width, image_width)
        horizontal_bounds = (left_bound, right_bound)
    return horizontal_bounds, vertical_bounds


def crop(image, horizontal_bounds, vertical_bounds):
    hb1, hb2 = horizontal_bounds
    vb1, vb2 = vertical_bounds
    return image[vb1:vb2, hb1:hb2]


def paste(image, insert, horizontal_bounds, vertical_bounds):
    hb1, hb2 = horizontal_bounds
    vb1, vb2 = vertical_bounds
    image[vb1:vb2, hb1:hb2] = insert
    return image


def blend(image, overlay, alpha):
    image = image / 255
    overlay = overlay / 255 * alpha
    overlay_color = overlay[..., :3]
    overlay_alpha = np.expand_dims(overlay[..., 3], 2)
    image_color = image[..., :3]
    image_alpha = np.expand_dims(image[..., 3], 2)
    blend_alpha = overlay_alpha + image_alpha - overlay_alpha * image_alpha
    blend_color = np.divide(
        overlay_alpha * overlay_color + (1 - overlay_alpha) * image_alpha * image_color,
        blend_alpha,
        out=np.zeros_like(overlay_color),
        where=(blend_alpha != 0))
    return np.concatenate([blend_color, blend_alpha], axis=2) * 255


def normalize_colorspace(image):
    if image.shape[2] == 3:
        alpha = np.expand_dims(np.ones(image.shape[:2]), 2) * 255
        image = np.concatenate([image, alpha], axis=2)
    return image
