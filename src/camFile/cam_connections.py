
from arena_api.callback import callback, callback_function
from pymodbus.client.sync import ModbusTcpClient
import numpy as np
import ctypes
from arena_api.buffer import *
from arena_api.system import system
import time
import sys
# from src.COMMON.common import load_env
import warnings
warnings.filterwarnings("ignore")


def get_image(device):
    buffer = device.get_buffer()
    a = convert_buffer_dev1(buffer)
    device.requeue_buffer(buffer)
    return a


def convert_buffer_dev1(buffer):
    count = 2
    num_channels = 3
    item = BufferFactory.copy(buffer)
    buffer_bytes_per_pixel = int(len(item.data) / (item.width * item.height))
    array = (ctypes.c_ubyte * num_channels * item.width *
             item.height).from_address(ctypes.addressof(item.pbytes))
    npndarray = np.ndarray(buffer=array, dtype=np.uint8, shape=(
        item.height, item.width, buffer_bytes_per_pixel))

    return npndarray

def configure_trigger_acquire_software(device):
    nodemap=device.nodemap
    nodemap['TriggerSource'].value = 'Software'
    trigger_armed=False
    while trigger_armed is False:
        trigger_armed= bool(nodemap['TriggerArmed'].value)
    # time.sleep(delay)
    nodemap['TriggerSoftware'].execute()
    buffer=device.get_buffer()
    a = convert_buffer_dev1(buffer)
    device.requeue_buffer(buffer)
    return a

def decimalToBinary(n):
    return bin(n).replace("0b", "")


def Convert(string):
    list1 = []
    list1[:0] = string
    return list1


def convert_to_bcd(decimal):
    place, bcd = 0, 0
    while decimal > 0:
        nibble = decimal % 10
        bcd += nibble << place
        decimal /= 10
        place += 4
    return bcd


@callback_function.system.on_device_disconnected
def print_disconnected_device_info(device):
    '''
    Print information from the callback
            When registered device is disconnected System fire a callback which pass
            disconnected device to this function.

    '''
    print('Device was disconnected:')
    while (len(system.device_infos) == 0):
        continue
    if device.is_connected() is True:
        print('Device is connected\n')
        device.stop_stream()

    # re_init()

def create_devices_with_tries():
    tries = 0
    tries_max = 6
    sleep_time_secs = 10
    while tries < tries_max:  # Wait for device for 60 seconds
        devices = system.create_device()
        if not devices:
            # # print(
            #     f'Try {tries + 1} of {tries_max}: waiting for {sleep_time_secs} '
            #     f'secs for a device to be connected!')
            for sec_count in range(sleep_time_secs):
                time.sleep(1)
                # print(f'{sec_count + 1} seconds passed ',
                #       '.' * sec_count, end='\r')
            tries += 1
        else:
            # print(f'Created {len(devices)} device(s)')
            return devices
    else:
        raise Exception(f'No device found! Please connect a device and run '
                        f'the example again.')


def capture_frame(device):
    num_channels = 3
    buffer = device.get_buffer()
    item = BufferFactory.copy(buffer)
    device.requeue_buffer(buffer)
    buffer_bytes_per_pixel = int(len(item.data) / (item.width * item.height))
    array = (ctypes.c_ubyte * num_channels * item.width *
             item.height).from_address(ctypes.addressof(item.pbytes))
    npndarray = np.ndarray(buffer=array, dtype=np.uint8, shape=(
        item.height, item.width, buffer_bytes_per_pixel))
    # cv2.imwrite('img1.jpg', npndarray)
    # BufferFactory.destroy(item)
    return npndarray


def setup(device, exposure_time, gain):
    nodemap = device.nodemap
    if not nodemap['TriggerArmed'].value:
        nodemap['TriggerSource'].value="Software"
        nodemap['TriggerSoftware'].execute()
    # nodemap.get_node("Height").value = height
    nodemap.get_node("ExposureAuto").value = 'Off'
    nodemap.get_node("ExposureTime").value = float(exposure_time)
    # nodemap.get_node("Gain").value = float(gain)
    nodemap.get_node("PixelFormat").value = 'Mono8'
    nodemap.get_node("TriggerDelay").value = float(40000)

    num_channels = 3
    tl_stream_nodemap = device.tl_stream_nodemap
    tl_stream_nodemap["StreamBufferHandlingMode"].value = "NewestOnly"
    tl_stream_nodemap['StreamAutoNegotiatePacketSize'].value = True
    tl_stream_nodemap['StreamPacketResendEnable'].value = True
    nodemap['TriggerSelector'].value = 'FrameStart'
    if nodemap['TriggerMode'].value == 'Off':
        nodemap['TriggerMode'].value = 'On'
    nodemap['TriggerSource'].value = 'Line0'
    tl_stream_nodemap = device.tl_stream_nodemap
    tl_stream_nodemap['StreamAutoNegotiatePacketSize'].value = True
    tl_stream_nodemap['StreamPacketResendEnable'].value = True
    return num_channels


# def camera_init():
#     device_infos = system.device_infos
#     cam_no = str(cam_id)
#     for i in range(0,len(device_infos)):
#         serial = device_infos[i]['serial']
#         if serial == cam_no:
#             devices = system.create_device(device_infos[i])
#             return devices[0]

def create_device_from_serial_number(serial_number):
    camera_found = False

    device_infos = None
    selected_index = None

    device_infos = system.device_infos
    for i in range(len(device_infos)):
        if serial_number == device_infos[i]['serial']:
            selected_index = i
            camera_found = True
            break

    if camera_found == True:
        selected_model = device_infos[selected_index]['model']
        print(f"Create device: {selected_model}...")
        device = system.create_device(device_infos=device_infos[selected_index])[0]
    else:
        raise Exception(f"Serial number {serial_number} cannot be found")
        
    return device

def read_mem(client,a):
    mem = a+2048
    rr = client.read_coils(mem, 1, unit=1)
    return rr.bits[0]

def write_mem(client,a, val):
    mem = a+2048
    client.write_coil(mem, val)

def write_mem_hold(client,a, val):
    pass
    mem = a+420
    client.write_registers(mem, val)

# device = camera_init()
# print(device,'device')
# exposure_time = 1502  # change to desired value
# gain = 7  # change to desired value
# num_channels = setup(device, exposure_time, gain)
# # if not modbus_client:
# #     print("PLC error ")
# #     sys.exit(0)
# device.start_stream()
# a = configure_trigger_acquire_software(device)
# print(a)
# asi.device = device