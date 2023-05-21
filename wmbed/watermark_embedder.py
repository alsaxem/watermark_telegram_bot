from .utils import *


class WatermarkEmbedder:

    def __init__(self):
        self.image = None
        self.original_watermark = None
        self.watermark = None
        self.marked_image = None

    def get_image_size(self):
        return self.image.shape[1::-1]

    def get_watermark_size(self):
        return self.watermark.shape[1::-1]

    def from_files(self, image_path, watermark_path, store_watermark_copy=True):
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        self.image = normalize_colorspace(image)
        watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
        self.watermark = normalize_colorspace(watermark)
        if store_watermark_copy:
            self.original_watermark = np.copy(self.watermark)

    def from_bytearrays(self, image_bytearray, watermark_bytearray, store_watermark_copy=True):
        image = cv2.imdecode(np.frombuffer(image_bytearray, np.uint8), cv2.IMREAD_UNCHANGED)
        self.image = normalize_colorspace(image)
        watermark = cv2.imdecode(np.frombuffer(watermark_bytearray, np.uint8), cv2.IMREAD_UNCHANGED)
        self.watermark = normalize_colorspace(watermark)
        if store_watermark_copy:
            self.original_watermark = np.copy(self.watermark)

    def reset_watermark(self):
        if self.original_watermark:
            self.watermark = self.original_watermark

    def scale_watermark(self, relative_scale):
        scaled_size = get_relatively_scaled_size(self.get_watermark_size(), self.get_image_size(), relative_scale)
        self.watermark = cv2.resize(self.watermark, scaled_size, interpolation=cv2.INTER_AREA)

    def embed_positional_watermark(self, position="BR", scale=1.0, angle=0, opacity=0.4, relative_padding=0):
        self.rotate_watermark(angle)
        self.scale_watermark(scale)
        horizontal_bounds, vertical_bounds = get_positional_bounds(
            self.get_image_size(), self.get_watermark_size(), position, relative_padding)
        self.embed(horizontal_bounds, vertical_bounds, opacity)

    def rotate_watermark(self, angle):
        angle = angle % 360
        if angle == 0:
            return
        rotation_matrix, new_width, new_height = get_image_rotation_args(self.get_watermark_size(), angle)
        self.watermark = cv2.warpAffine(self.watermark, rotation_matrix, (new_width, new_height))

    def embed_watermark_tiling(self, scale=1.0, angle=0, opacity=0.4):
        self.scale_watermark(scale)
        tiling_height_weight, tiling_width_weight = get_tiling_weights(self.get_watermark_size(), self.get_image_size())
        self.watermark = np.tile(self.watermark, (tiling_height_weight, tiling_width_weight, 1))
        self.rotate_watermark(angle)
        watermark_tiling_width, watermark_tiling_height = self.get_watermark_size()
        image_width, image_height = self.get_image_size()
        horizontal_bounds, vertical_bounds = get_positional_bounds(
            (watermark_tiling_width, watermark_tiling_height), (image_width, image_height), "CC", 0)
        self.watermark = crop(self.watermark, horizontal_bounds, vertical_bounds)
        self.embed((0, image_width), (0, image_height), opacity)

    def embed(self, horizontal_bounds, vertical_bounds, opacity):
        region_of_interest = crop(self.image, horizontal_bounds, vertical_bounds)
        marked_region_of_interest = blend(region_of_interest, self.watermark, opacity)
        self.marked_image = paste(self.image, marked_region_of_interest, horizontal_bounds, vertical_bounds)

    def apply_noise_to_watermark(self, intensity=0.7, opacity=1):
        alpha_filter = (self.watermark[:, :, 3] > 0).astype(np.uint8)
        noise = get_noise(self.watermark.shape, intensity, alpha_filter)
        self.watermark = blend(self.watermark, noise, opacity)

    def save_to_file(self, save_path):
        cv2.imwrite(save_path, self.marked_image)

    def get_result_byte_array(self):
        return cv2.imencode('.png', self.marked_image)[1]
