from .watermark_embedder import *


def create_image_with_positional_watermark(
        image_bytearray,
        watermark_bytearray,
        position,
        scale,
        angle,
        opacity,
        relative_padding,
        add_noise):
    watermark_embedder = WatermarkEmbedder()
    watermark_embedder.from_bytearrays(image_bytearray, watermark_bytearray, False)
    if add_noise:
        watermark_embedder.apply_noise_to_watermark()
    watermark_embedder.embed_positional_watermark(position, scale, angle, opacity, relative_padding)
    return watermark_embedder.get_result_byte_array()


def create_image_with_watermark_tiling(
        image_bytearray,
        watermark_bytearray,
        scale,
        angle,
        opacity,
        add_noise):
    watermark_embedder = WatermarkEmbedder()
    watermark_embedder.from_bytearrays(image_bytearray, watermark_bytearray, False)
    if add_noise:
        watermark_embedder.apply_noise_to_watermark()
    watermark_embedder.embed_watermark_tiling(scale, angle, opacity)
    return watermark_embedder.get_result_byte_array()
