from .room_tester import RoomTester


def test_rooms_standalone(test_room_dir: str):
    """Test saved rooms

    Parameters
    ----------
    test_room_dir
        Location of saved rooms
    """
    room_tester = RoomTester(test_room_dir)
    room_tester.load_test_rooms()
    room_tester.run_tests()
    failed_tests = room_tester.get_failed_tests()
    print("---")
    if len(failed_tests) == 0:
        print("Solved all rooms")
    else:
        print("Failed to solve these rooms:")
        for test in failed_tests:
            print(test.file_name)
