import cv2
import numpy as np
import math


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
        vertical_bounds = (
            max(image_height - watermark_height - padding, 0), min(image_height - padding, image_height))
    if horizontal_position == "L":
        horizontal_bounds = (max(padding, 0), min(watermark_width + padding, image_width))
    elif horizontal_position == "R":
        horizontal_bounds = (
            max(image_width - watermark_width - padding, 0), min(image_width - padding, image_width))
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


class WMbed:

    def __init__(self):
        self._image = None
        self._original_watermark = None
        self._watermark = None
        self._marked_image = None

    def from_files(self, image_path, watermark_path, store_watermark_copy=True):
        self._image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        self._watermark = cv2.imread(watermark_path, cv2.IMREAD_COLOR)
        if store_watermark_copy:
            self._original_watermark = np.copy(self._original_watermark)

    def from_bytearrays(self, image_bytearray, watermark_bytearray, store_watermark_copy=True):
        self._image = cv2.imdecode(np.fromstring(image_bytearray, np.uint8), cv2.IMREAD_COLOR)
        self._watermark = cv2.imdecode(np.fromstring(watermark_bytearray, np.uint8), cv2.IMREAD_COLOR)
        if store_watermark_copy:
            self._original_watermark = np.copy(self._original_watermark)

    def reset_watermark(self):
        if self._original_watermark:
            self._watermark = self._original_watermark

    def _scale_watermark(self, relative_scale):
        watermark_height, watermark_width = self._watermark.shape[:2]
        image_height, image_width = self._image.shape[:2]
        width_ratio = image_width / watermark_width
        height_ratio = image_height / watermark_height
        true_scale = min(width_ratio, height_ratio) * relative_scale
        resized_dimensions = (int(watermark_width * true_scale), int(watermark_height * true_scale))
        self._watermark = cv2.resize(self._watermark, resized_dimensions, interpolation=cv2.INTER_AREA)

    def embed_central_watermark(self, scale=1.0, opacity=0.4):
        image_height, image_width = self._image.shape[:2]
        self._scale_watermark(scale)
        watermark_height, watermark_width = self._watermark.shape[:2]
        horizontal_bounds, vertical_bounds = get_central_bounds(
            (image_width, image_height), (watermark_width, watermark_height))
        self._embed(horizontal_bounds, vertical_bounds, opacity)

    def embed_positional_watermark(self, position="BR", scale=1.0, opacity=0.4, relative_padding=0):
        image_height, image_width = self._image.shape[:2]
        self._scale_watermark(scale)
        watermark_height, watermark_width = self._watermark.shape[:2]
        padding_limit = min(image_width - watermark_width, image_height - watermark_height)
        padding = int(padding_limit * relative_padding)
        horizontal_bounds, vertical_bounds = get_positional_bounds(
            (image_width, image_height), (watermark_width, watermark_height), position, padding)
        self._embed(horizontal_bounds, vertical_bounds, opacity)

    def _rotate_watermark(self, angle):
        height, width = self._watermark.shape[:2]
        image_center = (width // 2, height // 2)
        rotation_mat = cv2.getRotationMatrix2D(image_center, -angle, 1.0)
        abs_cos = abs(rotation_mat[0, 0])
        abs_sin = abs(rotation_mat[0, 1])
        new_width = int(height * abs_sin + width * abs_cos)
        new_height = int(height * abs_cos + width * abs_sin)
        rotation_mat[0, 2] += new_width // 2 - image_center[0]
        rotation_mat[1, 2] += new_height // 2 - image_center[1]
        self._watermark = cv2.warpAffine(self._watermark, rotation_mat, (new_width, new_height))

    def embed_watermark_tiling(self, scale=1.0, angle=0, opacity=0.4):
        image_height, image_width = self._image.shape[:2]
        self._scale_watermark(scale)
        watermark_height, watermark_width = self._watermark.shape[:2]
        tiling_size_lower_bound = round(get_diagonal(image_width, image_height))
        tiling_width_weight = (tiling_size_lower_bound + watermark_width) // watermark_width
        if tiling_width_weight % 2 == 0:
            tiling_width_weight += 1
        tiling_height_weight = (tiling_size_lower_bound + watermark_height) // watermark_height
        if tiling_height_weight % 2 == 0:
            tiling_height_weight += 1
        self._watermark = np.tile(self._watermark, (tiling_height_weight, tiling_width_weight, 1))
        if angle % 360 != 0:
            self._rotate_watermark(angle)
        watermark_tiling_height, watermark_tiling_width = self._watermark.shape[:2]
        horizontal_bounds, vertical_bounds = get_central_bounds(
            (watermark_tiling_width, watermark_tiling_height), (image_width, image_height))
        self._watermark = crop(self._watermark, horizontal_bounds, vertical_bounds)
        self._embed((0, image_width), (0, image_height), opacity)

    def _embed(self, horizontal_bounds, vertical_bounds, opacity):
        region_of_interest = crop(self._image, horizontal_bounds, vertical_bounds)
        marked_region_of_interest = cv2.addWeighted(
            region_of_interest, (1 - opacity), self._watermark, opacity, 0)
        self._marked_image = paste(self._image, marked_region_of_interest, horizontal_bounds, vertical_bounds)
        
    def save_to_file(self, save_path):
        cv2.imwrite(save_path, self._marked_image)
        
    def get_result_byte_array(self):
        return cv2.imencode('.png', self._marked_image)[1]


def create_image_with_central_watermark(
        image_bytearray,
        watermark_bytearray,
        scale,
        opacity):
    wmbed = WMbed()
    wmbed.from_bytearrays(image_bytearray, watermark_bytearray, False)
    wmbed.embed_central_watermark(scale, opacity)
    return wmbed.get_result_byte_array()


def create_image_with_positional_watermark(
        image_bytearray,
        watermark_bytearray,
        position,
        scale,
        opacity,
        relative_padding):
    wmbed = WMbed()
    wmbed.from_bytearrays(image_bytearray, watermark_bytearray, False)
    wmbed.embed_positional_watermark(position, scale, opacity, relative_padding)
    return wmbed.get_result_byte_array()


def create_image_with_watermark_tiling(
        image_bytearray,
        watermark_bytearray,
        scale,
        angle,
        opacity):
    wmbed = WMbed()
    wmbed.from_bytearrays(image_bytearray, watermark_bytearray, False)
    wmbed.embed_watermark_tiling(scale, angle, opacity)
    return wmbed.get_result_byte_array()
