// This file is just to play around to try to get C++ bindings working at all.
// It will be removed later.

#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <sys/stat.h>
#include <pybind11/pybind11.h>

#include <DRODLib/CurrentGame.h>
#include <DRODLib/Db.h>
#include <BackEndLib/Files.h>

int temp()
{
    // == Setup fake home dir ==
    char fakeHome[] = "./fake_drod_home";
    mkdir(fakeHome, 0777);
    char fakeDataDir[] = "./fake_drod_home/Data";
    mkdir(fakeDataDir, 0777);
    // The file with DROD assets.
    char fakeDataFile[] = "./fake_drod_home/Data/drod5_0.dat";
    // Touch the file. For our purposes it only needs to exist,
    // not have any particular contents.
    std::ofstream output(fakeDataFile);
    // Point DROD to the fake home dir
    char fakeHomeEnv[] = "HOME=./fake_drod_home";
    putenv(fakeHomeEnv);

    // == Initialize file paths ==
    // Data file. Sometimes DROD creates this from drodName and drodVersion below instead.
    WSTRING dataFile;
    UTF8ToUnicode("drod5_0.dat", dataFile);
    // Writable data files, but not sure where they are used
    std::vector<string> datFiles;
    // Directories with extra assets, for modding. We don't need any here.
    std::vector<string> playerDataSubDirs;
    CFiles::InitAppVars(dataFile.c_str(), datFiles, playerDataSubDirs);
    // Fake path to the DROD executable, DROD will look for drod5_0.dat in Data/ next to this
    WSTRING fakeDrodPath;
    UTF8ToUnicode("./fake_drod_home/nonexistentdrod", fakeDrodPath);
    // Name of DROD, used to determine directory and data file name.
    WSTRING drodName;
    UTF8ToUnicode("drod", drodName);
    // Version of DROD, used to determine directory and data file name.
    WSTRING drodVersion;
    UTF8ToUnicode("5_0", drodVersion);
    // Singleton, needs to be constructed explicitly before DROD code can use it
    new CFiles(fakeDrodPath.c_str(), drodName.c_str(), drodVersion.c_str(), false, true, true);

    // == Initialize DB ==
    // Initialize db and assign to global pointer used in DROD code
    CDb *db = g_pTheDB = new CDb;
    db->Open();

    // == Initialize player profile ==
    CDbPlayer *player = db->Players.GetNew();
    player->NameText = u"";
    player->Update();
    db->Commit();

    // == Initialize hold ==
    CDbHold *hold = db->Holds.GetNew();
    hold->NameText = u"";
    hold->DescriptionText = u"";
    hold->Update();
    UINT holdID = hold->dwHoldID;

    // == Initialize level ==
    CDbLevel *level = db->Levels.GetNew();
    level->NameText = u"";
    level->dwHoldID = holdID;
    level->Update();
    hold->InsertLevel(level);
    UINT levelID = level->dwLevelID;

    // == Initialize room ==
    CDbRoom *room = db->Rooms.GetNew();
    room->dwLevelID = levelID;
    room->wRoomCols = 38;
    room->wRoomRows = 32;
    room->AllocTileLayers();
    const UINT dwSquareCount = room->CalcRoomArea();
    memset(room->pszOSquares, T_FLOOR, dwSquareCount * sizeof(char));
    memset(room->pszFSquares, T_EMPTY, dwSquareCount * sizeof(char));
    room->ClearTLayer();
    room->coveredOSquares.Init(38, 32);
    room->Update();
    UINT roomID = room->dwRoomID;
    delete room;
    room = db->Rooms.GetByID(roomID);

    // == Initialize entrance ==
    CEntranceData *pEntrance = new CEntranceData(0, 0, roomID,
                                                 15, 15,
                                                 SE, true, CEntranceData::DD_No, 0);
    hold->AddEntrance(pEntrance);
    hold->Update();

    // == Add some stuff to the room
    CMonster *monster = room->AddNewMonster(M_ROACH, 10, 10);
    monster->wO = N;
    room->Update();

    // == Initialize current game ==
    CCueEvents cueEvents;
    CCurrentGame *currentGame = db->GetNewCurrentGame(holdID, cueEvents);
    std::cout << "Beethro X: " << currentGame->swordsman.wX << std::endl;
    std::cout << "Roach X: " << currentGame->pRoom->GetMonsterOfType(M_ROACH)->wX << std::endl;

    // == Do something ==
    currentGame->ProcessCommand(CMD_SE, cueEvents);
    std::cout << "Beethro X: " << currentGame->swordsman.wX << std::endl;
    std::cout << "Roach X: " << currentGame->pRoom->GetMonsterOfType(M_ROACH)->wX << std::endl;

    return 0;
}

PYBIND11_MODULE(temp_module_name, m)
{
    m.doc() = "Just a module.";
    m.def("hello_world", &temp, "Print a hello");
}