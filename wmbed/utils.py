import numpy as np
import math
import cv2


def get_diagonal(width, height):
    return math.sqrt(width ** 2 + height ** 2)


def get_relatively_scaled_size(original_size, destination_size, relative_scale):
    watermark_width, watermark_height = original_size
    image_width, image_height = destination_size
    width_ratio = image_width / watermark_width
    height_ratio = image_height / watermark_height
    true_scale = min(width_ratio, height_ratio) * relative_scale
    scaled_size = (int(watermark_width * true_scale), int(watermark_height * true_scale))
    return scaled_size


def get_image_rotation_args(image_size, angle):
    width, height = image_size
    image_center = (width // 2, height // 2)
    rotation_matrix = cv2.getRotationMatrix2D(image_center, -angle, 1.0)
    abs_cos = abs(rotation_matrix[0, 0])
    abs_sin = abs(rotation_matrix[0, 1])
    new_width = int(height * abs_sin + width * abs_cos)
    new_height = int(height * abs_cos + width * abs_sin)
    rotation_matrix[0, 2] += new_width // 2 - image_center[0]
    rotation_matrix[1, 2] += new_height // 2 - image_center[1]
    return rotation_matrix, new_width, new_height


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


def get_tiling_weights(tiling_image_size, target_image_size):
    target_image_width, target_image_height = target_image_size
    tiling_image_width, tiling_image_height = tiling_image_size
    tiling_size_lower_bound = round(get_diagonal(target_image_width, target_image_height))
    tiling_width_weight = (tiling_size_lower_bound + tiling_image_width) // tiling_image_width
    if tiling_width_weight % 2 == 0:
        tiling_width_weight += 1
    tiling_height_weight = (tiling_size_lower_bound + tiling_image_height) // tiling_image_height
    if tiling_height_weight % 2 == 0:
        tiling_height_weight += 1
    return tiling_height_weight, tiling_width_weight


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


def get_noise(shape, intensity, alpha_filter):
    mean = np.zeros((4,), np.uint8)
    standard_deviation = np.empty((4,), np.uint8)
    standard_deviation.fill(intensity * 255)
    noise = np.zeros(shape, np.uint8)
    cv2.randn(noise, mean, standard_deviation)
    noise[:, :, 3] = noise[:, :, 3] * alpha_filter
    return noise
