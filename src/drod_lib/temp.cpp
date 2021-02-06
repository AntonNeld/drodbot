// This file is just to play around to try to get C++ bindings working at all.
// It will be removed later.

#include <iostream>
#include <pybind11/pybind11.h>
#include <DRODLib/Db.h>

int temp()
{
    // CDb *db = new CDb;
    // CDbRoom *room = db->Rooms.GetNew();
    // room->AddNewMonster(M_ROACH, 1, 1);
    std::cout << "Hello Eight from C++!";
    return 0;
}

PYBIND11_MODULE(temp_module_name, m)
{
    m.doc() = "Just a module.";
    m.def("hello_world", &temp, "Print a hello");
}