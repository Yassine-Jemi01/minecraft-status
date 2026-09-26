from __future__ import annotations

import gzip
import io
import struct
import zlib
from pathlib import Path

import nbtlib

from .legacy_biomes import get_legacy_biome, get_pre_flattening_biome
from .world_format import get_data_version

SECTOR_SIZE = 4096


def _dimension_region_dir(world_dir: Path, dimension: str) -> Path:
    modern = {
        "minecraft:overworld": world_dir / "dimensions/minecraft/overworld/region",
        "minecraft:the_nether": world_dir / "dimensions/minecraft/the_nether/region",
        "minecraft:the_end": world_dir / "dimensions/minecraft/the_end/region",
    }
    modern_path = modern.get(dimension)
    if modern_path is not None and modern_path.exists():
        return modern_path
    if dimension == "minecraft:overworld":
        return world_dir / "region"
    if dimension == "minecraft:the_nether":
        return world_dir / "DIM-1/region"
    if dimension == "minecraft:the_end":
        return world_dir / "DIM1/region"
    return world_dir / "region"


def _read_chunk_nbt(world_dir: Path, dimension: str, chunk_x: int, chunk_z: int):
    region_dir = _dimension_region_dir(world_dir, dimension)
    region_file = region_dir / f"r.{chunk_x // 32}.{chunk_z // 32}.mca"
    if not region_file.exists():
        return None
    local_x = chunk_x & 31
    local_z = chunk_z & 31
    header_offset = 4 * (local_x + local_z * 32)
    try:
        with region_file.open("rb") as file:
            file.seek(header_offset)
            location = file.read(4)
            if len(location) != 4:
                return None
            sector_offset = int.from_bytes(location[:3], "big")
            sector_count = location[3]
            if sector_offset == 0 or sector_count == 0:
                return None
            file.seek(sector_offset * SECTOR_SIZE)
            length_data = file.read(4)
            if len(length_data) != 4:
                return None
            chunk_length = struct.unpack(">I", length_data)[0]
            if chunk_length <= 1:
                return None
            compression_data = file.read(1)
            if len(compression_data) != 1:
                return None
            compressed_data = file.read(chunk_length - 1)
        compression_type = compression_data[0]
        if compression_type & 0x80:
            return None
        if compression_type == 1:
            nbt_data = gzip.decompress(compressed_data)
        elif compression_type == 2:
            nbt_data = zlib.decompress(compressed_data)
        elif compression_type == 3:
            nbt_data = compressed_data
        else:
            return None
        return nbtlib.File.parse(io.BytesIO(nbt_data))
    except (OSError, EOFError, ValueError, TypeError, struct.error, zlib.error):
        return None


def _get_chunk_data(chunk):
    return chunk.get("Level") or chunk


def _get_section_for_y(chunk_data, block_y: int):
    sections = chunk_data.get("sections") or chunk_data.get("Sections")
    if sections is None:
        return None
    section_y = block_y // 16
    for section in sections:
        try:
            if int(section.get("Y", 999999)) == section_y:
                return section
        except (TypeError, ValueError):
            continue
    return None


def _read_palette_index(data, index: int, bits_per_entry: int, entries_per_long: int) -> int | None:
    long_index = index // entries_per_long
    index_in_long = index % entries_per_long
    if long_index >= len(data):
        return None
    value = int(data[long_index])
    bit_offset = index_in_long * bits_per_entry
    mask = (1 << bits_per_entry) - 1
    return (value >> bit_offset) & mask


def _modern_section_biome(chunk_data, block_x: int, block_y: int, block_z: int) -> str | None:
    section = _get_section_for_y(chunk_data, block_y)
    if section is None:
        return None
    biomes = section.get("biomes")
    if biomes is None:
        return None
    palette = biomes.get("palette")
    if not palette:
        return None
    if len(palette) == 1:
        return str(palette[0])
    data = biomes.get("data")
    if data is None:
        return None
    biome_x = (block_x & 15) // 4
    biome_y = (block_y & 15) // 4
    biome_z = (block_z & 15) // 4
    index = biome_x + biome_z * 4 + biome_y * 16
    bits = max(1, (len(palette) - 1).bit_length())
    entries_per_long = 64 // bits
    palette_index = _read_palette_index(data, index, bits, entries_per_long)
    if palette_index is None or palette_index >= len(palette):
        return None
    return str(palette[palette_index])


def _legacy_biome(world_dir: Path, chunk_data, block_x: int, block_y: int, block_z: int) -> str | None:
    values = chunk_data.get("Biomes")
    if values is None:
        return None
    try:
        values = list(values)
    except TypeError:
        return None
    if not values:
        return None
    local_x = block_x & 15
    local_z = block_z & 15
    if len(values) == 256:
        index = local_x + local_z * 16
    elif len(values) >= 1024:
        index = (local_x // 4) + (local_z // 4) * 4 + (block_y // 4) * 16
    else:
        return None
    if not 0 <= index < len(values):
        return None
    try:
        biome_id = int(values[index])
    except (TypeError, ValueError):
        return None
    data_version = get_data_version(world_dir)
    if data_version is not None and data_version < 1519:
        return get_pre_flattening_biome(biome_id)
    return get_legacy_biome(biome_id)


def get_biome(world_dir: Path, player_data: dict | None) -> str | None:
    if player_data is None:
        return None
    dimension = player_data.get("dimension")
    if not dimension:
        return None
    try:
        x = float(player_data["x"])
        y = float(player_data["y"])
        z = float(player_data["z"])
    except (KeyError, TypeError, ValueError):
        return None
    block_x = int(x // 1)
    block_y = int(y // 1)
    block_z = int(z // 1)
    chunk = _read_chunk_nbt(world_dir, dimension, block_x // 16, block_z // 16)
    if chunk is None:
        return None
    chunk_data = _get_chunk_data(chunk)
    modern = _modern_section_biome(chunk_data, block_x, block_y, block_z)
    if modern is not None:
        return modern
    return _legacy_biome(world_dir, chunk_data, block_x, block_y, block_z)


def format_biome(biome: str | None) -> str:
    if biome is None:
        return "Unknown"
    return biome.split(":", 1)[-1].replace("_", " ").title()
