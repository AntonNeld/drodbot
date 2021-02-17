
#include <fstream>
#include <sys/stat.h>
#include <string>

#include <BackEndLib/Files.h>
#include <DRODLib/CurrentGame.h>
#include <DRODLib/Db.h>

#include "RoomPlayer.h"
#include "typedefs.h"

// Helper function to convert directions.
UINT convertDirection(Direction direction)
{
    switch (direction)
    {
    case Direction::N:
        return N;
    case Direction::NE:
        return NE;
    case Direction::E:
        return E;
    case Direction::SE:
        return SE;
    case Direction::S:
        return S;
    case Direction::SW:
        return SW;
    case Direction::W:
        return W;
    case Direction::NW:
        return NW;
    default:
        throw std::invalid_argument("Unknown direction");
    }
}

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
    // The file with DROD assets
    char fakeDataFile[] = "./fake_drod_home/Data/drod5_0.dat";
    // Touch the file. For our purposes it only needs to exist,
    // not have any particular contents.
    std::ofstream output(fakeDataFile);
    // Get the current HOME environment variable, so we can restore it later
    char *oldHomeEnv = getenv("HOME");
    // Point DROD to the fake home dir
    setenv("HOME", "./fake_drod_home", 1);

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

    // == Restore home dir ==
    setenv("HOME", oldHomeEnv, 1);
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
    for (unsigned int x = 0; x < room.size(); x += 1)
    {
        Column column = room[x];
        for (unsigned int y = 0; y < column.size(); y += 1)
        {
            Tile &tile = column[y];
            switch (tile.roomPiece.type)
            {
            case ElementType::FLOOR:
                break;
            case ElementType::WALL:
                drodRoom->Plot(x, y, T_WALL);
                break;
            case ElementType::PIT:
                drodRoom->Plot(x, y, T_PIT);
                break;
            case ElementType::MASTER_WALL:
                drodRoom->Plot(x, y, T_WALL_M);
                break;
            case ElementType::YELLOW_DOOR:
                drodRoom->Plot(x, y, T_DOOR_Y);
                break;
            case ElementType::YELLOW_DOOR_OPEN:
                drodRoom->Plot(x, y, T_DOOR_YO);
                break;
            // TODO: These may be switched depending on whether the room is
            // conquered. Investigate.
            case ElementType::GREEN_DOOR:
                drodRoom->Plot(x, y, T_DOOR_M);
                break;
            case ElementType::GREEN_DOOR_OPEN:
                drodRoom->Plot(x, y, T_DOOR_GO);
                break;
            case ElementType::BLUE_DOOR:
                drodRoom->Plot(x, y, T_DOOR_C);
                break;
            case ElementType::BLUE_DOOR_OPEN:
                drodRoom->Plot(x, y, T_DOOR_CO);
                break;
            case ElementType::STAIRS:
                drodRoom->Plot(x, y, T_STAIRS);
                break;
            default:
                throw std::invalid_argument("Wrong type in room piece layer");
            }

            switch (tile.floorControl.type)
            {
            case ElementType::NOTHING:
                break;
            case ElementType::FORCE_ARROW:
                switch (tile.floorControl.direction)
                {
                case Direction::N:
                    drodRoom->Plot(x, y, T_ARROW_N);
                    break;
                case Direction::NE:
                    drodRoom->Plot(x, y, T_ARROW_NE);
                    break;
                case Direction::E:
                    drodRoom->Plot(x, y, T_ARROW_E);
                    break;
                case Direction::SE:
                    drodRoom->Plot(x, y, T_ARROW_SE);
                    break;
                case Direction::S:
                    drodRoom->Plot(x, y, T_ARROW_S);
                    break;
                case Direction::SW:
                    drodRoom->Plot(x, y, T_ARROW_SW);
                    break;
                case Direction::W:
                    drodRoom->Plot(x, y, T_ARROW_W);
                    break;
                case Direction::NW:
                    drodRoom->Plot(x, y, T_ARROW_NW);
                    break;
                default:
                    throw std::invalid_argument("Wrong force arrow direction");
                }
                break;
            default:
                throw std::invalid_argument("Wrong type in floor control layer");
            }

            switch (tile.checkpoint.type)
            {
            case ElementType::NOTHING:
                break;
            case ElementType::CHECKPOINT:
                // T_CHECKPOINT is deprecated, but we may as well use it to keep
                // track of where the checkpoints are
                drodRoom->Plot(x, y, T_CHECKPOINT);
                break;
            default:
                throw std::invalid_argument("Wrong type in checkpoint layer");
            }

            switch (tile.item.type)
            {
            case ElementType::NOTHING:
                break;
            case ElementType::ORB:
                drodRoom->Plot(x, y, T_ORB);
                break;
            case ElementType::OBSTACLE:
                drodRoom->Plot(x, y, T_OBSTACLE);
                break;
            case ElementType::SCROLL:
                drodRoom->Plot(x, y, T_SCROLL);
                break;
            case ElementType::CONQUER_TOKEN:
                drodRoom->Plot(x, y, T_TOKEN);
                break;
            default:
                throw std::invalid_argument("Wrong type in item layer");
            }

            switch (tile.monster.type)
            {
            case ElementType::NOTHING:
                break;
            case ElementType::BEETHRO:
            {
                CEntranceData *pEntrance = new CEntranceData(0, 0, drodRoom->dwRoomID,
                                                             x, y, convertDirection(tile.monster.direction),
                                                             true, CEntranceData::DD_No, 0);
                hold->AddEntrance(pEntrance);
                hold->Update();
                break;
            }
            case ElementType::ROACH:
                drodRoom->AddNewMonster(M_ROACH, x, y)->wO = convertDirection(tile.monster.direction);
                break;
            default:
                throw std::invalid_argument("Wrong type in monster layer");
            }
        }
    }
    drodRoom->Update();

    // Start current game
    CCueEvents cueEvents;
    currentGame = db->GetNewCurrentGame(hold->dwHoldID, cueEvents);
}

// Perform an action in the room.
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