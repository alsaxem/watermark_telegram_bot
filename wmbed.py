import cv2
import numpy as np
import math


def scale_watermark(watermark, image_size, relative_scale):
    watermark_height, watermark_width, _ = watermark.shape
    image_width, image_height = image_size
    width_ratio = image_width / watermark_width
    height_ratio = image_height / watermark_height
    true_scale = min(width_ratio, height_ratio) * relative_scale
    resized_dimensions = (int(watermark_width * true_scale), int(watermark_height * true_scale))
    resized = cv2.resize(watermark, resized_dimensions, interpolation=cv2.INTER_AREA)
    return resized


def get_central_bounds(image_size, watermark_size):
    image_width, image_height = image_size
    watermark_width, watermark_height = watermark_size
    image_center_x = image_width // 2
    image_center_y = image_height // 2
    left_bound = max(image_center_x - watermark_width // 2, 0)
    right_bound = min(left_bound + watermark_width, image_width)
    top_bound = max(image_center_y - watermark_height // 2, 0)
    bottom_bound = min(top_bound + watermark_height, image_height)
    return (left_bound, right_bound), (top_bound, bottom_bound)


def embed_central_watermark(image, watermark, scale, opacity):
    image_height, image_width = image.shape[:2]
    watermark = scale_watermark(watermark, (image_width, image_height), scale)
    watermark_height, watermark_width = watermark.shape[:2]
    horizontal_bounds, vertical_bounds = get_central_bounds(
        (image_width, image_height), (watermark_width, watermark_height))
    marked_image = embed(image, watermark, horizontal_bounds, vertical_bounds, opacity)
    return marked_image


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
    if horizontal_position == "L":
        horizontal_bounds = (max(padding, 0), min(watermark_width + padding, image_width))
    elif horizontal_position == "R":
        horizontal_bounds = (max(image_width - watermark_width - padding, 0), min(image_width - padding, image_width))
    return horizontal_bounds, vertical_bounds


def embed_positional_watermark(image, watermark, position, scale, opacity, relative_padding):
    image_height, image_width = image.shape[:2]
    watermark = scale_watermark(watermark, (image_width, image_height), scale)
    watermark_height, watermark_width = watermark.shape[:2]
    padding_limit = min(image_width - watermark_width, image_height - watermark_height)
    padding = int(padding_limit * relative_padding)
    horizontal_bounds, vertical_bounds = get_positional_bounds(
        (image_width, image_height), (watermark_width, watermark_height), position, padding)
    marked_image = embed(image, watermark, horizontal_bounds, vertical_bounds, opacity)
    return marked_image


def rotate_watermark(watermark, angle):
    height, width = watermark.shape[:2]
    image_center = (width // 2, height // 2)
    rotation_mat = cv2.getRotationMatrix2D(image_center, -angle, 1.0)
    abs_cos = abs(rotation_mat[0, 0])
    abs_sin = abs(rotation_mat[0, 1])
    new_width = int(height * abs_sin + width * abs_cos)
    new_height = int(height * abs_cos + width * abs_sin)
    rotation_mat[0, 2] += new_width // 2 - image_center[0]
    rotation_mat[1, 2] += new_height // 2 - image_center[1]
    rotated_mat = cv2.warpAffine(watermark, rotation_mat, (new_width, new_height))
    return rotated_mat


def crop(image, horizontal_bounds, vertical_bounds):
    hb1, hb2 = horizontal_bounds
    vb1, vb2 = vertical_bounds
    return image[vb1:vb2, hb1:hb2]


def paste(image, insert, horizontal_bounds, vertical_bounds):
    hb1, hb2 = horizontal_bounds
    vb1, vb2 = vertical_bounds
    image[vb1:vb2, hb1:hb2] = insert
    return image


def get_diagonal(width, height):
    return math.sqrt(width ** 2 + height ** 2)


def embed_watermark_tiling(image, watermark, scale, angle, opacity):
    image_height, image_width = image.shape[:2]
    watermark = scale_watermark(watermark, (image_width, image_height), scale)
    watermark_height, watermark_width = watermark.shape[:2]
    tiling_size_lower_bound = round(get_diagonal(image_width, image_height))
    tiling_width_weight = (tiling_size_lower_bound + watermark_width) // watermark_width
    if tiling_width_weight % 2 == 0:
        tiling_width_weight += 1
    tiling_height_weight = (tiling_size_lower_bound + watermark_height) // watermark_height
    if tiling_height_weight % 2 == 0:
        tiling_height_weight += 1
    watermark_tiling = np.tile(watermark, (tiling_height_weight, tiling_width_weight, 1))
    if angle % 360 != 0:
        watermark_tiling = rotate_watermark(watermark_tiling, angle)
    watermark_tiling_height, watermark_tiling_width = watermark_tiling.shape[:2]
    horizontal_bounds, vertical_bounds = get_central_bounds(
        (watermark_tiling_width, watermark_tiling_height), (image_width, image_height))
    cropped_watermark_tiling = crop(watermark_tiling, horizontal_bounds, vertical_bounds)
    marked_image = embed(image, cropped_watermark_tiling, (0, image_width), (0, image_height), opacity)
    return marked_image


def embed(image, watermark, horizontal_bounds, vertical_bounds, opacity):
    region_of_interest = crop(image, horizontal_bounds, vertical_bounds)
    marked_region_of_interest = blend(region_of_interest, watermark, opacity)
    marked_image = paste(image, marked_region_of_interest, horizontal_bounds, vertical_bounds)
    return marked_image


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


def add_alpha(image):
    alpha = np.expand_dims(np.ones(image.shape[:2]), 2) * 255
    return np.concatenate([image, alpha], axis=2)


def create_image_with_central_watermark(
        image_path,
        watermark_path,
        save_path,
        scale=1.0,
        opacity=0.4):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image.shape[2] == 3:
        image = add_alpha(image)
    watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
    if watermark.shape[2] == 3:
        watermark = add_alpha(watermark)
    marked_image = embed_central_watermark(image, watermark, scale, opacity)
    cv2.imwrite(save_path, marked_image)


def create_image_with_positional_watermark(
        image_path,
        watermark_path,
        save_path,
        position="BR",
        scale=1.0,
        opacity=0.4,
        relative_padding=0):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image.shape[2] == 3:
        image = add_alpha(image)
    watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
    if watermark.shape[2] == 3:
        watermark = add_alpha(watermark)
    marked_image = embed_positional_watermark(image, watermark, position, scale, opacity, relative_padding)
    cv2.imwrite(save_path, marked_image)


def create_image_with_watermark_tiling(
        image_path,
        watermark_path,
        save_path,
        scale=1.0,
        angle=0,
        opacity=0.4):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image.shape[2] == 3:
        image = add_alpha(image)
    watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
    if watermark.shape[2] == 3:
        watermark = add_alpha(watermark)
    marked_image = embed_watermark_tiling(image, watermark, scale, angle, opacity)
    cv2.imwrite(save_path, marked_image)
