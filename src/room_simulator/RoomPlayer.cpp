#include <fstream>
#include <sys/stat.h>
#include <string>
#include <optional>

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

ElementType convertMonsterBack(UINT monster)
{
    switch (monster)
    {
    case M_ROACH:
        return ElementType::ROACH;
    case M_QROACH:
        return ElementType::ROACH_QUEEN;
    case M_REGG:
        return ElementType::ROACH_EGG;
    case M_EYE:
        return ElementType::EVIL_EYE;
    case M_EYE_ACTIVE:
        return ElementType::EVIL_EYE_AWAKE;
    case M_WWING:
        return ElementType::WRAITHWING;
    case M_SPIDER:
        return ElementType::SPIDER;
    case M_GOBLIN:
        return ElementType::GOBLIN;
    case M_TARBABY:
        return ElementType::TAR_BABY;
    case M_BRAIN:
        return ElementType::BRAIN;
    case M_MIMIC:
        return ElementType::MIMIC;
    default:
        throw std::invalid_argument("Unknown monster type");
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

std::optional<CDb *> globalDb;
std::optional<CDbHold *> globalHold;
std::optional<CDbLevel *> globalLevel;

void initRoomPlayerRequirements()
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
    // Initialize globalDb and assign to global pointer used in DROD code
    globalDb = g_pTheDB = new CDb;
    globalDb.value()->Open();

    // == Initialize player profile ==
    CDbPlayer *player = globalDb.value()->Players.GetNew();
    player->NameText = u"";
    player->Update();
    globalDb.value()->Commit();

    // == Initialize globalHold ==
    globalHold = globalDb.value()->Holds.GetNew();
    globalHold.value()->NameText = u"";
    globalHold.value()->DescriptionText = u"";
    globalHold.value()->Update();
    UINT holdID = globalHold.value()->dwHoldID;

    // == Initialize globalLevel ==
    globalLevel = globalDb.value()->Levels.GetNew();
    globalLevel.value()->NameText = u"";
    globalLevel.value()->dwHoldID = holdID;
    globalLevel.value()->Update();
    globalHold.value()->InsertLevel(globalLevel.value());

    // == Restore home dir ==
    setenv("HOME", oldHomeEnv, 1);

    // == Create a dummy required room, to get correct blue door state
    CDbRoom *requiredRoom = globalDb.value()->Rooms.GetNew();
    requiredRoom->bIsRequired = true;
    requiredRoom->dwLevelID = globalLevel.value()->dwLevelID;
    requiredRoom->wRoomCols = 38;
    requiredRoom->wRoomRows = 32;
    requiredRoom->AllocTileLayers();
    const UINT dwSquareCount = requiredRoom->CalcRoomArea();
    memset(requiredRoom->pszOSquares, T_FLOOR, dwSquareCount * sizeof(char));
    memset(requiredRoom->pszFSquares, T_EMPTY, dwSquareCount * sizeof(char));
    requiredRoom->ClearTLayer();
    requiredRoom->coveredOSquares.Init(38, 32);
    requiredRoom->Update();
    // UINT roomID = requiredRoom->dwRoomID;
    delete requiredRoom;
    // requiredRoom = globalDb.value()->Rooms.GetByID(roomID);
}

// This class creates a room and plays it.
RoomPlayer::RoomPlayer(Room room, bool firstEntrance) : drodRoom(globalDb.value()->Rooms.GetNew()),
                                                        currentGame(NULL),
                                                        baseRoom(room),
                                                        actions({}),
                                                        doors({})
{
    // Map from turnorder to monster
    std::map<int, std::tuple<ElementType, Position, Direction>> monsters = {};
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
                        std::set<Position> tiles = floodFill({x, y}, room);
                        preToggledDoors.insert(tiles.begin(), tiles.end());
                    }
                }
            }
        }
    }
    this->drodRoom->dwLevelID = globalLevel.value()->dwLevelID;
    this->drodRoom->wRoomCols = 38;
    this->drodRoom->wRoomRows = 32;
    this->drodRoom->AllocTileLayers();
    const UINT dwSquareCount = this->drodRoom->CalcRoomArea();
    memset(this->drodRoom->pszOSquares, T_FLOOR, dwSquareCount * sizeof(char));
    memset(this->drodRoom->pszFSquares, T_EMPTY, dwSquareCount * sizeof(char));
    this->drodRoom->ClearTLayer();
    this->drodRoom->coveredOSquares.Init(38, 32);
    this->drodRoom->Update();
    UINT roomID = this->drodRoom->dwRoomID;
    delete this->drodRoom;
    this->drodRoom = globalDb.value()->Rooms.GetByID(roomID);

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
                this->drodRoom->Plot(x, y, T_WALL);
                break;
            case ElementType::PIT:
                this->drodRoom->Plot(x, y, T_PIT);
                break;
            case ElementType::MASTER_WALL:
                this->drodRoom->Plot(x, y, T_WALL_M);
                break;
            case ElementType::TRAPDOOR:
                this->drodRoom->Plot(x, y, T_TRAPDOOR);
                break;
            case ElementType::YELLOW_DOOR:
                if (preToggledDoors.find({x, y}) != preToggledDoors.end())
                {
                    this->drodRoom->Plot(x, y, T_DOOR_YO);
                }
                else
                {
                    this->drodRoom->Plot(x, y, T_DOOR_Y);
                }
                this->doors.insert({x, y});
                break;
            case ElementType::YELLOW_DOOR_OPEN:
                if (preToggledDoors.find({x, y}) != preToggledDoors.end())
                {
                    this->drodRoom->Plot(x, y, T_DOOR_Y);
                }
                else
                {
                    this->drodRoom->Plot(x, y, T_DOOR_YO);
                }
                this->doors.insert({x, y});
                break;
            case ElementType::GREEN_DOOR:
                if (room.isConquered())
                {
                    this->drodRoom->Plot(x, y, T_DOOR_GO);
                }
                else
                {
                    this->drodRoom->Plot(x, y, T_DOOR_M);
                }
                break;
            case ElementType::GREEN_DOOR_OPEN:
                if (room.isConquered())
                {
                    this->drodRoom->Plot(x, y, T_DOOR_M);
                }
                else
                {
                    this->drodRoom->Plot(x, y, T_DOOR_GO);
                }
                break;
            case ElementType::BLUE_DOOR:
                this->drodRoom->Plot(x, y, T_DOOR_C);
                break;
            case ElementType::BLUE_DOOR_OPEN:
                this->drodRoom->Plot(x, y, T_DOOR_CO);
                break;
            // TODO: Check whether room has trapdoors and toggle doors if appropriate
            case ElementType::RED_DOOR:
                this->drodRoom->Plot(x, y, T_DOOR_R);
                break;
            case ElementType::RED_DOOR_OPEN:
                this->drodRoom->Plot(x, y, T_DOOR_RO);
                break;
            case ElementType::STAIRS:
                this->drodRoom->Plot(x, y, T_STAIRS);
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
                    this->drodRoom->Plot(x, y, T_ARROW_N);
                    break;
                case Direction::NE:
                    this->drodRoom->Plot(x, y, T_ARROW_NE);
                    break;
                case Direction::E:
                    this->drodRoom->Plot(x, y, T_ARROW_E);
                    break;
                case Direction::SE:
                    this->drodRoom->Plot(x, y, T_ARROW_SE);
                    break;
                case Direction::S:
                    this->drodRoom->Plot(x, y, T_ARROW_S);
                    break;
                case Direction::SW:
                    this->drodRoom->Plot(x, y, T_ARROW_SW);
                    break;
                case Direction::W:
                    this->drodRoom->Plot(x, y, T_ARROW_W);
                    break;
                case Direction::NW:
                    this->drodRoom->Plot(x, y, T_ARROW_NW);
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
                this->drodRoom->Plot(x, y, T_ORB);
                COrbData *orb = this->drodRoom->AddOrbToSquare(x, y);
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
                this->drodRoom->Plot(x, y, T_OBSTACLE);
                break;
            case ElementType::MIMIC_POTION:
                this->drodRoom->Plot(x, y, T_POTION_K);
                break;
            case ElementType::INVISIBILITY_POTION:
                this->drodRoom->Plot(x, y, T_POTION_I);
                break;
            case ElementType::SCROLL:
                this->drodRoom->Plot(x, y, T_SCROLL);
                break;
            case ElementType::CONQUER_TOKEN:
                this->drodRoom->Plot(x, y, T_TOKEN);
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
                CEntranceData *pEntrance = new CEntranceData(0, 0, this->drodRoom->dwRoomID,
                                                             x, y, convertDirection(tile.monster.direction),
                                                             true, CEntranceData::DD_No, 0);
                globalHold.value()->AddEntrance(pEntrance);
                globalHold.value()->Update();
                break;
            }
            default:
                monsters[tile.monster.turnOrder.value()] = {tile.monster.type,
                                                            {x, y},
                                                            tile.monster.direction};
            }
        }
    }
    // This relies on monsters being sorted by turn order
    for (auto it = monsters.begin(); it != monsters.end(); ++it)
    {
        ElementType type = std::get<0>(std::get<1>(*it));
        Position position = std::get<1>(std::get<1>(*it));
        Direction direction = std::get<2>(std::get<1>(*it));
        int x = std::get<0>(position);
        int y = std::get<1>(position);
        switch (type)
        {
        case ElementType::ROACH:
            this->drodRoom->AddNewMonster(M_ROACH, x, y)->wO = convertDirection(direction);
            break;
        case ElementType::ROACH_QUEEN:
            this->drodRoom->AddNewMonster(M_QROACH, x, y)->wO = convertDirection(direction);
            break;
        case ElementType::ROACH_EGG:
            throw std::invalid_argument("Cannot start room with roach egg");
        case ElementType::EVIL_EYE:
            this->drodRoom->AddNewMonster(M_EYE, x, y)->wO = convertDirection(direction);
            break;
        case ElementType::EVIL_EYE_AWAKE:
            this->drodRoom->AddNewMonster(M_EYE_ACTIVE, x, y)->wO = convertDirection(direction);
            break;
        case ElementType::WRAITHWING:
            this->drodRoom->AddNewMonster(M_WWING, x, y)->wO = convertDirection(direction);
            break;
        case ElementType::SPIDER:
            this->drodRoom->AddNewMonster(M_SPIDER, x, y)->wO = convertDirection(direction);
            break;
        case ElementType::GOBLIN:
            this->drodRoom->AddNewMonster(M_GOBLIN, x, y)->wO = convertDirection(direction);
            break;
        case ElementType::TAR_BABY:
            this->drodRoom->AddNewMonster(M_TARBABY, x, y)->wO = convertDirection(direction);
            break;
        case ElementType::BRAIN:
            this->drodRoom->AddNewMonster(M_BRAIN, x, y);
            break;
        case ElementType::MIMIC:
            this->drodRoom->AddNewMonster(M_MIMIC, x, y)->wO = convertDirection(direction);
            break;
        default:
            throw std::invalid_argument("Wrong type in monster layer");
        }
    }
    this->drodRoom->Update();
    // Start current game
    CCueEvents cueEvents;
    this->currentGame = globalDb.value()->GetNewCurrentGame(globalHold.value()->dwHoldID, cueEvents);
    // Take snapshots more often, since we reset the counter by undoing all the time
    this->currentGame->SetComputationTimePerSnapshot(100);
};

RoomPlayer::~RoomPlayer()
{
    globalDb.value()->Rooms.Delete(this->drodRoom->dwRoomID);
    delete this->drodRoom;
    delete this->currentGame;
}

std::vector<Action> RoomPlayer::getPossibleActions()
{
    if (this->playerIsDead() || this->playerHasLeft())
    {
        return {};
    }
    Position playerPosition = std::get<0>(this->findPlayer());
    std::vector<std::pair<Action, Direction>> movementActions = {
        {Action::N, Direction::N},
        {Action::NE, Direction::NE},
        {Action::E, Direction::E},
        {Action::SE, Direction::SE},
        {Action::S, Direction::S},
        {Action::SW, Direction::SW},
        {Action::W, Direction::W},
        {Action::NW, Direction::NW},
    };
    std::vector<Action> actions = {Action::WAIT, Action::CW, Action::CCW};
    // Don't add movement actions that will bump into things, they are equivalent to waiting.
    for (auto it = movementActions.begin(); it != movementActions.end(); ++it)
    {
        Direction direction = (*it).second;
        if (this->isPassableInDirection(positionInDirection(playerPosition, direction), direction))
        {
            actions.push_back((*it).first);
        }
    }
    return actions;
}

bool RoomPlayer::isPassableInDirection(Position position, Direction moveDirection)
{
    unsigned int x = std::get<0>(position);
    unsigned int y = std::get<1>(position);
    if (x < 0 || x >= 38 || y < 0 || y >= 32)
    {
        return false;
    }
    bool ignored;
    return !this->currentGame->pRoom->DoesSquareContainPlayerObstacle(x, y, convertDirection(moveDirection), ignored);
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
}

// Rewind an action
void RoomPlayer::undo(unsigned long int turns)
{
    if (turns == 0)
    {
        return;
    }
    CCueEvents cueEvents;
    this->currentGame->UndoCommands(turns, cueEvents);
    auto end = this->actions.end();
    auto firstToErase = end - turns;
    this->actions.erase(firstToErase, end);
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
    unsigned long int timesToUndo = this->actions.size() - divergingIndex;
    this->undo(timesToUndo);
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
            switch (this->currentGame->pRoom->GetOSquare(x, y))
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
            // TODO: These may be switched depending on whether the room is
            // conquered. Investigate.
            case T_DOOR_R:
                roomPiece = Element(ElementType::RED_DOOR);
                break;
            case T_DOOR_RO:
                roomPiece = Element(ElementType::RED_DOOR_OPEN);
                break;
            case T_STAIRS:
                roomPiece = Element(ElementType::STAIRS);
                break;
            case T_TRAPDOOR:
                roomPiece = Element(ElementType::TRAPDOOR);
                break;
            default:
                throw std::invalid_argument("Unknown element in room piece layer");
            }
            tile.roomPiece = roomPiece;

            Element floorControl;
            switch (this->currentGame->pRoom->GetFSquare(x, y))
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
            switch (this->currentGame->pRoom->GetTSquare(x, y))
            {
            case T_EMPTY:
                floorControl = Element();
                break;
            case T_ORB:
            {
                OrbEffects orbEffects;
                COrbData *orb = this->currentGame->pRoom->GetOrbAtCoords(x, y);
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
            case T_POTION_K:
                item = Element(ElementType::MIMIC_POTION);
                break;
            case T_POTION_I:
                item = Element(ElementType::INVISIBILITY_POTION);
                break;
            default:
                throw std::invalid_argument("Unknown element in item layer");
            }
            tile.item = item;

            tiles[x][y] = tile;
        }
    }
    // Add monsters
    Element player = Element(ElementType::BEETHRO, convertDirectionBack(this->currentGame->swordsman.wO));
    tiles[this->currentGame->swordsman.wX][this->currentGame->swordsman.wY].monster = player;
    int turnOrder = 0;
    for (auto it = this->currentGame->pRoom->pFirstMonster; it != NULL; it = it->pNext)
    {
        ElementType type = convertMonsterBack(it->wType);
        Direction direction;
        if (type == ElementType::BRAIN || type == ElementType::ROACH_EGG)
        {
            direction = Direction::NONE;
        }
        else
        {
            direction = convertDirectionBack(it->wO);
        }
        tiles[it->wX][it->wY].monster = Element(type, direction, {}, turnOrder);
        turnOrder++;
    }
    return Room(tiles);
}

DerivedRoom RoomPlayer::getDerivedRoom()
{
    return DerivedRoom(this->actions,
                       this->findPlayer(),
                       this->getToggledDoors(),
                       this->playerIsDead(),
                       this->playerHasLeft(),
                       this->getMonsters());
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

bool RoomPlayer::playerHasLeft()
{
    return this->currentGame->bIsLeavingLevel;
}

std::set<Position> RoomPlayer::getToggledDoors()
{
    std::set<Position> toggledDoors = {};
    for (auto it = this->doors.begin(); it != this->doors.end(); ++it)
    {
        Position position = *it;
        int x = std::get<0>(position);
        int y = std::get<1>(position);
        UINT content = this->currentGame->pRoom->GetOSquare(x, y);
        ElementType baseDoorType = this->baseRoom.getTile(position).roomPiece.type;
        if ((content == T_DOOR_Y && baseDoorType == ElementType::YELLOW_DOOR_OPEN) ||
            (content == T_DOOR_YO && baseDoorType == ElementType::YELLOW_DOOR))
        {
            toggledDoors.insert(position);
        }
    }
    return toggledDoors;
}

std::vector<std::tuple<ElementType, Position, Direction>> RoomPlayer::getMonsters()
{
    std::vector<std::tuple<ElementType, Position, Direction>> monsters = {};
    for (auto it = this->currentGame->pRoom->pFirstMonster; it != NULL; it = it->pNext)
    {
        ElementType type = convertMonsterBack(it->wType);
        Position position = {it->wX, it->wY};
        Direction direction;
        if (type == ElementType::BRAIN || type == ElementType::ROACH_EGG)
        {
            direction = Direction::NONE;
        }
        else
        {
            direction = convertDirectionBack(it->wO);
        }
        monsters.push_back({type, position, direction});
    }
    return monsters;
}
