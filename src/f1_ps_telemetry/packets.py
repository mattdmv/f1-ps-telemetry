"""F1 22 UDP Telemetry support package

This package is based on the CodeMasters Forum post documenting the F1 22 packet format:

    https://answers.ea.com/t5/General-Discussion/F1-22-UDP-Specification/td-p/11551274
"""

import ctypes
import enum

#########################################################
#                                                       #
#  __________  PackedLittleEndianStructure  __________  #
#                                                       #
#########################################################


class PackedLittleEndianStructure(ctypes.LittleEndianStructure):
    """The standard ctypes LittleEndianStructure, but tightly packed (no field padding), and with a proper repr() function.

    This is the base type for all structures in the telemetry data.
    """

    _pack_ = 1

    def __repr__(self):
        fstr_list = []
        for (fname, ftype) in self._fields_:
            value = getattr(self, fname)
            if isinstance(value, (PackedLittleEndianStructure, int, float, bytes)):
                vstr = repr(value)
            elif isinstance(value, ctypes.Array):
                vstr = "[{}]".format(", ".join(repr(e) for e in value))
            else:
                raise RuntimeError(
                    "Bad value {!r} of type {!r}".format(value, type(value))
                )
            fstr = "{}={}".format(fname, vstr)
            fstr_list.append(fstr)
        return "{}({})".format(self.__class__.__name__, ", ".join(fstr_list))


###########################################
#                                         #
#  __________  Packet Header  __________  #
#                                         #
###########################################


class PacketHeader(PackedLittleEndianStructure):
    """The header for each of the UDP telemetry packets."""

    _fields_ = [
        ("packetFormat", ctypes.c_uint16),  # 2022
        ("gameMajorVersion", ctypes.c_uint8),  # Game major version - "X.00"
        ("gameMinorVersion", ctypes.c_uint8),  # Game minor version - "1.XX"
        (
            "packetVersion",
            ctypes.c_uint8,
        ),  # Version of this packet type, all start from 1
        ("packetId", ctypes.c_uint8),  # Identifier for the packet type, see below
        ("sessionUID", ctypes.c_uint64),  # Unique identifier for the session
        ("sessionTime", ctypes.c_float),  # Session timestamp
        (
            "frameIdentifier",
            ctypes.c_uint32,
        ),  # Identifier for the frame the data was retrieved on
        ("playerCarIndex", ctypes.c_uint8),  # Index of player's car in the array
        (
            "secondaryPlayerCarIndex",
            ctypes.c_uint8,
        )  # Index of secondary player's car in the array (splitscreen)
        # 255 if no second player
    ]


@enum.unique
class PacketID(enum.IntEnum):
    """Value as specified in the PacketHeader.packetId header field, used to distinguish packet types."""

    MOTION = 0
    SESSION = 1
    LAP_DATA = 2
    EVENT = 3
    PARTICIPANTS = 4  # 0.2 Hz (once every five seconds)
    CAR_SETUPS = 5
    CAR_TELEMETRY = 6
    CAR_STATUS = 7
    FINAL_CLASSIFICATION = 8
    LOBBY_INFO = 9
    CAR_DAMAGE = 10
    SESSION_HISTORY = 11


PacketID.short_description = {
    PacketID.MOTION: "Motion",
    PacketID.SESSION: "Session",
    PacketID.LAP_DATA: "Lap Data",
    PacketID.EVENT: "Event",
    PacketID.PARTICIPANTS: "Participants",
    PacketID.CAR_SETUPS: "Car Setups",
    PacketID.CAR_TELEMETRY: "Car Telemetry",
    PacketID.CAR_STATUS: "Car Status",
    PacketID.FINAL_CLASSIFICATION: "Final Classification",
    PacketID.LOBBY_INFO: "Lobby Info",
    PacketID.CAR_DAMAGE: "Car Damage",
    PacketID.SESSION_HISTORY: "Session History",
}


PacketID.long_description = {
    PacketID.MOTION: "Contains all motion data for player's car – only sent while player is in control",
    PacketID.SESSION: "Data about the session – track, time left",
    PacketID.LAP_DATA: "Data about all the lap times of cars in the session",
    PacketID.EVENT: "Various notable events that happen during a session",
    PacketID.PARTICIPANTS: "List of participants in the session, mostly relevant for multiplayer",
    PacketID.CAR_SETUPS: "Packet detailing car setups for cars in the race",
    PacketID.CAR_TELEMETRY: "Telemetry data for all cars",
    PacketID.CAR_STATUS: "Status data for all cars",
    PacketID.FINAL_CLASSIFICATION: "Final classification confirmation at the end of a race",
    PacketID.LOBBY_INFO: "Information about players in a multiplayer lobby",
    PacketID.CAR_DAMAGE: "Damage status for all cars",
    PacketID.SESSION_HISTORY: "Lap and tyre data for session",
}

#########################################################
#                                                       #
#  __________  Packet ID 0 : MOTION PACKET  __________  #
#                                                       #
#########################################################


class CarMotionData_V1(PackedLittleEndianStructure):
    """This type is used for the 20-element 'carMotionData' array of the PacketMotionData_V1 type, defined below."""

    _fields_ = [
        ("worldPositionX", ctypes.c_float),  # World space X position
        ("worldPositionY", ctypes.c_float),  # World space Y position
        ("worldPositionZ", ctypes.c_float),  # World space Z position
        ("worldVelocityX", ctypes.c_float),  # Velocity in world space X
        ("worldVelocityY", ctypes.c_float),  # Velocity in world space Y
        ("worldVelocityZ", ctypes.c_float),  # Velocity in world space Z
        (
            "worldForwardDirX",
            ctypes.c_int16,
        ),  # World space forward X direction (normalised)
        (
            "worldForwardDirY",
            ctypes.c_int16,
        ),  # World space forward Y direction (normalised)
        (
            "worldForwardDirZ",
            ctypes.c_int16,
        ),  # World space forward Z direction (normalised)
        (
            "worldRightDirX",
            ctypes.c_int16,
        ),  # World space right X direction (normalised)
        (
            "worldRightDirY",
            ctypes.c_int16,
        ),  # World space right Y direction (normalised)
        (
            "worldRightDirZ",
            ctypes.c_int16,
        ),  # World space right Z direction (normalised)
        ("gForceLateral", ctypes.c_float),  # Lateral G-Force component
        ("gForceLongitudinal", ctypes.c_float),  # Longitudinal G-Force component
        ("gForceVertical", ctypes.c_float),  # Vertical G-Force component
        ("yaw", ctypes.c_float),  # Yaw angle in radians
        ("pitch", ctypes.c_float),  # Pitch angle in radians
        ("roll", ctypes.c_float),  # Roll angle in radians
    ]


class PacketMotionData_V1(PackedLittleEndianStructure):
    """The motion packet gives physics data for all the cars being driven.

    There is additional data for the car being driven with the goal of being able to drive a motion platform setup.

    N.B. For the normalised vectors below, to convert to float values divide by 32767.0f – 16-bit signed values are
    used to pack the data and on the assumption that direction values are always between -1.0f and 1.0f.

    Frequency: Rate as specified in menus
    Size: 1464 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        ("carMotionData", CarMotionData_V1 * 22),  # Data for all cars on track
        # Extra player car ONLY data
        (
            "suspensionPosition",
            ctypes.c_float * 4,
        ),  # Note: All wheel arrays have the following order:
        ("suspensionVelocity", ctypes.c_float * 4),  # RL, RR, FL, FR
        ("suspensionAcceleration", ctypes.c_float * 4),  # RL, RR, FL, FR
        ("wheelSpeed", ctypes.c_float * 4),  # Speed of each wheel
        ("wheelSlip", ctypes.c_float * 4),  # Slip ratio for each wheel
        ("localVelocityX", ctypes.c_float),  # Velocity in local space
        ("localVelocityY", ctypes.c_float),  # Velocity in local space
        ("localVelocityZ", ctypes.c_float),  # Velocity in local space
        ("angularVelocityX", ctypes.c_float),  # Angular velocity x-component
        ("angularVelocityY", ctypes.c_float),  # Angular velocity y-component
        ("angularVelocityZ", ctypes.c_float),  # Angular velocity z-component
        ("angularAccelerationX", ctypes.c_float),  # Angular acceleration x-component
        ("angularAccelerationY", ctypes.c_float),  # Angular acceleration y-component
        ("angularAccelerationZ", ctypes.c_float),  # Angular acceleration z-component
        ("frontWheelsAngle", ctypes.c_float),  # Current front wheels angle in radians
    ]


##########################################################
#                                                        #
#  __________  Packet ID 1 : SESSION PACKET  __________  #
#                                                        #
##########################################################


class MarshalZone_V1(PackedLittleEndianStructure):
    """This type is used for the 21-element 'marshalZones' array of the PacketSessionData_V1 type, defined below."""

    _fields_ = [
        (
            "zoneStart",
            ctypes.c_float,
        ),  # Fraction (0..1) of way through the lap the marshal zone starts
        (
            "zoneFlag",
            ctypes.c_int8,
        ),  # -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow, 4 = red
    ]


class WeatherForecastSample_V1(PackedLittleEndianStructure):
    """This type is used for the 56-element 'weatherForecastSamples' array of the PacketSessionData_V1 type, defined below."""

    _fields_ = [
        (
            "sessionType",
            ctypes.c_uint8,
        ),  # 0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P, 5 = Q1,
        # 6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ, 10 = R, 11 = R2
        # 12 = R3, 13 = Time Trial
        ("timeOffset", ctypes.c_uint8),  # Time in minutes the forecast is for
        (
            "weather",
            ctypes.c_uint8,
        ),  # Weather - 0 = clear, 1 = light cloud, 2 = overcast, 3 = light rain, 4 = heavy rain, 5 = storm
        ("trackTemperature", ctypes.c_int8),  # Track temp. in degrees Celsius
        (
            "trackTemperatureChange",
            ctypes.c_int8,
        ),  # Track temp. change – 0 = up, 1 = down, 2 = no change
        ("airTemperature", ctypes.c_int8),  # Air temp. in degrees celsius
        (
            "airTemperatureChange",
            ctypes.c_int8,
        ),  # Air temp. change – 0 = up, 1 = down, 2 = no change
        ("rainPercentage", ctypes.c_uint8),  # Rain percentage (0-100)
    ]


class PacketSessionData_V1(PackedLittleEndianStructure):
    """The session packet includes details about the current session in progress.

    Frequency: 2 per second
    Size: 632 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        (
            "weather",
            ctypes.c_uint8,
        ),  # Weather - 0 = clear, 1 = light cloud, 2 = overcast
        # 3 = light rain, 4 = heavy rain, 5 = storm
        ("trackTemperature", ctypes.c_int8),  # Track temp. in degrees celsius
        ("airTemperature", ctypes.c_int8),  # Air temp. in degrees celsius
        ("totalLaps", ctypes.c_uint8),  # Total number of laps in this race
        ("trackLength", ctypes.c_uint16),  # Track length in metres
        (
            "sessionType",
            ctypes.c_uint8,
        ),  # 0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P
        # 5 = Q1, 6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ
        # 10 = R, 11 = R2, 12 = Time Trial
        ("trackId", ctypes.c_int8),  # -1 for unknown, 0-21 for tracks, see appendix
        ("formula", ctypes.c_uint8),  # Formula, 0 = F1 Modern, 1 = F1 Classic, 2 = F2,
        # 3 = F1 Generic
        ("sessionTimeLeft", ctypes.c_uint16),  # Time left in session in seconds
        ("sessionDuration", ctypes.c_uint16),  # Session duration in seconds
        ("pitSpeedLimit", ctypes.c_uint8),  # Pit speed limit in kilometres per hour
        ("gamePaused", ctypes.c_uint8),  # Whether the game is paused
        ("isSpectating", ctypes.c_uint8),  # Whether the player is spectating
        ("spectatorCarIndex", ctypes.c_uint8),  # Index of the car being spectated
        (
            "sliProNativeSupport",
            ctypes.c_uint8,
        ),  # SLI Pro support, 0 = inactive, 1 = active
        ("numMarshalZones", ctypes.c_uint8),  # Number of marshal zones to follow
        ("marshalZones", MarshalZone_V1 * 21),  # List of marshal zones – max 21
        ("safetyCarStatus", ctypes.c_uint8),  # 0 = no safety car, 1 = full safety car
        # 2 = virtual safety car
        ("networkGame", ctypes.c_uint8),  # 0 = offline, 1 = online
        (
            "numWeatherForecastSamples",
            ctypes.c_uint8,
        ),  # Number of weather samples to follow
        (
            "weatherForecastSamples",
            WeatherForecastSample_V1 * 56,
        ),  # Array of weather forecast samples
        ("forecastAccuracy", ctypes.c_uint8),  # 0 = Perfect, 1 = Approximate
        ("aiDifficulty", ctypes.c_uint8),  # AI Difficulty rating – 0-110
        (
            "seasonLinkIdentifier",
            ctypes.c_uint32,
        ),  # Identifier for season - persists across saves
        (
            "weekendLinkIdentifier",
            ctypes.c_uint32,
        ),  # Identifier for weekend - persists across saves
        (
            "sessionLinkIdentifier",
            ctypes.c_uint32,
        ),  # Identifier for session - persists across saves
        (
            "pitStopWindowIdealLap",
            ctypes.c_uint8,
        ),  # Ideal lap to pit on for current strategy (player)
        (
            "pitStopWindowLatestLap",
            ctypes.c_uint8,
        ),  # Latest lap to pit on for current strategy (player)
        (
            "pitStopRejoinPosition",
            ctypes.c_uint8,
        ),  # Predicted position to rejoin at (player)
        ("steeringAssist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("brakingAssist", ctypes.c_uint8),  # 0 = off, 1 = low, 2 = medium, 3 = high
        (
            "gearboxAssist",
            ctypes.c_uint8,
        ),  # 1 = manual, 2 = manual & suggested gear, 3 = auto
        ("pitAssist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("pitReleaseAssist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("ERSAssist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("DRSAssist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("dynamicRacingLine", ctypes.c_uint8),  # 0 = off, 1 = corners only, 2 = full
        ("dynamicRacingLineType", ctypes.c_uint8),  # 0 = 2D, 1 = 3D
        ("gameMode", ctypes.c_uint8),  # Game mode id - see appendix
        ("ruleSet", ctypes.c_uint8),  # Ruleset - see appendix
        ("timeOfDay", ctypes.c_uint32),  # Local time of day - minutes since midnight
        (
            "sessionLength",
            ctypes.c_uint8,
        )  # 0 = None, 2 = Very Short, 3 = Short, 4 = Medium
        # 5 = Medium Long, 6 = Long, 7 = Full
    ]


###########################################################
#                                                         #
#  __________  Packet ID 2 : LAP DATA PACKET  __________  #
#                                                         #
###########################################################


class LapData_V1(PackedLittleEndianStructure):
    """This type is used for the 20-element 'lapData' array of the PacketLapData_V1 type, defined below."""

    _fields_ = [
        ("lastLapTimeInMS", ctypes.c_uint32),  # Last lap time in miliseconds
        (
            "currentLapTimeInMS",
            ctypes.c_uint32,
        ),  # Current time around the lap in miliseconds
        ("sector1TimeInMS", ctypes.c_uint16),  # Sector 1 time in miliseconds
        ("sector2TimeInMS", ctypes.c_uint16),  # Sector 2 time in miliseconds
        (
            "lapDistance",
            ctypes.c_float,
        ),  # Distance vehicle is around current lap in metres – could
        # be negative if line hasn’t been crossed yet
        (
            "totalDistance",
            ctypes.c_float,
        ),  # Total distance travelled in session in metres – could
        # be negative if line hasn’t been crossed yet
        ("safetyCarDelta", ctypes.c_float),  # Delta in seconds for safety car
        ("carPosition", ctypes.c_uint8),  # Car race position
        ("currentLapNum", ctypes.c_uint8),  # Current lap number
        ("pitStatus", ctypes.c_uint8),  # 0 = none, 1 = pitting, 2 = in pit area
        ("numPitStops", ctypes.c_uint8),  # Number of pit stops taken in this race
        ("sector", ctypes.c_uint8),  # 0 = sector1, 1 = sector2, 2 = sector3
        (
            "currentLapInvalid",
            ctypes.c_uint8,
        ),  # Current lap invalid - 0 = valid, 1 = invalid
        (
            "penalties",
            ctypes.c_uint8,
        ),  # Accumulated time penalties in seconds to be added
        ("warnings", ctypes.c_uint8),  # Accumulated number of warnings issued
        (
            "numUnservedDriveThroughPens",
            ctypes.c_uint8,
        ),  # Num drive through pens left to serve
        ("numUnservedStopGoPens", ctypes.c_uint8),  # Num stop go pens left to serve
        (
            "gridPosition",
            ctypes.c_uint8,
        ),  # Grid position the vehicle started the race in
        (
            "driverStatus",
            ctypes.c_uint8,
        ),  # Status of driver - 0 = in garage, 1 = flying lap
        # 2 = in lap, 3 = out lap, 4 = on track
        (
            "resultStatus",
            ctypes.c_uint8,
        ),  # Result status - 0 = invalid, 1 = inactive, 2 = active
        # 3 = finished, 4 = didnotfinish, 5 = disqualified,
        # 6 = not classified, 7 = retired
        (
            "pitLaneTimerActive",
            ctypes.c_uint8,
        ),  # Pit lane timing, 0 = inactive, 1 = active
        (
            "pitLaneTimeInLaneInMS",
            ctypes.c_uint16,
        ),  # If active, the current time spent in the pit lane in ms
        ("pitStopTimerInMS", ctypes.c_uint16),  # Time of the actual pit stop in ms
        (
            "pitStopShouldServePen",
            ctypes.c_uint8,
        ),  # Whether the car should serve a penalty at this stop
    ]


class PacketLapData_V1(PackedLittleEndianStructure):
    """The lap data packet gives details of all the cars in the session.

    Frequency: Rate as specified in menus
    Size: 972 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        ("lapData", LapData_V1 * 22),  # Lap data for all cars on track
        (
            "timeTrialPBCarIdx",
            ctypes.c_uint8,
        ),  # Index of Personal Best car in time trial (255 if invalid)
        (
            "timeTrialRivalCarIdx",
            ctypes.c_uint8,
        ),  # Index of Rival car in time trial (255 if invalid)
    ]


########################################################
#                                                      #
#  __________  Packet ID 3 : EVENT PACKET  __________  #
#                                                      #
########################################################


class FastestLap_V1(PackedLittleEndianStructure):
    _fields_ = [
        ("vehicleIdx", ctypes.c_uint8),  # Vehicle index of car achieving fastest lap
        ("lapTime", ctypes.c_float),  # Lap time is in seconds
    ]


class Retirement_V1(PackedLittleEndianStructure):
    _fields_ = [("vehicleIdx", ctypes.c_uint8)]  # Vehicle index of car retiring


class TeamMateInPits_V1(PackedLittleEndianStructure):
    _fields_ = [("vehicleIdx", ctypes.c_uint8)]  # Vehicle index of team mate


class RaceWinner_V1(PackedLittleEndianStructure):
    _fields_ = [("vehicleIdx", ctypes.c_uint8)]  # Vehicle index of the race winner


class Penalty_V1(PackedLittleEndianStructure):
    _fields_ = [
        ("penaltyType", ctypes.c_uint8),  # Penalty type – see Appendices
        ("infringementType", ctypes.c_uint8),  # Infringement type – see Appendices
        (
            "vehicleIdx",
            ctypes.c_uint8,
        ),  # Vehicle index of the car the penalty is applied to
        ("otherVehicleIdx", ctypes.c_uint8),  # Vehicle index of the other car involved
        ("time", ctypes.c_uint8),  # Time gained, or time spent doing action in seconds
        ("lapNum", ctypes.c_uint8),  # Lap the penalty occurred on
        ("placesGained", ctypes.c_uint8),  # Number of places gained by this
    ]


class SpeedTrap_V1(PackedLittleEndianStructure):
    _fields_ = [
        (
            "vehicleIdx",
            ctypes.c_uint8,
        ),  # Vehicle index of the vehicle triggering speed trap
        ("speed", ctypes.c_float),  # Top speed achieved in kilometres per hour
        (
            "isOverallFastestInSession",
            ctypes.c_uint8,
        ),  # Overall fastest speed in session = 1, otherwise 0
        (
            "isDriverFastestInSession",
            ctypes.c_uint8,
        ),  # Fastest speed for driver in session = 1, otherwise 0
        (
            "fastestVehicleIdxInSession",
            ctypes.c_uint8,
        ),  # Vehicle index of the vehicle that is the fastest in this session
        (
            "fastestSpeedInSession",
            ctypes.c_float,
        ),  # Speed of the vehicle that is the fastest in this session
    ]


class StartLights_V1(PackedLittleEndianStructure):
    _fields_ = [("numLights", ctypes.c_uint8)]  # Number of lights showing


class DriveThroughPenaltyServed_V1(PackedLittleEndianStructure):
    _fields_ = [
        (
            "vehicleIdx",
            ctypes.c_uint8,
        )  # Vehicle index of the vehicle serving drive through
    ]


class StopGoPenaltyServed_V1(PackedLittleEndianStructure):
    _fields_ = [
        ("vehicleIdx", ctypes.c_uint8)  # Vehicle index of the vehicle serving stop go
    ]


class Flashback_V1(PackedLittleEndianStructure):
    _fields_ = [
        (
            "flashbackFrameIdentifier",
            ctypes.c_uint32,
        ),  # Frame identifier flashed back to
        ("flashbackSessionTime", ctypes.c_float),  # Session time flashed back to
    ]


class Buttons_V1(PackedLittleEndianStructure):
    _fields_ = [
        (
            "buttonStatus",
            ctypes.c_uint32,
        )  # Bit flags specifying which buttons are being pressed currently - see appendices
    ]


class EventDataDetails_V1(ctypes.Union, PackedLittleEndianStructure):
    """The event details packet is different for each type of event. Make sure only the correct type is interpreted."""

    _fields_ = [
        ("fastestLap", FastestLap_V1),
        ("retirement", Retirement_V1),
        ("teamMateInPits", TeamMateInPits_V1),
        ("raceWinner", RaceWinner_V1),
        ("penalty", Penalty_V1),
        ("speedTrap", SpeedTrap_V1),
        ("startLIghts", StartLights_V1),
        ("driveThroughPenaltyServed", DriveThroughPenaltyServed_V1),
        ("stopGoPenaltyServed", StopGoPenaltyServed_V1),
        ("flashback", Flashback_V1),
        ("buttons", Buttons_V1),
    ]


class PacketEventData_V1(PackedLittleEndianStructure):
    """This packet gives details of events that happen during the course of a session.

    Frequency: When the event occurs
    Size: 40 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        ("eventStringCode", ctypes.c_uint8 * 4),  # Event string code, see below
        (
            "eventDetails",
            EventDataDetails_V1,
        ),  # Event details - should be interpreted differently for each type
    ]


@enum.unique
class EventStringCode(enum.Enum):
    """Value as specified in the PacketEventData_V1.eventStringCode header field, used to distinguish packet types."""

    SSTA = b"SSTA"
    SEND = b"SEND"
    FTLP = b"FTLP"
    RTMT = b"RTMT"
    DRSE = b"DRSE"
    DRSD = b"DRSD"
    TMPT = b"TMPT"
    CHQF = b"CHQF"
    RCWN = b"RCWN"
    PENA = b"PENA"
    SPTP = b"SPTP"
    STLG = b"STLG"
    LGOT = b"LGOT"
    DTSV = b"DTSV"
    SGSV = b"SGSV"
    FLBK = b"FLBK"
    BUTN = b"BUTN"


EventStringCode.short_description = {
    EventStringCode.SSTA: "Session Started",
    EventStringCode.SEND: "Session Ended",
    EventStringCode.FTLP: "Fastest Lap",
    EventStringCode.RTMT: "Retirement",
    EventStringCode.DRSE: "DRS enabled",
    EventStringCode.DRSD: "DRS disabled",
    EventStringCode.TMPT: "Team mate in pits",
    EventStringCode.CHQF: "Chequered flag",
    EventStringCode.RCWN: "Race Winner",
    EventStringCode.PENA: "Penalty Issued",
    EventStringCode.SPTP: "Speed Trap Triggered",
    EventStringCode.STLG: "Start lights",
    EventStringCode.LGOT: "Lights out",
    EventStringCode.DTSV: "Drive through served",
    EventStringCode.SGSV: "Stop go served",
    EventStringCode.FLBK: "Flashback",
    EventStringCode.BUTN: "Button status",
}


EventStringCode.long_description = {
    EventStringCode.SSTA: "Sent when the session starts",
    EventStringCode.SEND: "Sent when the session ends",
    EventStringCode.FTLP: "When a driver achieves the fastest lap",
    EventStringCode.RTMT: "When a driver retires",
    EventStringCode.DRSE: "Race control have enabled DRS",
    EventStringCode.DRSD: "Race control have disabled DRS",
    EventStringCode.TMPT: "Your team mate has entered the pits",
    EventStringCode.CHQF: "The chequered flag has been waved",
    EventStringCode.RCWN: "The race winner is announced",
    EventStringCode.PENA: "A penalty has been issued - details in event",
    EventStringCode.SPTP: "Speed trap has been triggered by fastest speed",
    EventStringCode.STLG: "Start lights – number shown",
    EventStringCode.LGOT: "Lights out",
    EventStringCode.DTSV: "Drive through penatly served",
    EventStringCode.SGSV: "Stop go penalty served",
    EventStringCode.FLBK: "Flashback activated",
    EventStringCode.BUTN: "Button status changed",
}

###############################################################
#                                                             #
#  __________  Packet ID 4 : PARTICIPANTS PACKET  __________  #
#                                                             #
###############################################################


class ParticipantData_V1(PackedLittleEndianStructure):
    """This type is used for the 22-element 'participants' array of the PacketParticipantsData_V1 type, defined below."""

    _fields_ = [
        (
            "aiControlled",
            ctypes.c_uint8,
        ),  # Whether the vehicle is AI (1) or Human (0) controlled
        ("driverId", ctypes.c_uint8),  # Driver id - see appendix, 255 if network human
        (
            "networkId",
            ctypes.c_uint8,
        ),  # Network id – unique identifier for network players
        ("teamId", ctypes.c_uint8),  # Team id - see appendix
        ("myTeam", ctypes.c_uint8),  # My team flag – 1 = My Team, 0 = otherwise
        ("raceNumber", ctypes.c_uint8),  # Race number of the car
        ("nationality", ctypes.c_uint8),  # Nationality of the driver
        (
            "name",
            ctypes.c_char * 48,
        ),  # Name of participant in UTF-8 format – null terminated
        # Will be truncated with … (U+2026) if too long
        (
            "yourTelemetry",
            ctypes.c_uint8,
        ),  # The player's UDP setting, 0 = restricted, 1 = public
    ]


class PacketParticipantsData_V1(PackedLittleEndianStructure):
    """This is a list of participants in the race.

    If the vehicle is controlled by AI, then the name will be the driver name.
    If this is a multiplayer game, the names will be the Steam Id on PC, or the LAN name if appropriate.
    On Xbox One, the names will always be the driver name, on PS4 the name will be the LAN name if playing a LAN game,
    otherwise it will be the driver name.

    The array should be indexed by vehicle index.

    Frequency: Every 5 seconds
    Size: 1257 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        (
            "numActiveCars",
            ctypes.c_uint8,
        ),  # Number of active cars in the data – should match number of
        # cars on HUD
        ("participants", ParticipantData_V1 * 22),
    ]


#############################################################
#                                                           #
#  __________  Packet ID 5 : CAR SETUPS PACKET  __________  #
#                                                           #
#############################################################


class CarSetupData_V1(PackedLittleEndianStructure):
    """This type is used for the 22-element 'carSetups' array of the PacketCarSetupData_V1 type, defined below."""

    _fields_ = [
        ("frontWing", ctypes.c_uint8),  # Front wing aero
        ("rearWing", ctypes.c_uint8),  # Rear wing aero
        (
            "onThrottle",
            ctypes.c_uint8,
        ),  # Differential adjustment on throttle (percentage)
        (
            "offThrottle",
            ctypes.c_uint8,
        ),  # Differential adjustment off throttle (percentage)
        ("frontCamber", ctypes.c_float),  # Front camber angle (suspension geometry)
        ("rearCamber", ctypes.c_float),  # Rear camber angle (suspension geometry)
        ("frontToe", ctypes.c_float),  # Front toe angle (suspension geometry)
        ("rearToe", ctypes.c_float),  # Rear toe angle (suspension geometry)
        ("frontSuspension", ctypes.c_uint8),  # Front suspension
        ("rearSuspension", ctypes.c_uint8),  # Rear suspension
        ("frontAntiRollBar", ctypes.c_uint8),  # Front anti-roll bar
        ("rearAntiRollBar", ctypes.c_uint8),  # Rear anti-roll bar
        ("frontSuspensionHeight", ctypes.c_uint8),  # Front ride height
        ("rearSuspensionHeight", ctypes.c_uint8),  # Rear ride height
        ("brakePressure", ctypes.c_uint8),  # Brake pressure (percentage)
        ("brakeBias", ctypes.c_uint8),  # Brake bias (percentage)
        ("rearLeftTyrePressure", ctypes.c_float),  # Rear left tyre pressure (PSI)
        ("rearRightTyrePressure", ctypes.c_float),  # Rear right tyre pressure (PSI)
        ("frontLeftTyrePressure", ctypes.c_float),  # Front left tyre pressure (PSI)
        ("frontRightTyrePressure", ctypes.c_float),  # Front right tyre pressure (PSI)
        ("ballast", ctypes.c_uint8),  # Ballast
        ("fuelLoad", ctypes.c_float),  # Fuel load
    ]


class PacketCarSetupData_V1(PackedLittleEndianStructure):
    """This packet details the car setups for each vehicle in the session.

    Note that in multiplayer games, other player cars will appear as blank, you will only be able to see your car setup and AI cars.

    Frequency: 2 per second
    Size: 1102 bytes
    Version: 1
    """

    _fields_ = [("header", PacketHeader), ("carSetups", CarSetupData_V1 * 22)]  # Header


################################################################
#                                                              #
#  __________  Packet ID 6 : CAR TELEMETRY PACKET  __________  #
#                                                              #
################################################################


class CarTelemetryData_V1(PackedLittleEndianStructure):
    """This type is used for the 22-element 'carTelemetryData' array of the PacketCarTelemetryData_V1 type, defined below."""

    _fields_ = [
        ("speed", ctypes.c_uint16),  # Speed of car in kilometres per hour
        ("throttle", ctypes.c_float),  # Amount of throttle applied (0.0 to 1.0)
        (
            "steer",
            ctypes.c_float,
        ),  # Steering (-1.0 (full lock left) to 1.0 (full lock right))
        ("brake", ctypes.c_float),  # Amount of brake applied (0 to 1.0)
        ("clutch", ctypes.c_uint8),  # Amount of clutch applied (0 to 100)
        ("gear", ctypes.c_int8),  # Gear selected (1-8, N=0, R=-1)
        ("engineRPM", ctypes.c_uint16),  # Engine RPM
        ("drs", ctypes.c_uint8),  # 0 = off, 1 = on
        ("revLightsPercent", ctypes.c_uint8),  # Rev lights indicator (percentage)
        (
            "revLightsBitValue",
            ctypes.c_uint16,
        ),  # Rev lights (bit 0 = leftmost LED, bit 14 = rightmost LED)
        ("brakesTemperature", ctypes.c_uint16 * 4),  # Brakes temperature (celsius)
        (
            "tyresSurfaceTemperature",
            ctypes.c_uint8 * 4,
        ),  # Tyres surface temperature (celsius)
        (
            "tyresInnerTemperature",
            ctypes.c_uint8 * 4,
        ),  # Tyres inner temperature (celsius)
        ("engineTemperature", ctypes.c_uint16),  # Engine temperature (celsius)
        ("tyresPressure", ctypes.c_float * 4),  # Tyres pressure (PSI)
        ("surfaceType", ctypes.c_uint8 * 4),  # Driving surface, see appendices
    ]


class PacketCarTelemetryData_V1(PackedLittleEndianStructure):
    """This packet details telemetry for all the cars in the race.

    It details various values that would be recorded on the car such as speed, throttle application, DRS etc.
    Note that the rev light configurations are presented separately as well and will mimic real life driver preferences.

    Frequency: Rate as specified in menus
    Size: 1347 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        ("carTelemetryData", CarTelemetryData_V1 * 22),
        ("mfdPanelIndex", ctypes.c_uint8),  # Index of MFD panel open - 255 = MFD closed
        # Single player, race – 0 = Car setup, 1 = Pits
        # 2 = Damage, 3 = Engine, 4 = Temperatures
        # May vary depending on game mode
        ("mfdPanelIndexSecondaryPlayer", ctypes.c_uint8),  # See above
        (
            "suggestedGear",
            ctypes.c_int8,
        ),  # Suggested gear for the player (1-8), 0 if no gear suggested
    ]


#############################################################
#                                                           #
#  __________  Packet ID 7 : CAR STATUS PACKET  __________  #
#                                                           #
#############################################################


class CarStatusData_V1(PackedLittleEndianStructure):
    """This type is used for the 22-element 'carStatusData' array of the PacketCarStatusData_V1 type, defined below."""

    _fields_ = [
        (
            "tractionControl",
            ctypes.c_uint8,
        ),  # Traction control - 0 = off, 1 = medium, 2 = full
        ("antiLockBrakes", ctypes.c_uint8),  # 0 (off) - 1 (on)
        (
            "fuelMix",
            ctypes.c_uint8,
        ),  # Fuel mix - 0 = lean, 1 = standard, 2 = rich, 3 = max
        ("frontBrakeBias", ctypes.c_uint8),  # Front brake bias (percentage)
        ("pitLimiterStatus", ctypes.c_uint8),  # Pit limiter status - 0 = off, 1 = on
        ("fuelInTank", ctypes.c_float),  # Current fuel mass
        ("fuelCapacity", ctypes.c_float),  # Fuel capacity
        (
            "fuelRemainingLaps",
            ctypes.c_float,
        ),  # Fuel remaining in terms of laps (value on MFD)
        ("maxRPM", ctypes.c_uint16),  # Cars max RPM, point of rev limiter
        ("idleRPM", ctypes.c_uint16),  # Cars idle RPM
        ("maxGears", ctypes.c_uint8),  # Maximum number of gears
        ("drsAllowed", ctypes.c_uint8),  # 0 = not allowed, 1 = allowed
        (
            "drsActivationDistance",
            ctypes.c_uint16,
        ),  # 0 = DRS not available, non-zero - DRS will be available
        # in [X] metres
        (
            "actualTyreCompound",
            ctypes.c_uint8,
        ),  # F1 Modern - 16 = C5, 17 = C4, 18 = C3, 19 = C2, 20 = C1
        # 7 = inter, 8 = wet
        # F1 Classic - 9 = dry, 10 = wet
        # F2 – 11 = super soft, 12 = soft, 13 = medium, 14 = hard
        # 15 = wet
        (
            "visualTyreCompound",
            ctypes.c_uint8,
        ),  # F1 visual (can be different from actual compound)
        # 16 = soft, 17 = medium, 18 = hard, 7 = inter, 8 = wet
        # F1 Classic – same as above
        # F2 – same as above
        ("tyresAgeLaps", ctypes.c_uint8),  # Age in laps of the current set of tyres
        ("vehicleFiaFlags", ctypes.c_int8),  # -1 = invalid/unknown, 0 = none, 1 = green
        # 2 = blue, 3 = yellow, 4 = red
        ("ersStoreEnergy", ctypes.c_float),  # ERS energy store in Joules
        ("ersDeployMode", ctypes.c_uint8),  # ERS deployment mode, 0 = none, 1 = medium
        # 2 = hotlap, 3 = overtake
        (
            "ersHarvestedThisLapMGUK",
            ctypes.c_float,
        ),  # ERS energy harvested this lap by MGU-K
        (
            "ersHarvestedThisLapMGUH",
            ctypes.c_float,
        ),  # ERS energy harvested this lap by MGU-H
        ("ersDeployedThisLap", ctypes.c_float),  # ERS energy deployed this lap
        (
            "networkPaused",
            ctypes.c_uint8,
        ),  # Whether the car is paused in a network game
    ]


class PacketCarStatusData_V1(PackedLittleEndianStructure):
    """This packet details car statuses for all the cars in the race.

    Frequency: Rate as specified in menus
    Size: 1058 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        ("carStatusData", CarStatusData_V1 * 22),
    ]


#######################################################################
#                                                                     #
#  __________  Packet ID 8 : FINAL CLASSIFICATION PACKET  __________  #
#                                                                     #
#######################################################################


class FinalClassificationData_V1(PackedLittleEndianStructure):
    """This type is used for the 22-element 'classificationData' array of the PacketFinalClassificationData_V1 type, defined below."""

    _fields_ = [
        ("position", ctypes.c_uint8),  # Finishing position
        ("numLaps", ctypes.c_uint8),  # Number of laps completed
        ("gridPosition", ctypes.c_uint8),  # Grid position of the car
        ("points", ctypes.c_uint8),  # Number of points scored
        ("numPitStops", ctypes.c_uint8),  # Number of pit stops made
        (
            "resultStatus",
            ctypes.c_uint8,
        ),  # Result status - 0 = invalid, 1 = inactive, 2 = active
        # 3 = finished, 4 = didnotfinish, 5 = disqualified
        # 6 = not classified, 7 = retired
        (
            "bestLapTimeInMS",
            ctypes.c_uint32,
        ),  # Best lap time of the session in milliseconds
        (
            "totalRaceTime",
            ctypes.c_double,
        ),  # Total race time in seconds without penalties
        ("penaltiesTime", ctypes.c_uint8),  # Total penalties accumulated in seconds
        ("numPenalties", ctypes.c_uint8),  # Number of penalties applied to this driver
        ("numTyreStints", ctypes.c_uint8),  # Number of tyres stints up to maximum
        ("tyreStintsActual", ctypes.c_uint8 * 8),  # Actual tyres used by this driver
        ("tyreStintsVisual", ctypes.c_uint8 * 8),  # Visual tyres used by this driver
        ("tyreStintsEndLaps", ctypes.c_uint8 * 8),  # The lap number stints end on
    ]


class PacketFinalClassificationData_V1(PackedLittleEndianStructure):
    """This packet details the final classification at the end of the race, and the data will match with the post
    race results screen.
    This is especially useful for multiplayer games where it is not always possible to send lap times on the final
    frame because of network delay.

    Frequency: Once at the end of a race
    Size: 1015 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        ("numCars", ctypes.c_uint8),  # Number of cars in the final classification
        ("classificationData", FinalClassificationData_V1 * 22),
    ]


#############################################################
#                                                           #
#  __________  Packet ID 9 : LOBBY INFO PACKET  __________  #
#                                                           #
#############################################################


class LobbyInfoData_V1(PackedLittleEndianStructure):
    """This type is used for the 22-element 'lobbyPlayers' array of the PacketLobbyInfoData_V1 type, defined below."""

    _fields_ = [
        (
            "aiControlled",
            ctypes.c_uint8,
        ),  # Whether the vehicle is AI (1) or Human (0) controlled
        (
            "teamId",
            ctypes.c_uint8,
        ),  # Team id - see appendix (255 if no team currently selected)
        ("nationality", ctypes.c_uint8),  # Nationality of the driver
        (
            "name",
            ctypes.c_char * 48,
        ),  # Name of participant in UTF-8 format – null terminated
        # Will be truncated with ... (U+2026) if too long
        ("carNumber", ctypes.c_uint8),  # Car number of the player
        ("readyStatus", ctypes.c_uint8),  # 0 = not ready, 1 = ready, 2 = spectating
    ]


class PacketLobbyInfoData_V1(PackedLittleEndianStructure):
    """This packet details the players currently in a multiplayer lobby. It details each player’s selected car, any
    AI involved in the game and also the ready status of each of the participants.

    Frequency: Two every second when in the lobby
    Size: 1191 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        # Packet specific data
        ("numPlayers", ctypes.c_uint8),  # Number of players in the lobby data
        ("lobbyPlayers", LobbyInfoData_V1 * 22),
    ]


##############################################################
#                                                            #
#  __________  Packet ID 10 : CAR DAMAGE PACKET  __________  #
#                                                            #
##############################################################


class CarDamageData_V1(PackedLittleEndianStructure):
    """This type is used for the 22-element 'carDamageData' array of the PacketCarDamageData_V1 type, defined below."""

    _fields_ = [
        ("tyresWear", ctypes.c_float * 4),  # Tyre wear (percentage)
        ("tyresDamage", ctypes.c_uint8 * 4),  # Tyre damage (percentage)
        ("brakesDamage", ctypes.c_uint8 * 4),  # Brakes damage (percentage)
        ("frontLeftWingDamage", ctypes.c_uint8),  # Front left wing damage (percentage)
        (
            "frontRightWingDamage",
            ctypes.c_uint8,
        ),  # Front right wing damage (percentage)
        ("rearWingDamage", ctypes.c_uint8),  # Rear wing damage (percentage)
        ("floorDamage", ctypes.c_uint8),  # Floor damage (percentage)
        ("diffuserDamage", ctypes.c_uint8),  # Diffuser damage (percentage)
        ("sidepodDamage", ctypes.c_uint8),  # Sidepod damage (percentage)
        ("drsFault", ctypes.c_uint8),  # Indicator for DRS fault, 0 = OK, 1 = fault
        ("ersFault", ctypes.c_uint8),  # Indicator for ERS fault, 0 = OK, 1 = fault
        ("gearBoxDamage", ctypes.c_uint8),  # Gear box damage (percentage)
        ("engineDamage", ctypes.c_uint8),  # Engine damage (percentage)
        ("engineMGUHWear", ctypes.c_uint8),  # Engine wear MGU-H (percentage)
        ("engineESWear", ctypes.c_uint8),  # Engine wear ES (percentage)
        ("engineCEWear", ctypes.c_uint8),  # Engine wear CE (percentage)
        ("engineICEWear", ctypes.c_uint8),  # Engine wear ICE (percentage)
        ("engineMGUKWear", ctypes.c_uint8),  # Engine wear MGU-K (percentage)
        ("engineTCWear", ctypes.c_uint8),  # Engine wear TC (percentage)
        ("engineBlown", ctypes.c_uint8),  # Engine blown, 0 = OK, 1 = fault
        ("engineSeized", ctypes.c_uint8),  # Engine seized, 0 = OK, 1 = fault
    ]


class PacketCarDamageData_V1(PackedLittleEndianStructure):
    """This packet details car damage parameters for all the cars in the race.

    Frequency: 2 per second
    Size: 948 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        ("carDamageData", CarDamageData_V1 * 22),
    ]


###################################################################
#                                                                 #
#  __________  Packet ID 11 : SESSION HISTORY PACKET  __________  #
#                                                                 #
###################################################################


class LapHistoryData_V1(PackedLittleEndianStructure):
    """This type is used for the 100-element 'lapHistoryData' array of the PacketSessionHistoryData_V1 type, defined below."""

    _fields_ = [
        ("lapTimeInMS", ctypes.c_uint32),  # Lap time in milliseconds
        ("sector1TimeInMS", ctypes.c_uint16),  # Sector 1 time in milliseconds
        ("sector2TimeInMS", ctypes.c_uint16),  # Sector 2 time in milliseconds
        ("sector3TimeInMS", ctypes.c_uint16),  # Sector 3 time in milliseconds
        (
            "lapValidBitFlags",
            ctypes.c_uint8,
        )  # 0x01 bit set-lap valid, 0x02 bit set-sector 1 valid
        # 0x04 bit set-sector 2 valid, 0x08 bit set-sector 3 valid
    ]


class TyreStintHistoryData_V1(PackedLittleEndianStructure):
    """This type is used for the 8-element 'tyreStintsHistoryData' array of the PacketSessionHistoryData_V1 type, defined below."""

    _fields_ = [
        ("endLap", ctypes.c_uint8),  # Lap the tyre usage ends on (255 of current tyre)
        ("tyreActualCompound", ctypes.c_uint8),  # Actual tyres used by this driver
        ("tyreVisualCompound", ctypes.c_uint8),  # Visual tyres used by this driver
    ]


class PacketSessionHistoryData_V1(PackedLittleEndianStructure):
    """This packet contains lap times and tyre usage for the session. This packet works slightly differently
    to other packets.
    To reduce CPU and bandwidth, each packet relates to a specific vehicle and is sent every 1/20 s, and the
    vehicle being sent is cycled through. Therefore in a 20 car race you should receive an update for each
    vehicle at least once per second.

    Note that at the end of the race, after the final classification packet has been sent, a final bulk update
    of all the session histories for the vehicles in that session will be sent.

    Frequency: 20 per second but cycling through cars
    Size: 1155 bytes
    Version: 1
    """

    _fields_ = [
        ("header", PacketHeader),  # Header
        ("carIdx", ctypes.c_uint8),  # Index of the car this lap data relates to
        (
            "numLaps",
            ctypes.c_uint8,
        ),  # Num laps in the data (including current partial lap)
        ("numTyreStints", ctypes.c_uint8),  # Number of tyre stints in the data
        ("bestLapTimeLapNum", ctypes.c_uint8),  # Lap the best lap time was achieved on
        (
            "bestSector1LapNum",
            ctypes.c_uint8,
        ),  # Lap the best Sector 1 time was achieved on
        (
            "bestSector2LapNum",
            ctypes.c_uint8,
        ),  # Lap the best Sector 2 time was achieved on
        (
            "bestSector3LapNum",
            ctypes.c_uint8,
        ),  # Lap the best Sector 3 time was achieved on
        ("lapHistoryData", LapHistoryData_V1 * 100),  # 100 laps of data max
        ("tyreStintsHistoryData", TyreStintHistoryData_V1 * 8),
    ]


###################################################################
#                                                                 #
#  Appendices: various value enumerations used in the UDP output  #
#                                                                 #
###################################################################

TeamIDs = {
    0: "Mercedes",
    1: "Ferrari",
    2: "Red Bull Racing",
    3: "Williams",
    4: "Aston Martin",
    5: "Alpine",
    6: "Alpha Tauri",
    7: "Haas",
    8: "McLaren",
    9: "Alfa Romeo",
    85: "Mercedes 2020",
    86: "Ferrari 2020",
    87: "Red Bull 2020",
    88: "Williams 2020",
    89: "Racing Point 2020",
    90: "Renault 2020",
    91: "Alpha Tauri 2020",
    92: "Haas 2020",
    93: "McLaren 2020",
    94: "Alfa Romeo 2020",
    95: "Aston Martin DB11 V12 ",
    96: "Aston Martin Vantage F1 Edition",
    97: "Aston Martin Vantage Safety Car",
    98: "Ferrari F8 Tributo",
    99: "Ferrari Roma",
    100: "McLaren 720S",
    101: "McLaren Artura",
    102: "Mercedes AMG GT Black Series Safety Car",
    103: "Mercedes AMG GTR Pro",
    104: "F1 Custom Team",
    106: "Prema ‘21",
    107: "Uni - Virtuosi ‘21",
    108: "Carlin ‘21",
    109: "Hitech ‘21",
    110: "Art GP ‘21",
    111: "MP Motorsport ‘21",
    112: "Charouz ‘21",
    113: "Dams ‘21",
    114: "Campos ‘21",
    115: "BWT ‘21",
    116: "Trident ‘21",
    117: "Mercedes AMG GT Black Series",
    118: "Prema ‘22",
    119: "Virtuosi ‘22",
    120: "Carlin ‘22",
    121: "Hitech ‘22",
    122: "Art GP ‘22",
    123: "MP Motorsport ‘22",
    124: "Charouz ‘22",
    125: "Dams ‘22",
    126: "Campos ‘22",
    127: "Van Amersfoort Racing ‘22",
    128: "Trident ‘22",
}


DriverIDs = {
    0: "Carlos Sainz",
    1: "Daniil Kvyat",
    2: "Daniel Ricciardo",
    3: "Fernando Alonso",
    4: "Felipe Massa",
    6: "Kimi Räikkönen",
    7: "Lewis Hamilton",
    9: "Max Verstappen",
    10: "Nico Hulkenburg",
    11: "Kevin Magnussen",
    12: "Romain Grosjean",
    13: "Sebastian Vettel",
    14: "Sergio Perez",
    15: "Valtteri Bottas",
    17: "Esteban Ocon",
    19: "Lance Stroll",
    20: "Arron Barnes",
    21: "Martin Giles",
    22: "Alex Murray",
    23: "Lucas Roth",
    24: "Igor Correia",
    25: "Sophie Levasseur",
    26: "Jonas Schiffer",
    27: "Alain Forest",
    28: "Jay Letourneau",
    29: "Esto Saari",
    30: "Yasar Atiyeh",
    31: "Callisto Calabresi",
    32: "Naota Izum",
    33: "Howard Clarke",
    34: "Wilheim Kaufmann",
    35: "Marie Laursen",
    36: "Flavio Nieves",
    37: "Peter Belousov",
    38: "Klimek Michalski",
    39: "Santiago Moreno",
    40: "Benjamin Coppens",
    41: "Noah Visser",
    42: "Gert Waldmuller",
    43: "Julian Quesada",
    44: "Daniel Jones",
    45: "Artem Markelov",
    46: "Tadasuke Makino",
    47: "Sean Gelael",
    48: "Nyck De Vries",
    49: "Jack Aitken",
    50: "George Russell",
    51: "Maximilian Günther",
    52: "Nirei Fukuzumi",
    53: "Luca Ghiotto",
    54: "Lando Norris",
    55: "Sérgio Sette Câmara",
    56: "Louis Delétraz",
    57: "Antonio Fuoco",
    58: "Charles Leclerc",
    59: "Pierre Gasly",
    62: "Alexander Albon",
    63: "Nicholas Latifi",
    64: "Dorian Boccolacci",
    65: "Niko Kari",
    66: "Roberto Merhi",
    67: "Arjun Maini",
    68: "Alessio Lorandi",
    69: "Ruben Meijer",
    70: "Rashid Nair",
    71: "Jack Tremblay",
    72: "Devon Butler",
    73: "Lukas Weber",
    74: "Antonio Giovinazzi",
    75: "Robert Kubica",
    76: "Alain Prost",
    77: "Ayrton Senna",
    78: "Nobuharu Matsushita",
    79: "Nikita Mazepin",
    80: "Guanya Zhou",
    81: "Mick Schumacher",
    82: "Callum Ilott",
    83: "Juan Manuel Correa",
    84: "Jordan King",
    85: "Mahaveer Raghunathan",
    86: "Tatiana Calderon",
    87: "Anthoine Hubert",
    88: "Guiliano Alesi",
    89: "Ralph Boschung",
    90: "Michael Schumacher",
    91: "Dan Ticktum",
    92: "Marcus Armstrong",
    93: "Christian Lundgaard",
    94: "Yuki Tsunoda",
    95: "Jehan Daruvala",
    96: "Gulherme Samaia",
    97: "Pedro Piquet",
    98: "Felipe Drugovich",
    99: "Robert Schwartzman",
    100: "Roy Nissany",
    101: "Marino Sato",
    102: "Aidan Jackson",
    103: "Casper Akkerman",
    109: "Jenson Button",
    110: "David Coulthard",
    111: "Nico Rosberg",
    112: "Oscar Piastri",
    113: "Liam Lawson",
    114: "Juri Vips",
    115: "Theo Pourchaire",
    116: "Richard Verschoor",
    117: "Lirim Zendeli",
    118: "David Beckmann",
    121: "Alessio Deledda",
    122: "Bent Viscaal",
    123: "Enzo Fittipaldi",
    125: "Mark Webber",
    126: "Jacques Villenneuve",
    127: "Jake Hughes",
    128: "Frederik Vesti",
    129: "Olli Caldwell",
    130: "Logan Sargeant",
    131: "Cem Bölükbasi",
    132: "Ayumu Iwasa",
    133: "Clément Novalak",
    134: "Dennis Hauger",
    135: "Calan Williams",
    136: "Jack Doohan",
    137: "Amaury Cordeel",
    138: "Mika Hakkinen",
}


TrackIDs = {
    0: "Melbourne",
    1: "Paul Ricard",
    2: "Shanghai",
    3: "Sakhir (Bahrain)",
    4: "Catalunya",
    5: "Monaco",
    6: "Montreal",
    7: "Silverstone",
    8: "Hockenheim",
    9: "Hungaroring",
    10: "Spa",
    11: "Monza",
    12: "Singapore",
    13: "Suzuka",
    14: "Abu Dhabi",
    15: "Texas",
    16: "Brazil",
    17: "Austria",
    18: "Sochi",
    19: "Mexico",
    20: "Baku (Azerbaijan)",
    21: "Sakhir Short",
    22: "Silverstone Short",
    23: "Texas Short",
    24: "Suzuka Short",
    25: "Hanoi",
    26: "Zandvoort",
    27: "Imola",
    28: "Portimão",
    29: "Jeddah",
    30: "Miami",
}


NationalityIDs = {
    1: "American",
    2: "Argentinean",
    3: "Australian",
    4: "Austrian",
    5: "Azerbaijani",
    6: "Bahraini",
    7: "Belgian",
    8: "Bolivian",
    9: "Brazilian",
    10: "British",
    11: "Bulgarian",
    12: "Cameroonian",
    13: "Canadian",
    14: "Chilean",
    15: "Chinese",
    16: "Colombian",
    17: "Costa Rican",
    18: "Croatian",
    19: "Cypriot",
    20: "Czech",
    21: "Danish",
    22: "Dutch",
    23: "Ecuadorian",
    24: "English",
    25: "Emirian",
    26: "Estonian",
    27: "Finnish",
    28: "French",
    29: "German",
    30: "Ghanaian",
    31: "Greek",
    32: "Guatemalan",
    33: "Honduran",
    34: "Hong Konger",
    35: "Hungarian",
    36: "Icelander",
    37: "Indian",
    38: "Indonesian",
    39: "Irish",
    40: "Israeli",
    41: "Italian",
    42: "Jamaican",
    43: "Japanese",
    44: "Jordanian",
    45: "Kuwaiti",
    46: "Latvian",
    47: "Lebanese",
    48: "Lithuanian",
    49: "Luxembourger",
    50: "Malaysian",
    51: "Maltese",
    52: "Mexican",
    53: "Monegasque",
    54: "New Zealander",
    55: "Nicaraguan",
    56: "Northern Irish",
    57: "Norwegian",
    58: "Omani",
    59: "Pakistani",
    60: "Panamanian",
    61: "Paraguayan",
    62: "Peruvian",
    63: "Polish",
    64: "Portuguese",
    65: "Qatari",
    66: "Romanian",
    67: "Russian",
    68: "Salvadoran",
    69: "Saudi",
    70: "Scottish",
    71: "Serbian",
    72: "Singaporean",
    73: "Slovakian",
    74: "Slovenian",
    75: "South Korean",
    76: "South African",
    77: "Spanish",
    78: "Swedish",
    79: "Swiss",
    80: "Thai",
    81: "Turkish",
    82: "Uruguayan",
    83: "Ukrainian",
    84: "Venezuelan",
    85: "Barbadian",
    86: "Welsh",
    87: "Vietnamese",
}


GameModeIDs = {
    0: "Event Mode",
    3: "Grand Prix",
    5: "Time Trial",
    6: "Splitscreen",
    7: "Online Custom",
    8: "Online League",
    11: "Career Invitational",
    12: "Championship Invitational",
    13: "Championship",
    14: "Online Championship",
    15: "Online Weekly Event",
    19: "Career ‘22",
    20: "Career ’22 Online",
    127: "Benchmark",
}


Ruleset_IDs = {
    0: "Practice & Qualifying",
    1: "Race",
    2: "Time Trial",
    4: "Time Attack",
    6: "Checkpoint Challenge",
    8: "Autocross",
    9: "Drift",
    10: "Average Speed Zone",
    11: "Rival Duel",
}


# These surface types are from physics data and show what type of contact each wheel is experiencing.
SurfaceTypes = {
    0: "Tarmac",
    1: "Rumble strip",
    2: "Concrete",
    3: "Rock",
    4: "Gravel",
    5: "Mud",
    6: "Sand",
    7: "Grass",
    8: "Water",
    9: "Cobblestone",
    10: "Metal",
    11: "Ridged",
}


PenaltyTypes = {
    0: "Drive through",
    1: "Stop Go",
    2: "Grid penalty",
    3: "Penalty reminder",
    4: "Time penalty",
    5: "Warning",
    6: "Disqualified",
    7: "Removed from formation lap",
    8: "Parked too long timer",
    9: "Tyre regulations",
    10: "This lap invalidated",
    11: "This and next lap invalidated",
    12: "This lap invalidated without reason",
    13: "This and next lap invalidated without reason",
    14: "This and previous lap invalidated",
    15: "This and previous lap invalidated without reason",
    16: "Retired",
    17: "Black flag timer",
}


InfringementTypes = {
    0: "Blocking by slow driving",
    1: "Blocking by wrong way driving",
    2: "Reversing off the start line",
    3: "Big Collision",
    4: "Small Collision",
    5: "Collision failed to hand back position single",
    6: "Collision failed to hand back position multiple",
    7: "Corner cutting gained time",
    8: "Corner cutting overtake single",
    9: "Corner cutting overtake multiple",
    10: "Crossed pit exit lane",
    11: "Ignoring blue flags",
    12: "Ignoring yellow flags",
    13: "Ignoring drive through",
    14: "Too many drive throughs",
    15: "Drive through reminder serve within n laps",
    16: "Drive through reminder serve this lap",
    17: "Pit lane speeding",
    18: "Parked for too long",
    19: "Ignoring tyre regulations",
    20: "Too many penalties",
    21: "Multiple warnings",
    22: "Approaching disqualification",
    23: "Tyre regulations select single",
    24: "Tyre regulations select multiple",
    25: "Lap invalidated corner cutting",
    26: "Lap invalidated running wide",
    27: "Corner cutting ran wide gained time minor",
    28: "Corner cutting ran wide gained time significant",
    29: "Corner cutting ran wide gained time extreme",
    30: "Lap invalidated wall riding",
    31: "Lap invalidated flashback used",
    32: "Lap invalidated reset to track",
    33: "Blocking the pitlane",
    34: "Jump start",
    35: "Safety car to car collision",
    36: "Safety car illegal overtake",
    37: "Safety car exceeding allowed pace",
    38: "Virtual safety car exceeding allowed pace",
    39: "Formation lap below allowed speed",
    40: "Formation lap parking",
    41: "Retired mechanical failure",
    42: "Retired terminally damaged",
    43: "Safety car falling too far back",
    44: "Black flag timer",
    45: "Unserved stop go penalty",
    46: "Unserved drive through penalty",
    47: "Engine component change",
    48: "Gearbox change",
    49: "Parc Fermé change",
    50: "League grid penalty",
    51: "Retry penalty",
    52: "Illegal time gain",
    53: "Mandatory pitstop",
    54: "Attribute assignee",
}


@enum.unique
class ButtonFlag(enum.IntEnum):
    """Bit-mask values for the 'button' field in Car Telemetry Data packets."""

    CROSS = 0x00000001
    TRIANGLE = 0x00000002
    CIRCLE = 0x00000004
    SQUARE = 0x00000008
    D_PAD_LEFT = 0x00000010
    D_PAD_RIGHT = 0x00000020
    D_PAD_UP = 0x00000040
    D_PAD_DOWN = 0x00000080
    OPTIONS = 0x00000100
    L1 = 0x00000200
    R1 = 0x00000400
    L2 = 0x00000800
    R2 = 0x00001000
    LEFT_STICK_CLICK = 0x00002000
    RIGHT_STICK_CLICK = 0x00004000
    RIGHT_STICK_LEFT = 0x00008000
    RIGHT_STICK_RIGHT = 0x00010000
    RIGHT_STICK_UP = 0x00020000
    RIGHT_STICK_DOWN = 0x00040000
    SPECIAL = 0x00080000
    UDP_ACTION_1 = 0x00100000
    UDP_ACTION_2 = 0x00200000
    UDP_ACTION_3 = 0x00400000
    UDP_ACTION_4 = 0x00800000
    UDP_ACTION_5 = 0x01000000
    UDP_ACTION_6 = 0x02000000
    UDP_ACTION_7 = 0x04000000
    UDP_ACTION_8 = 0x08000000
    UDP_ACTION_9 = 0x10000000
    UDP_ACTION_10 = 0x20000000
    UDP_ACTION_11 = 0x40000000
    UDP_ACTION_12 = 0x80000000


ButtonFlag.description = {
    ButtonFlag.CROSS: "Cross or A",
    ButtonFlag.TRIANGLE: "Triangle or Y",
    ButtonFlag.CIRCLE: "Circle or B",
    ButtonFlag.SQUARE: "Square or X",
    ButtonFlag.D_PAD_LEFT: "D-pad Left",
    ButtonFlag.D_PAD_RIGHT: "D-pad Right",
    ButtonFlag.D_PAD_UP: "D-pad Up",
    ButtonFlag.D_PAD_DOWN: "D-pad Down",
    ButtonFlag.OPTIONS: "Options or Menu",
    ButtonFlag.L1: "L1 or LB",
    ButtonFlag.R1: "R1 or RB",
    ButtonFlag.L2: "L2 or LT",
    ButtonFlag.R2: "R2 or RT",
    ButtonFlag.LEFT_STICK_CLICK: "Left Stick Click",
    ButtonFlag.RIGHT_STICK_CLICK: "Right Stick Click",
    ButtonFlag.RIGHT_STICK_LEFT: "Right Stick Left",
    ButtonFlag.RIGHT_STICK_RIGHT: "Right Stick Right",
    ButtonFlag.RIGHT_STICK_UP: "Right Stick Up",
    ButtonFlag.RIGHT_STICK_DOWN: "Right Stick Down",
    ButtonFlag.SPECIAL: "Special",
    ButtonFlag.UDP_ACTION_1: "UDP Action 1",
    ButtonFlag.UDP_ACTION_2: "UDP Action 2",
    ButtonFlag.UDP_ACTION_3: "UDP Action 3",
    ButtonFlag.UDP_ACTION_4: "UDP Action 4",
    ButtonFlag.UDP_ACTION_5: "UDP Action 5",
    ButtonFlag.UDP_ACTION_6: "UDP Action 6",
    ButtonFlag.UDP_ACTION_7: "UDP Action 7",
    ButtonFlag.UDP_ACTION_8: "UDP Action 8",
    ButtonFlag.UDP_ACTION_9: "UDP Action 9",
    ButtonFlag.UDP_ACTION_10: "UDP Action 10",
    ButtonFlag.UDP_ACTION_11: "UDP Action 11",
    ButtonFlag.UDP_ACTION_12: "UDP Action 12",
}

##################################
#                                #
#  Decode UDP telemetry packets  #
#                                #
##################################

# Map from (packetFormat, packetVersion, packetId) to a specific packet type.
HeaderFieldsToPacketType = {
    (2022, 1, 0): PacketMotionData_V1,
    (2022, 1, 1): PacketSessionData_V1,
    (2022, 1, 2): PacketLapData_V1,
    (2022, 1, 3): PacketEventData_V1,
    (2022, 1, 4): PacketParticipantsData_V1,
    (2022, 1, 5): PacketCarSetupData_V1,
    (2022, 1, 6): PacketCarTelemetryData_V1,
    (2022, 1, 7): PacketCarStatusData_V1,
    (2022, 1, 8): PacketFinalClassificationData_V1,
    (2022, 1, 9): PacketLobbyInfoData_V1,
    (2022, 1, 10): PacketCarDamageData_V1,
    (2022, 1, 11): PacketSessionHistoryData_V1,
}


class UnpackError(Exception):
    pass


def unpack_udp_packet(packet: bytes) -> PackedLittleEndianStructure:
    """Convert raw UDP packet to an appropriately-typed telemetry packet.

    Args:
        packet: the contents of the UDP packet to be unpacked.

    Returns:
        The decoded packet structure.

    Raises:
        UnpackError if a problem is detected.
    """
    actual_packet_size = len(packet)

    header_size = ctypes.sizeof(PacketHeader)

    if actual_packet_size < header_size:
        raise UnpackError(
            "Bad telemetry packet: too short ({} bytes).".format(actual_packet_size)
        )

    header = PacketHeader.from_buffer_copy(packet)
    key = (header.packetFormat, header.packetVersion, header.packetId)

    if key not in HeaderFieldsToPacketType:
        raise UnpackError(
            "Bad telemetry packet: no match for key fields {!r}.".format(key)
        )

    packet_type = HeaderFieldsToPacketType[key]

    expected_packet_size = ctypes.sizeof(packet_type)

    if actual_packet_size != expected_packet_size:
        raise UnpackError(
            "Bad telemetry packet: bad size for {} packet; expected {} bytes but received {} bytes.".format(
                packet_type.__name__, expected_packet_size, actual_packet_size
            )
        )

    return packet_type.from_buffer_copy(packet)


#########################################################################
#                                                                       #
#  Verify packet sizes if this module is executed rather than imported  #
#                                                                       #
#########################################################################

if __name__ == "__main__":

    # Check all the packet sizes.

    assert ctypes.sizeof(PacketMotionData_V1) == 1464
    assert ctypes.sizeof(PacketSessionData_V1) == 632
    assert ctypes.sizeof(PacketLapData_V1) == 972
    assert ctypes.sizeof(PacketEventData_V1) == 40
    assert ctypes.sizeof(PacketParticipantsData_V1) == 1257
    assert ctypes.sizeof(PacketCarSetupData_V1) == 1102
    assert ctypes.sizeof(PacketCarTelemetryData_V1) == 1347
    assert ctypes.sizeof(PacketCarStatusData_V1) == 1058
    assert ctypes.sizeof(PacketFinalClassificationData_V1) == 1015
    assert ctypes.sizeof(PacketLobbyInfoData_V1) == 1191
    assert ctypes.sizeof(PacketCarDamageData_V1) == 948
    assert ctypes.sizeof(PacketSessionHistoryData_V1) == 1155
