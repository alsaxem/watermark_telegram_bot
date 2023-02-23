import cv2


def scale_watermark(watermark, image_size, relative_scale):
    watermark_height, watermark_width, _ = watermark.shape
    image_width, image_height = image_size
    width_ratio = image_width / watermark_width
    height_ratio = image_height / watermark_height
    true_scale = min(width_ratio, height_ratio) * relative_scale
    resized_dimensions = (int(watermark_width * true_scale), int(watermark_height * true_scale))
    resized = cv2.resize(watermark, resized_dimensions, interpolation=cv2.INTER_AREA)
    return resized


def embed_central_watermark(image, watermark, scale, opacity):
    image_height, image_width = image.shape[:2]
    watermark = scale_watermark(watermark, (image_width, image_height), scale)
    watermark_height, watermark_width = watermark.shape[:2]
    image_center_x = image_width // 2
    image_center_y = image_height // 2
    left_bound = image_center_x - watermark_width // 2
    right_bound = left_bound + watermark_width
    top_bound = image_center_y - watermark_height // 2
    bottom_bound = top_bound + watermark_height
    marked_image = embed(image, watermark, (left_bound, right_bound), (top_bound, bottom_bound), opacity)
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


def crop(image, horizontal_bounds, vertical_bounds):
    hb1, hb2 = horizontal_bounds
    vb1, vb2 = vertical_bounds
    return image[vb1:vb2, hb1:hb2]


def paste(image, insert, horizontal_bounds, vertical_bounds):
    hb1, hb2 = horizontal_bounds
    vb1, vb2 = vertical_bounds
    image[vb1:vb2, hb1:hb2] = insert
    return image


def embed(image, watermark, horizontal_bounds, vertical_bounds, opacity):
    region_of_interest = crop(image, horizontal_bounds, vertical_bounds)
    marked_region_of_interest = cv2.addWeighted(region_of_interest, (1 - opacity), watermark, opacity, 0)
    marked_image = paste(image, marked_region_of_interest, horizontal_bounds, vertical_bounds)
    return marked_image


def create_image_with_central_watermark(
        image_path,
        watermark_path,
        save_path,
        scale=1.0,
        opacity=0.4):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    watermark = cv2.imread(watermark_path, cv2.IMREAD_COLOR)
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
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    watermark = cv2.imread(watermark_path, cv2.IMREAD_COLOR)
    marked_image = embed_positional_watermark(image, watermark, position, scale, opacity, relative_padding)
    cv2.imwrite(save_path, marked_image)
