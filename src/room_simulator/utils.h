#ifndef DRODBOT_UTILS_H
#define DRODBOT_UTILS_H

#include "typedefs.h"

Position swordPosition(Position position, Direction direction);
Position movePosition(Position start, Action action);

#endif // DRODBOT_UTILS_H