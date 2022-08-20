# TODOs

## Python code quality

- Make the different states and displayed types in room solver app concentrated somewhere
- Use type hints

## C++ code quality

- Split module.cpp into multiple files
- Use asserts instead of exceptions where appropriate
- Only use std::set when needed, and remove any unnecessary < operator overloads

## Larger refactorings

- Do level walking search in C++ code instead of having two search implementations

## Bugs

- We make up a direction when checking alternative room entrances. If the room is
  solvable with that direction but not the one we end up facing, we can get into an infinite
  loop.
- Fix tiny memory leak

## Functional improvements

- Handle wraithwings
- Interpret stairs better, despite the shade.
  (Custom code to only look at black lines? Make sure that works for all themes.)
- Speed up right-clicking monsters (different screenshot lib?)
- Multi-threaded search!
- Regression tests of solving rooms
- Regression tests to not break apps
- Improve start time by saving textures better

## Done but not presented

- Different room styles
- Performance (and accuracy) improvement by using location-based tile image, and comparing to whole room
- Actually reading the right-click text
