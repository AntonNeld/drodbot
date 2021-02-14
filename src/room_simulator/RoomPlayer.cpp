
#include <fstream>
#include <sys/stat.h>
#include <string>

#include <BackEndLib/Files.h>
#include <DRODLib/CurrentGame.h>
#include <DRODLib/Db.h>

#include "RoomPlayer.h"
#include "typedefs.h"

// This class creates a room and plays it.
RoomPlayer::RoomPlayer()
{
}

// Initialize the RoomPlayer. This must be done before setting a room.
// Not part of the constructor since it has side effects on the filesystem.
void RoomPlayer::initialize()
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
    db = g_pTheDB = new CDb;
    db->Open();

    // == Initialize player profile ==
    CDbPlayer *player = db->Players.GetNew();
    player->NameText = u"";
    player->Update();
    db->Commit();

    // == Initialize hold ==
    hold = db->Holds.GetNew();
    hold->NameText = u"";
    hold->DescriptionText = u"";
    hold->Update();
    UINT holdID = hold->dwHoldID;

    // == Initialize level ==
    level = db->Levels.GetNew();
    level->NameText = u"";
    level->dwHoldID = holdID;
    level->Update();
    hold->InsertLevel(level);
}

// Set the room that is being played.
void RoomPlayer::setRoom(Room room)
{
    // Clear any existing room
    if (drodRoom != NULL)
    {
        db->Rooms.Delete(drodRoom->dwRoomID);
    }
    // Create new room
    drodRoom = db->Rooms.GetNew();
    drodRoom->dwLevelID = level->dwLevelID;
    drodRoom->wRoomCols = 38;
    drodRoom->wRoomRows = 32;
    drodRoom->AllocTileLayers();
    const UINT dwSquareCount = drodRoom->CalcRoomArea();
    memset(drodRoom->pszOSquares, T_FLOOR, dwSquareCount * sizeof(char));
    memset(drodRoom->pszFSquares, T_EMPTY, dwSquareCount * sizeof(char));
    drodRoom->ClearTLayer();
    drodRoom->coveredOSquares.Init(38, 32);
    drodRoom->Update();
    UINT roomID = drodRoom->dwRoomID;
    delete drodRoom;
    drodRoom = db->Rooms.GetByID(roomID);
    // Place things in room
    unsigned int beethroX;
    unsigned int beethroY;
    unsigned int beethroDir;
    switch (room)
    {
    case 0:
        beethroX = 15;
        beethroY = 15;
        beethroDir = SE;
        break;
    case 1:
        beethroX = 10;
        beethroY = 5;
        beethroDir = N;
        break;
    default:
        beethroX = 2;
        beethroY = 30;
        beethroDir = W;
    }
    CEntranceData *pEntrance = new CEntranceData(0, 0, drodRoom->dwRoomID,
                                                 beethroX, beethroY, beethroDir,
                                                 true, CEntranceData::DD_No, 0);
    hold->AddEntrance(pEntrance);
    hold->Update();
    CMonster *monster = drodRoom->AddNewMonster(M_ROACH, 10, 10);
    monster->wO = N;
    drodRoom->Update();
    // Start current game
    CCueEvents cueEvents;
    currentGame = db->GetNewCurrentGame(hold->dwHoldID, cueEvents);
}

// Perform an action in the room. Currently takes no arguments, but will take
// an action later.
void RoomPlayer::performAction(Action action)
{
    CCueEvents cueEvents;
    int drodAction;
    switch (action)
    {
    case Action::SW:
        drodAction = CMD_SW;
        break;
    case Action::S:
        drodAction = CMD_S;
        break;
    case Action::SE:
        drodAction = CMD_SE;
        break;
    case Action::W:
        drodAction = CMD_W;
        break;
    case Action::WAIT:
        drodAction = CMD_WAIT;
        break;
    case Action::E:
        drodAction = CMD_E;
        break;
    case Action::NW:
        drodAction = CMD_NW;
        break;
    case Action::N:
        drodAction = CMD_N;
        break;
    case Action::NE:
        drodAction = CMD_NE;
        break;
    case Action::CW:
        drodAction = CMD_C;
        break;
    case Action::CCW:
        drodAction = CMD_CC;
        break;
    default:
        throw std::invalid_argument("Unknown action");
    }
    currentGame->ProcessCommand(drodAction, cueEvents);
}

// Get a representation of the current room state. Currently only returns
// the player's X coordinate, but will return the full room later.
int RoomPlayer::getRoom()
{
    return currentGame->swordsman.wX;
}