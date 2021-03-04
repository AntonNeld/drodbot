from room_simulator import ElementType, Direction, OrbEffect, Element


def element_to_dict(element):
    return {
        "element_type": element.element_type.name,
        "direction": element.direction.name,
        "orb_effects": [(x, y, effect.name) for (x, y, effect) in element.orb_effects],
    }


def element_from_dict(element_dict):
    return Element(
        element_type=getattr(ElementType, element_dict["element_type"]),
        direction=getattr(Direction, element_dict["direction"]),
        orb_effects=[
            (x, y, getattr(OrbEffect, effect))
            for (x, y, effect) in element_dict["orb_effects"]
        ],
    )
