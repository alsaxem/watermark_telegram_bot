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
