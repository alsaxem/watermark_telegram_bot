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


def embed_positional_watermark(image, watermark, position, scale, opacity, relative_padding):
    image_height, image_width = image.shape[:2]
    watermark = scale_watermark(watermark, (image_width, image_height), scale)
    watermark_height, watermark_width = watermark.shape[:2]
    padding_limit = min(image_width - watermark_width, image_height - watermark_height)
    padding = int(padding_limit * relative_padding)
    horizontal_bounds = ()
    vertical_bounds = ()
    vertical_position = position[0]
    horizontal_position = position[1]
    if vertical_position == "T":
        vertical_bounds = (padding, watermark_height + padding)
    elif vertical_position == "B":
        vertical_bounds = (image_height - watermark_height - padding, image_height - padding)
    if horizontal_position == "L":
        horizontal_bounds = (padding, watermark_width + padding)
    elif horizontal_position == "R":
        horizontal_bounds = (image_width - watermark_width - padding, image_width - padding)
    marked_image = embed(image, watermark, horizontal_bounds, vertical_bounds, opacity)
    return marked_image


def embed(image, watermark, horizontal_bounds, vertical_bounds, opacity):
    hb1, hb2 = horizontal_bounds
    vb1, vb2 = vertical_bounds
    region_of_interest = image[vb1:vb2, hb1:hb2]
    marked_region_of_interest = cv2.addWeighted(region_of_interest, (1 - opacity), watermark, opacity, 0)
    image[vb1:vb2, hb1:hb2] = marked_region_of_interest
    return image


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
