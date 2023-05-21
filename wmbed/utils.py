import numpy as np
import math
import cv2


def get_diagonal(width, height):
    return math.sqrt(width ** 2 + height ** 2)


def get_positional_bounds(image_size, watermark_size, position, relative_padding):
    image_width, image_height = image_size
    watermark_width, watermark_height = watermark_size
    vertical_position = position[0]
    horizontal_position = position[1]
    max_padding_x = image_width - watermark_width
    max_padding_y = image_height - watermark_height
    padding_y = int(max_padding_y * relative_padding)
    padding_x = int(max_padding_x * relative_padding)
    horizontal_bounds = ()
    vertical_bounds = ()
    if vertical_position == "T":
        top_bound = max(padding_y, 0)
        bottom_bound = min(watermark_height + padding_y, image_height)
        vertical_bounds = (top_bound, bottom_bound)
    elif vertical_position == "B":
        top_bound = max(image_height - watermark_height - padding_y, 0)
        bottom_bound = min(image_height - padding_y, image_height)
        vertical_bounds = (top_bound, bottom_bound)
    elif vertical_position == "C":
        image_center_y = image_height // 2
        top_bound = max(image_center_y - watermark_height // 2, 0)
        bottom_bound = min(top_bound + watermark_height, image_height)
        vertical_bounds = (top_bound, bottom_bound)
    if horizontal_position == "L":
        left_bound = max(padding_x, 0)
        right_bound = min(watermark_width + padding_x, image_width)
        horizontal_bounds = (left_bound, right_bound)
    elif horizontal_position == "R":
        left_bound = max(image_width - watermark_width - padding_x, 0)
        right_bound = min(image_width - padding_x, image_width)
        horizontal_bounds = (left_bound, right_bound)
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
    if len(image.shape) < 3:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    if image.shape[2] == 3:
        alpha = np.expand_dims(np.ones(image.shape[:2]), 2) * 255
        alpha = alpha.astype(np.uint8)
        image = np.concatenate([image, alpha], axis=2)
    return image
