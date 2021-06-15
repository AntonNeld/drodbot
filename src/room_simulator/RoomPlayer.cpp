#include <fstream>
#include <sys/stat.h>
#include <string>

#include <BackEndLib/Files.h>
#include <DRODLib/CurrentGame.h>
#include <DRODLib/Db.h>

#include "RoomPlayer.h"
#include "typedefs.h"
#include "Room.h"
#include "utils.h"

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
    if (this->claimed)
    {
        throw std::invalid_argument("Trying to use already claimed RoomPlayer");
    }
    this->claimed = true;
    this->closedDoors = {};
    // If the player starts with their sword on an orb and we are not
    // entering the room, the orb will have already been struck. Since
    // DRODLib will strike the orb again, we invert the status of the
    // doors that will be toggled by the orb. This makes the DROD room
    // match the function input. We don't need to care about the orb
    // opening and closing doors, since those actions are idempotent.
    std::set<Position> preToggledDoors = {};
    if (!firstEntrance)
    {
        std::tuple<Position, Direction> player = room.findPlayer();
        Position position = std::get<0>(player);
        Direction direction = std::get<1>(player);
        Position swordPos = positionInDirection(position, direction);
        int x = std::get<0>(swordPos);
        int y = std::get<1>(swordPos);
        if (x >= 0 && x < 38 && y >= 0 && y < 32)
        {
            Tile swordedTile = room.getTile(swordPos);
            if (swordedTile.item.type == ElementType::ORB)
            {
                OrbEffects effects = swordedTile.item.orbEffects;
                for (auto it = effects.begin(); it != effects.end(); ++it)
                {
                    OrbEffect effectType = std::get<2>(*it);
                    if (effectType == OrbEffect::TOGGLE)
                    {
                        int x = std::get<0>(*it);
                        int y = std::get<1>(*it);
                        std::set<Position> tiles = affectedDoorTiles({x, y}, room);
                        preToggledDoors.insert(tiles.begin(), tiles.end());
                    }
                }
            }
        }
    }
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
                if (preToggledDoors.find({x, y}) != preToggledDoors.end())
                {
                    drodRoom->Plot(x, y, T_DOOR_YO);
                }
                else
                {
                    drodRoom->Plot(x, y, T_DOOR_Y);
                }
                this->closedDoors[{x, y}] = true;
                break;
            case ElementType::YELLOW_DOOR_OPEN:
                if (preToggledDoors.find({x, y}) != preToggledDoors.end())
                {
                    drodRoom->Plot(x, y, T_DOOR_Y);
                }
                else
                {
                    drodRoom->Plot(x, y, T_DOOR_YO);
                }
                this->closedDoors[{x, y}] = false;
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
    this->currentGame = db->GetNewCurrentGame(hold->dwHoldID, cueEvents);

    this->baseRoom = room;
    this->actions = {};
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
    this->currentGame->ProcessCommand(drodAction, cueEvents);
    this->actions.push_back(action);
    for (auto it = this->closedDoors.begin(); it != this->closedDoors.end(); ++it)
    {
        Position key = std::get<0>(*it);
        int x = std::get<0>(key);
        int y = std::get<1>(key);
        UINT content = this->currentGame->pRoom->GetOSquare(x, y);
        if (content == T_DOOR_Y)
        {
            this->closedDoors[key] = true;
        }
        else if (content == T_DOOR_YO)
        {
            this->closedDoors[key] = false;
        }
        else
        {
            throw std::invalid_argument("Something has stopped being a door");
        }
    }
}

// Rewind an action
void RoomPlayer::undo()
{
    CCueEvents cueEvents;
    this->currentGame->UndoCommand(cueEvents);
    this->actions.pop_back();
}

// Set the actions performed from the base room, undoing if necessary
void RoomPlayer::setActions(std::vector<Action> newActions)
{
    long unsigned int divergingIndex = this->actions.size();
    for (long unsigned int i = 0; i < this->actions.size(); i++)
    {
        if (
            // If this is true, all the new actions are part of the old actions since
            // we haven't stopped yet. But the rest of the old actions
            // (including this) should be undone.
            i == newActions.size() ||
            // If this is true, we have reached the first diverging action. Undo this
            // and everything after.
            this->actions[i] != newActions[i])
        {
            divergingIndex = i;
            break;
        }
    }
    // Undo all old actions that are not part of the new actions
    long unsigned int timesToUndo = this->actions.size() - divergingIndex;
    for (long unsigned int i = 0; i < timesToUndo; i++)
    {
        this->undo();
    }
    // Perform the new actions after the point of divergence
    for (long unsigned int i = divergingIndex; i < newActions.size(); i++)
    {
        this->performAction(newActions[i]);
    }
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
    return Room(tiles, this->playerIsDead());
}

std::tuple<Position, Direction> RoomPlayer::findPlayer()
{
    return {{this->currentGame->swordsman.wX, this->currentGame->swordsman.wY},
            convertDirectionBack(this->currentGame->swordsman.wO)};
}

bool RoomPlayer::playerIsDead()
{
    return this->currentGame->IsPlayerDying();
}

std::set<Position> RoomPlayer::getToggledDoors()
{
    std::set<Position> toggledDoors = {};
    for (auto it = this->closedDoors.begin(); it != this->closedDoors.end(); ++it)
    {
        Position position = std::get<0>(*it);
        bool closed = std::get<1>(*it);
        Element element = this->baseRoom.value().getTile(position).roomPiece;
        switch (element.type)
        {
        case ElementType::YELLOW_DOOR:
            if (!closed)
            {
                toggledDoors.insert(position);
            }
            break;
        case ElementType::YELLOW_DOOR_OPEN:
            if (closed)
            {
                toggledDoors.insert(position);
            }
            break;
        default:
            throw std::invalid_argument("Tile not a door in the base room");
        }
    }
    return toggledDoors;
}

void RoomPlayer::release()
{
    if (!this->claimed)
    {
        throw std::invalid_argument("Trying to release unclaimed RoomPlayer");
    }
    this->claimed = false;
}

// Since a lot of things in the DROD code is global, we'll need the interface
// toward it to be global too
RoomPlayer globalRoomPlayer = RoomPlayer();
void initGlobalRoomPlayer()
{
    globalRoomPlayer.initialize();
}