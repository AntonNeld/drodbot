from common import Direction


def tile_to_text(tile):
    lines = [
        f"Room piece: {_format_element(tile.room_piece)}",
        f"Floor control: {_format_element(tile.floor_control)}",
        f"Checkpoint: {_format_element(tile.checkpoint)}",
        f"Item: {_format_element(tile.item)}",
        f"Monster: {_format_element(tile.monster)}",
    ]
    return "\n".join(lines)


def _format_element(pair):
    element, direction = pair
    if direction == Direction.NONE:
        return element.value
    else:
        return f"{element.value} {direction.value}"
