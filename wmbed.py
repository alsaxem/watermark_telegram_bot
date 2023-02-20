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


def apply_threshold(value, threshold):
    if value > threshold:
        return threshold
    else:
        return value


def embed_watermark(image, watermark, position, scale, opacity, padding):
    image_height, image_width = image.shape[:2]
    watermark = scale_watermark(watermark, (image_width, image_height), scale)
    watermark_height, watermark_width = watermark.shape[:2]
    padding = apply_threshold(padding, min(image_width - watermark_width, image_height - watermark_height))
    horizontal_bounds = ()
    vertical_bounds = ()
    vertical_position = position[0]
    horizontal_position = position[1]
    if vertical_position == "T":
        if watermark_height + padding <= image_height:
            vertical_bounds = (padding, watermark_height + padding)
        else:
            vertical_bounds = (padding, image_height)
            watermark = watermark[:image_height - padding, ...]
    elif vertical_position == "B":
        if watermark_height + padding <= image_height:
            vertical_bounds = (image_height - watermark_height - padding, image_height - padding)
        else:
            vertical_bounds = (0, image_height - padding)
            watermark = watermark[watermark_height + padding - image_height:, ...]
    if horizontal_position == "L":
        if watermark_width + padding <= image_width:
            horizontal_bounds = (padding, watermark_width + padding)
        else:
            horizontal_bounds = (padding, image_width)
            watermark = watermark[..., image_width - padding]
    elif horizontal_position == "R":
        if watermark_width + padding <= image_width:
            horizontal_bounds = (image_width - watermark_width - padding, image_width - padding)
        else:
            horizontal_bounds = (0, image_width - padding)
            watermark = watermark[..., watermark_width + padding - image_width]
    region_of_interest = image[vertical_bounds[0]:vertical_bounds[1], horizontal_bounds[0]:horizontal_bounds[1]]
    marked_region_of_interest = cv2.addWeighted(region_of_interest, (1 - opacity), watermark, opacity, 0)
    image[vertical_bounds[0]:vertical_bounds[1], horizontal_bounds[0]:horizontal_bounds[1]] = marked_region_of_interest
    return image


def create_marked_image(
        image_path,
        watermark_path,
        save_path,
        position="BR",
        scale=1.0,
        opacity=0.4,
        padding=0):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    watermark = cv2.imread(watermark_path, cv2.IMREAD_COLOR)
    marked_image = embed_watermark(image, watermark, position, scale, opacity, padding)
    cv2.imwrite(save_path, marked_image)
