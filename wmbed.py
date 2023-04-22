import cv2
import numpy as np
import wmbed_utils


class WMbed:

    def __init__(self):
        self.image = None
        self.original_watermark = None
        self.watermark = None
        self.marked_image = None

    def from_files(self, image_path, watermark_path, store_watermark_copy=True):
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        self.image = wmbed_utils.add_missing_alpha(image)
        watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
        self.watermark = wmbed_utils.add_missing_alpha(watermark)
        if store_watermark_copy:
            self.original_watermark = np.copy(self.watermark)

    def from_bytearrays(self, image_bytearray, watermark_bytearray, store_watermark_copy=True):
        image = cv2.imdecode(np.frombuffer(image_bytearray, np.uint8), cv2.IMREAD_UNCHANGED)
        self.image = wmbed_utils.add_missing_alpha(image)
        watermark = cv2.imdecode(np.frombuffer(watermark_bytearray, np.uint8), cv2.IMREAD_UNCHANGED)
        self.watermark = wmbed_utils.add_missing_alpha(watermark)
        if store_watermark_copy:
            self.original_watermark = np.copy(self.watermark)

    def reset_watermark(self):
        if self.original_watermark:
            self.watermark = self.original_watermark

    def scale_watermark(self, relative_scale):
        watermark_height, watermark_width = self.watermark.shape[:2]
        image_height, image_width = self.image.shape[:2]
        width_ratio = image_width / watermark_width
        height_ratio = image_height / watermark_height
        true_scale = min(width_ratio, height_ratio) * relative_scale
        resized_dimensions = (int(watermark_width * true_scale), int(watermark_height * true_scale))
        self.watermark = cv2.resize(self.watermark, resized_dimensions, interpolation=cv2.INTER_AREA)

    def embed_central_watermark(self, scale=1.0, opacity=0.4):
        image_height, image_width = self.image.shape[:2]
        self.scale_watermark(scale)
        watermark_height, watermark_width = self.watermark.shape[:2]
        horizontal_bounds, vertical_bounds = wmbed_utils.get_central_bounds(
            (image_width, image_height), (watermark_width, watermark_height))
        self.embed(horizontal_bounds, vertical_bounds, opacity)

    def embed_positional_watermark(self, position="BR", scale=1.0, opacity=0.4, relative_padding=0):
        image_height, image_width = self.image.shape[:2]
        self.scale_watermark(scale)
        watermark_height, watermark_width = self.watermark.shape[:2]
        padding_limit = min(image_width - watermark_width, image_height - watermark_height)
        padding = int(padding_limit * relative_padding)
        horizontal_bounds, vertical_bounds = wmbed_utils.get_positional_bounds(
            (image_width, image_height), (watermark_width, watermark_height), position, padding)
        self.embed(horizontal_bounds, vertical_bounds, opacity)

    def rotate_watermark(self, angle):
        height, width = self.watermark.shape[:2]
        image_center = (width // 2, height // 2)
        rotation_mat = cv2.getRotationMatrix2D(image_center, -angle, 1.0)
        abs_cos = abs(rotation_mat[0, 0])
        abs_sin = abs(rotation_mat[0, 1])
        new_width = int(height * abs_sin + width * abs_cos)
        new_height = int(height * abs_cos + width * abs_sin)
        rotation_mat[0, 2] += new_width // 2 - image_center[0]
        rotation_mat[1, 2] += new_height // 2 - image_center[1]
        self.watermark = cv2.warpAffine(self.watermark, rotation_mat, (new_width, new_height))

    def embed_watermark_tiling(self, scale=1.0, angle=0, opacity=0.4):
        image_height, image_width = self.image.shape[:2]
        self.scale_watermark(scale)
        watermark_height, watermark_width = self.watermark.shape[:2]
        tiling_size_lower_bound = round(wmbed_utils.get_diagonal(image_width, image_height))
        tiling_width_weight = (tiling_size_lower_bound + watermark_width) // watermark_width
        if tiling_width_weight % 2 == 0:
            tiling_width_weight += 1
        tiling_height_weight = (tiling_size_lower_bound + watermark_height) // watermark_height
        if tiling_height_weight % 2 == 0:
            tiling_height_weight += 1
        self.watermark = np.tile(self.watermark, (tiling_height_weight, tiling_width_weight, 1))
        if angle % 360 != 0:
            self.rotate_watermark(angle)
        watermark_tiling_height, watermark_tiling_width = self.watermark.shape[:2]
        horizontal_bounds, vertical_bounds = wmbed_utils.get_central_bounds(
            (watermark_tiling_width, watermark_tiling_height), (image_width, image_height))
        self.watermark = wmbed_utils.crop(self.watermark, horizontal_bounds, vertical_bounds)
        self.embed((0, image_width), (0, image_height), opacity)

    def embed(self, horizontal_bounds, vertical_bounds, opacity):
        region_of_interest = wmbed_utils.crop(self.image, horizontal_bounds, vertical_bounds)
        marked_region_of_interest = wmbed_utils.blend(region_of_interest, self.watermark, opacity)
        self.marked_image = wmbed_utils.paste(self.image, marked_region_of_interest, horizontal_bounds, vertical_bounds)

    def save_to_file(self, save_path):
        cv2.imwrite(save_path, self.marked_image)

    def get_result_byte_array(self):
        return cv2.imencode('.png', self.marked_image)[1]
