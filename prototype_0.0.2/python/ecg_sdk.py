"""
Translating the polar SDK to Python.
"""
from __future__ import annotations
from typing import Dict, Tuple
from enum import Enum
#from abc import ABC, abstractmethod

# CONSTANTS & ENUMS:
# ------------------------------------------------------------

# starting point for timestamps measured in nanoseconds
EPOCHE_TIMESTAMP = "2000-01-01-00:00:00-UTC"

class MeasurementUUIDs(Enum):
    PMD_SERVICE = "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8"
    PMD_CONTROL_POINT = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
    PMD_DATA_MTU_CHARACTERISTICS = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"

class RecordingType(Enum):
    ONLINE = 0
    OFFLINE = 1

class ControlPointCmd(Enum):
    GET_MEASUREMENT_SETTINGS = 1
    REQUEST_MEASUREMENT_START = 2
    REQUEST_MEASUREMENT_STOP = 3

class MeasurementTypes(Enum):
    ECG = 0
    PPG = 1
    ACC = 2
    PPI = 3
    GYRO = 5
    MAGNETOMETER = 6
    SDK_MODE = 9
    LOCATION = 10
    PRESSURE = 11
    TEMPERATURE = 12

class SettingType(Enum):
    SAMPLE_RATE_IN_HZ = 0
    RESOLUTION_IN_BITS = 1
    RANGE_PLUS_MINUS_UNIT = 2
    RANGE_MILLI_UNIT = 3
    NUMBER_OF_CHANNELS = 4
    CONVERSION_FACTOR = 5
    SECURITY = 6
    UNKNOWN = 0xff

    # def field_size(self) -> int:
    #     match self:
    #         case self.SAMPLE_RATE_IN_HZ:
    #             return 2
    #         case self.RESOLUTION_IN_BITS:
    #             return 2
    #         case self.RANGE_PLUS_MINUS_UNIT:
    #             return 2
    #         case self.RANGE_MILLI_UNIT:
    #             return 4
    #         case self.NUMBER_OF_CHANNELS:
    #             return 1
    #         case self.CONVERSION_FACTOR:
    #             return 4
    #     return 0

    def field_size(self) -> int:
        """Match was introduced with Python 3.10"""
        sizes = {
            SettingType.SAMPLE_RATE_IN_HZ: 2,
            SettingType.RESOLUTION_IN_BITS: 2,
            SettingType.RANGE_PLUS_MINUS_UNIT: 2,
            SettingType.RANGE_MILLI_UNIT: 4,
            SettingType.NUMBER_OF_CHANNELS: 1,
            SettingType.CONVERSION_FACTOR: 4,
        }
        return sizes.get(self, 0)

    


class SampleSize(Enum):
    ECG_FRAME = 3


class ResponseCodes(Enum):
    SUCCESS = 0
    ERROR_INVALID_OP_CODE = 1
    ERROR_INVALID_MEASUREMENT_TYPE = 2
    ERROR_NOT_SUPPORTED = 3
    ERROR_INVALID_LENGTH = 4
    ERROR_INVALID_PARAMETER = 5
    ERROR_INVALID_STATE = 6
    UNKNOWN_ERROR = 0xffff


# PARSERS:
# ------------------------------------------------------------
SettingsDict = Dict[SettingType, Tuple[int, ...]]


class Parse():
    @classmethod
    def parse_settings_data(cls, data: bytes) -> SettingsDict:
        """
        Parses *data* from a bytes object into a dictionary of the structure:
        
        SettingsDict = Dict[SettingType, Tuple[int]].
        """
        offset, settings = 0,  {}

        while (offset + 2) < len(data):
            data_type, data_length = SettingType(data[offset]), data[offset + 1]
            offset += 2

            #  step = setting_type_to_field_size.get(data_type, 1)
            step = data_type.field_size() if data_type.field_size() > 0 else 1
            end = offset + data_length * step // data_type.field_size()

            settings[data_type] = tuple(int.from_bytes(data[_:_ + step], 'little')
                                        for _ in range(offset, end, step))

            offset = end

        return settings

    @classmethod
    def serialize_settings_data(cls, settings: SettingsDict) -> bytes:
        """
        Serializes the information in *settings* into *bytes*.

        Follows repeatedly a TLV-scheme:
    
        - first byte:    type of data
    
        - second byte:   number of bytes used to parse
    
        - third to nth byte: value parsed from little endian & unsigned
        """
        acc = b''

        for s in settings.keys():
            data_type = int.to_bytes(SettingType[s.name].value,
                                     length = 1,
                                     byteorder = 'little',
                                     signed = False)

            data_length = int.to_bytes(len(settings[s]),
                                       length = 1,
                                       byteorder = 'little',
                                       signed = False)

            acc += data_type + data_length

            for val in settings[s]:
                acc += int.to_bytes(val,
                                    length = s.field_size(), #setting_type_to_field_size[s],
                                    byteorder = 'little',
                                    signed = False)

        return acc

    @classmethod
    def parse_ecg_samples(cls, data: bytes) -> Tuple[int, Tuple[int, ...]]:
        # measurement_type = data[0]
        sample_size = SampleSize.ECG_FRAME.value
        time_stamp = int.from_bytes(data[1:9], 'little')
        #frame_type = data[9]
        raw_samples = data[10:]
        length = len(raw_samples)
        samples = []

        for _ in range(0, length, sample_size):
            sample = int.from_bytes(raw_samples[_ : _ + sample_size], 'little', signed = True)
            samples.append(sample)

        return time_stamp, tuple(samples)


class ParseResponse():
    def __init__(self, data: bytes) -> None:
        self.response = data[0]  # 0xF0: Control Point Response
        self.op_code = ControlPointCmd(data[1]).name
        self.measurement_type = MeasurementTypes(data[2]).name
        self.error_code = ResponseCodes(data[3]).name
        self.values = Parse().parse_settings_data(data[5:]) if (data[4] != 0) else None


class ParseSupportedFeature:
    def __init__(self, data):
        self.ecg = (data[1] & 0x01) != 0
        self.ppg = (data[1] & 0x02) != 0
        self.acc = (data[1] & 0x04) != 0
        self.ppi = (data[1] & 0x08) != 0
        self.bio_z = (data[1] & 0x10) != 0
        self.gyro = (data[1] & 0x20) != 0
        self.magnetometer = (data[1] & 0x40) != 0
        self.barometer = (data[1] & 0x80) != 0
        self.ambient = (data[2] & 0x01) != 0


class BuildCmd(Parse):
    FIRST_BYTE_OFFLINE_MEASUREMENT = \
        RecordingType.OFFLINE.value << 7 | MeasurementTypes.ECG.value
    
    @classmethod
    def build_start_cmd(cls, m_type: MeasurementTypes, settings: SettingsDict):
        header = bytes((ControlPointCmd.REQUEST_MEASUREMENT_START.value,
                        m_type.value))
        payload = cls.serialize_settings_data(settings)
        return header + payload
    
    @classmethod
    def build_stop_cmd(cls, m_type: MeasurementTypes) -> bytes:
        return bytes((ControlPointCmd.REQUEST_MEASUREMENT_STOP.value,
                      m_type.value))
    
    @classmethod
    def build_settings_cmd(cls, m_type: MeasurementTypes) -> bytes:
        return bytes((ControlPointCmd.GET_MEASUREMENT_SETTINGS.value,
                      m_type.value))

    
class ECG(Parse):
    """Draft for API."""
    PMD_SERVICE_UUID = MeasurementUUIDs.PMD_SERVICE.value
    CONTROL_POINT_UUID = MeasurementUUIDs.PMD_CONTROL_POINT.value
    DATA_STREAM_UUID = MeasurementUUIDs.PMD_DATA_MTU_CHARACTERISTICS.value
    
    START_CMD = BuildCmd.build_start_cmd(MeasurementTypes.ECG,
                                         {SettingType.SAMPLE_RATE_IN_HZ:(130,),
                                          SettingType.RESOLUTION_IN_BITS: (14,)})
    
    SETTINGS_CMD = BuildCmd.build_settings_cmd(MeasurementTypes.ECG)


    STOP_CMD = BuildCmd.build_stop_cmd(MeasurementTypes.ECG)


    @classmethod
    def samples(cls, data: bytes) -> Tuple[int, Tuple[int, ...]]:
        return cls.parse_ecg_samples(data)

    @staticmethod
    def response(data: bytes) -> ParseResponse:
        return ParseResponse(data)



if __name__ == '__main__':
    response = ParseResponse(b'\xf0\x01\x00\x00\x00\x00\x01\x82\x00\x01\x01\x0e\x00')
    parsed_settings = response.values
    
    # review & add defensiveness
    # test cases & documentation
    # add more features
