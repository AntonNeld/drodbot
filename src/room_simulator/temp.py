# This file is just to play around to try to get C++ bindings working at all.
# It will be removed later.
import room_simulator

if __name__ == "__main__":
    room_simulator.initialize()
    print("==Room 0==")
    print(f"X after: {room_simulator.simulate_action(0, 1)}")
    print("==Room 1==")
    print(f"X after: {room_simulator.simulate_action(1, 2)}")
