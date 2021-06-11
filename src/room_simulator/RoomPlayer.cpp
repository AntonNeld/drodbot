
#include <fstream>
#include <sys/stat.h>
#include <string>

#include <BackEndLib/Files.h>
#include <DRODLib/CurrentGame.h>
#include <DRODLib/Db.h>

#include "RoomPlayer.h"
#include "typedefs.h"
#include "Room.h"

// Helper function to convert direction from our format to DROD format.
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

// Helper function to convert direction from DROD format to our format.
Direction convertDirectionBack(UINT direction)
{
    switch (direction)
    {
    case N:
        return Direction::N;
    case NE:
        return Direction::NE;
    case E:
        return Direction::E;
    case SE:
        return Direction::SE;
    case S:
        return Direction::S;
    case SW:
        return Direction::SW;
    case W:
        return Direction::W;
    case NW:
        return Direction::NW;
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

    // == Create a dummy required room, to get correct blue door state
    requiredRoom = db->Rooms.GetNew();
    requiredRoom->bIsRequired = true;
    requiredRoom->dwLevelID = level->dwLevelID;
    requiredRoom->wRoomCols = 38;
    requiredRoom->wRoomRows = 32;
    requiredRoom->AllocTileLayers();
    const UINT dwSquareCount = requiredRoom->CalcRoomArea();
    memset(requiredRoom->pszOSquares, T_FLOOR, dwSquareCount * sizeof(char));
    memset(requiredRoom->pszFSquares, T_EMPTY, dwSquareCount * sizeof(char));
    requiredRoom->ClearTLayer();
    requiredRoom->coveredOSquares.Init(38, 32);
    requiredRoom->Update();
    UINT roomID = requiredRoom->dwRoomID;
    delete requiredRoom;
    requiredRoom = db->Rooms.GetByID(roomID);
}

// Set the room that is being played.
void RoomPlayer::setRoom(
    Room room,         // Representation of the room
    bool firstEntrance // Whether we're first entering the room or
                       // whether it's a room in progress. If false,
                       // apply some workarounds to undo things that
                       // happen when entering a room.
)
{
    // Clear any existing room
    if (drodRoom != NULL)
    {
        db->Rooms.Delete(drodRoom->dwRoomID);
        delete drodRoom;
        delete currentGame;
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

    // Optionally wait with placing the doors until after starting playing. This
    // is because Beethro strikes orbs when first entering a room, which is
    // undesirable if we're actually in the middle of playing the given room.
    std::vector<std::pair<int, int>> closedDoors;
    std::vector<std::pair<int, int>> openDoors;

    for (int x = 0; x < 38; x += 1)
    {
        for (int y = 0; y < 32; y += 1)
        {
            Tile tile = room.getTile(std::make_tuple(x, y));
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
                if (firstEntrance)
                {
                    drodRoom->Plot(x, y, T_DOOR_Y);
                }
                else
                {
                    closedDoors.push_back({x, y});
                }
                break;
            case ElementType::YELLOW_DOOR_OPEN:
                if (firstEntrance)
                {
                    drodRoom->Plot(x, y, T_DOOR_YO);
                }
                else
                {
                    openDoors.push_back({x, y});
                }
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

            // TODO: Keep track of checkpoints

            switch (tile.item.type)
            {
            case ElementType::NOTHING:
                break;
            case ElementType::ORB:
            {
                drodRoom->Plot(x, y, T_ORB);
                COrbData *orb = drodRoom->AddOrbToSquare(x, y);
                for (unsigned int i = 0; i < tile.item.orbEffects.size(); i += 1)
                {
                    std::tuple<int, int, OrbEffect> effectTuple = tile.item.orbEffects[i];
                    int doorX = std::get<0>(effectTuple);
                    int doorY = std::get<1>(effectTuple);
                    OrbAgentType doorAction;
                    switch (std::get<2>(effectTuple))
                    {
                    case OrbEffect::CLOSE:
                        doorAction = OA_CLOSE;
                        break;
                    case OrbEffect::OPEN:
                        doorAction = OA_OPEN;
                        break;
                    case OrbEffect::TOGGLE:
                        doorAction = OA_TOGGLE;
                        break;
                    default:
                        throw std::invalid_argument("Wrong orb effect type");
                    }
                    orb->AddAgent(doorX, doorY, doorAction);
                }
                break;
            }
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

    if (!firstEntrance)
    {
        for (unsigned int i = 0; i < closedDoors.size(); i += 1)
        {
            int x = closedDoors[i].first;
            int y = closedDoors[i].second;
            currentGame->pRoom->Plot(x, y, T_DOOR_Y);
        }
        for (unsigned int i = 0; i < openDoors.size(); i += 1)
        {
            int x = openDoors[i].first;
            int y = openDoors[i].second;
            currentGame->pRoom->Plot(x, y, T_DOOR_YO);
        }
    }
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

// Get a representation of the current room state.
Room RoomPlayer::getRoom()
{
    Tiles tiles;
    for (unsigned int x = 0; x < 38; x += 1)
    {
        for (unsigned int y = 0; y < 32; y += 1)
        {
            Tile tile;
            Element roomPiece;
            switch (currentGame->pRoom->GetOSquare(x, y))
            {
            case T_FLOOR:
                roomPiece = Element(ElementType::FLOOR);
                break;
            case T_WALL:
                roomPiece = Element(ElementType::WALL);
                break;
            case T_PIT:
                roomPiece = Element(ElementType::PIT);
                break;
            case T_WALL_M:
                roomPiece = Element(ElementType::MASTER_WALL);
                break;
            case T_DOOR_Y:
                roomPiece = Element(ElementType::YELLOW_DOOR);
                break;
            case T_DOOR_YO:
                roomPiece = Element(ElementType::YELLOW_DOOR_OPEN);
                break;
            // TODO: These may be switched depending on whether the room is
            // conquered. Investigate.
            case T_DOOR_M:
                roomPiece = Element(ElementType::GREEN_DOOR);
                break;
            case T_DOOR_GO:
                roomPiece = Element(ElementType::GREEN_DOOR_OPEN);
                break;
            case T_DOOR_C:
                roomPiece = Element(ElementType::BLUE_DOOR);
                break;
            case T_DOOR_CO:
                roomPiece = Element(ElementType::BLUE_DOOR_OPEN);
                break;
            case T_STAIRS:
                roomPiece = Element(ElementType::STAIRS);
                break;
            default:
                throw std::invalid_argument("Unknown element in room piece layer");
            }
            tile.roomPiece = roomPiece;

            Element floorControl;
            switch (currentGame->pRoom->GetFSquare(x, y))
            {
            case T_EMPTY:
                floorControl = Element();
                break;
            case T_ARROW_N:
                floorControl = Element(ElementType::FORCE_ARROW, Direction::N);
                break;
            case T_ARROW_NE:
                floorControl = Element(ElementType::FORCE_ARROW, Direction::NE);
                break;
            case T_ARROW_E:
                floorControl = Element(ElementType::FORCE_ARROW, Direction::E);
                break;
            case T_ARROW_SE:
                floorControl = Element(ElementType::FORCE_ARROW, Direction::SE);
                break;
            case T_ARROW_S:
                floorControl = Element(ElementType::FORCE_ARROW, Direction::S);
                break;
            case T_ARROW_SW:
                floorControl = Element(ElementType::FORCE_ARROW, Direction::SW);
                break;
            case T_ARROW_W:
                floorControl = Element(ElementType::FORCE_ARROW, Direction::W);
                break;
            case T_ARROW_NW:
                floorControl = Element(ElementType::FORCE_ARROW, Direction::NW);
                break;
            default:
                throw std::invalid_argument("Unknown element in floor control layer");
            }
            tile.floorControl = floorControl;

            // TODO: Keep track of checkpoints
            tile.checkpoint = Element();

            Element item;
            switch (currentGame->pRoom->GetTSquare(x, y))
            {
            case T_EMPTY:
                floorControl = Element();
                break;
            case T_ORB:
            {
                OrbEffects orbEffects;
                COrbData *orb = currentGame->pRoom->GetOrbAtCoords(x, y);
                for (unsigned int i = 0; i < orb->agents.size(); i += 1)
                {
                    COrbAgentData *agent = orb->agents[i];
                    switch (agent->action)
                    {
                    case OA_CLOSE:
                        orbEffects.push_back(std::make_tuple(agent->wX, agent->wY, OrbEffect::CLOSE));
                        break;
                    case OA_OPEN:
                        orbEffects.push_back(std::make_tuple(agent->wX, agent->wY, OrbEffect::OPEN));
                        break;
                    case OA_TOGGLE:
                        orbEffects.push_back(std::make_tuple(agent->wX, agent->wY, OrbEffect::TOGGLE));
                        break;
                    default:
                        throw std::invalid_argument("Unknown orb effect");
                    }
                }
                item = Element(ElementType::ORB, Direction::NONE, orbEffects);
                break;
            }
            case T_OBSTACLE:
                item = Element(ElementType::OBSTACLE);
                break;
            case T_SCROLL:
                item = Element(ElementType::SCROLL);
                break;
            case T_TOKEN:
                item = Element(ElementType::CONQUER_TOKEN);
                break;
            default:
                throw std::invalid_argument("Unknown element in item layer");
            }
            tile.item = item;

            Element monster;
            if (currentGame->swordsman.wX == x && currentGame->swordsman.wY == y)
            {
                monster = Element(ElementType::BEETHRO, convertDirectionBack(currentGame->swordsman.wO));
            }
            else
            {
                CMonster *pMonster = currentGame->pRoom->GetMonsterAtSquare(x, y);
                if (pMonster == NULL)
                {
                    monster = Element();
                }
                else
                {
                    switch (pMonster->wType)
                    {
                    case M_ROACH:
                        monster = Element(ElementType::ROACH, convertDirectionBack(pMonster->wO));
                        break;
                    default:
                        throw std::invalid_argument("Wrong type in monster layer");
                    }
                }
            }
            tile.monster = monster;

            tiles[x][y] = tile;
        }
    }
    return Room(tiles);
}

// Since a lot of things in the DROD code is global, we'll need the interface
// toward it to be global too
RoomPlayer globalRoomPlayer = RoomPlayer();
void initGlobalRoomPlayer()
{
    globalRoomPlayer.initialize();
}