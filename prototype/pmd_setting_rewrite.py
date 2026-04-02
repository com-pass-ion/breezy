"""
Translating the polar SDK to Python.
"""
from enum import Enum

measurement_uuids = {
    "pmd_service": "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8",
    "pmd_control_point": "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8",
    "pmd_data_mtu_characteristics": "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"
}

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
    """
    Enum holding *SettingType*s used in *setting_type_to_field_size*
    to look for field sizes.
    """
    SAMPLE_RATE_IN_HZ = 0
    RESOLUTION_IN_BITS = 1
    RANGE_PLUS_MINUS_UNIT = 2
    RANGE_MILLI_UNIT = 3
    NUMBER_OF_CHANNELS = 4
    CONVERSION_FACTOR = 5
    SECURITY = 6
    UNKNOWN = 0xff


setting_type_to_field_size = {
    SettingType.SAMPLE_RATE_IN_HZ: 2,
    SettingType.RESOLUTION_IN_BITS: 2,
    SettingType.RANGE_PLUS_MINUS_UNIT: 2,
    SettingType.RANGE_MILLI_UNIT: 4,
    SettingType.NUMBER_OF_CHANNELS: 1,
    SettingType.CONVERSION_FACTOR: 4
}

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

SettingsDict = dict[SettingType, tuple[int, ...]]


class ParseResponse():
    def __init__(self, data: bytes) -> None:
        self.response = data[0] # 0xF0: Control Point Response
        self.op_code = ControlPointCmd(data[1]).name
        self.measurement_type = MeasurementTypes(data[2]).name
        self.error_code = ResponseCodes(data[3]).name
        self.values = parse_settings_data(data[5:]) if (data[4] != 0) else None


class SupportedFeature():
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

def parse_settings_data(data: bytes) -> SettingsDict:
    """
    Parses *data* from a bytes object into a dictionary of the structure:

    SettingsDict = dict[SettingType, tuple[int]].
    """
    offset, settings = 0,  {}

    while (offset + 2) < len(data):
        data_type, data_length = SettingType(data[offset]), data[offset + 1]
        offset += 2

        step = setting_type_to_field_size.get(data_type, 1)
        end = offset + data_length * step

        settings[data_type] = tuple(int.from_bytes(data[_:_+step], 'little')
                     for _ in range(offset, end, step))

        offset = end

    return settings



def serialize_settings_data(settings: SettingsDict) -> bytes:
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
                                length = setting_type_to_field_size[s],
                                byteorder = 'little',
                                signed = False)

    return acc


epoch = "2000-01-01-00:00:00-UTC" # starting point for timestamps measured in nanoseconds

def build_ecg_samples(data: bytes) -> tuple[int, tuple[int, ...]]:
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


def build_start_cmd(m_type: MeasurementTypes, settings: SettingsDict):
    header = bytes((ControlPointCmd.REQUEST_MEASUREMENT_START.value,
              m_type.value))
    payload = serialize_settings_data(settings)
    return header + payload


def build_stop_cmd(m_type: MeasurementTypes) -> bytes:
    return bytes((ControlPointCmd.REQUEST_MEASUREMENT_STOP.value,
                  m_type.value))

def build_settings_cmd(m_type: MeasurementTypes) -> bytes:
    return bytes((ControlPointCmd.GET_MEASUREMENT_SETTINGS.value,
                 m_type.value))

first_byte_offline_measurement = RecordingType.OFFLINE.value << 7 | MeasurementTypes.ECG.value

##### TEST CASES:
test_requests = {
    "acc_settings": b'\x01\x02',
    "ecg_settings": b'\x01\x00',
    "ppg_settings": b'\x01\x01',
    "acc_start_h10":b'\x02\x02\x02\x01\x08\x00\x00\x01\xc8\x00\x01\x01\x10\x00',
    "acc_start_delta_framed_h10": b'\x02\x02\x00\x01\x34\x00\x01\x01\x10\x00\x02\x01\x08\x00\x04\x01\x03',
    "acc_stop": b'\x03\x02',
    "ecg_stop": b'\x03\x00',
    "start_sdk_mode": b'\x02\x09',
    "stop_sdk_mode": b'\x03\x09',
    "sdk_mode_settings": b'\x04\x02'
}

test_responses = {
    "att_characteristic_read": b'\x0f\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    "acc_settings_h10": b'\xf0\x01\x02\x00\x00\x00\x04\x19\x00\x32\x00\x64\x00\xc8\x00\x01\x01\x10\x00\x02\x03\x02\x00\x04\x00\x08\x00',
    "acc_settings_variety": b'\xf0\x01\x02\x00\x00\x00\x01\x34\x00\x01\x01\x10\x00\x02\x01\x08\x00\x04\x01\x03',
    "ecg_settings": b'\xf0\x01\x00\x00\x00\x00\x01\x82\x00\x01\x01\x0e\x00',
    "ppg_settings": b'\xf0\x01\x01\x00\x00\x00\x01\x82\x00\x01\x01\x16\x00',
    "acc_started_response": b'\xf0\x02\x02\x00\x00\x01',
    "acc_started_stream": b'\x02\xea\x54\xa2\x42\x8b\x45\x52\x08\x01\x45\xff\xe4\xff\xb5\x03\x45\xff\xe4\xff\xb8\x03',
    "acc_started_delta_framed_response": b'\xf0\x02\x02\x00\x00\x05\x01\x40\xda\x7f\x39',
    "acc_started_delta_framed_stream": b'\x02\x64\x6c\x76\xc4\x3c\xc6\x7f\x07\x80\xd0\xff\x65\x01\xe4\x0f\x08\x1d\xfc\x07\xff\x0c\x13\xf2\x11\xf1\x1a\xf9\xee\xf8\xef\x0c\x03\x09\xf2',
    "acc_stopped": b'\xf0\x03\x02\x00\x00',
    "ecg_stopped": b'\xf0\x03\x02\x00\x00',
    "start_sdk_mode": b'\xf0\x02\x09\x00\x00',
    "stop_sdk_mode": b'\xf0\x03\x09\x00\x00',
    "sdk_mode_settings": b'\xf0\x01\x02\x00\x00\x00\x04\x19\x00\x32\x00\x64\x00\xc8\x00\x01\x01\x10\x00\x02\x03\x02\x00\x04\x00\x08\x00'
}




if __name__ == '__main__':
    start_cmd = build_start_cmd(MeasurementTypes.ECG, {SettingType.SAMPLE_RATE_IN_HZ: (130,)})
    stop_cmd = build_stop_cmd(MeasurementTypes.ECG)
    settings_cmd = build_settings_cmd(MeasurementTypes.ECG)
    response = ParseResponse(b'\xf0\x01\x00\x00\x00\x00\x01\x82\x00\x01\x01\x0e\x00')
    parsed_settings = response.values
    
# 0. establish bluetoth connection
# 1. send pmd_service uuid
# 2. send control_point_cmd to start measurement
# 3. parse data
# 4. send control point cmd to stop measurement

# x. request and parse settings


