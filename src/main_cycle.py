import os
import cv2
from datetime import datetime
from src.MODEL.detectron import modelmain
from src.COMMON.common import nparray_to_bytes,recent_cycle,thread_func,run_delete_old_five_in_thread
from src.camFile.cam_connections import *
from bson import ObjectId
import requests
import threading
import json
import boto3
from boto3.s3.transfer import S3Transfer
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from src.MODEL.Yolo import run_yolo_inference_single

def check_internet_connectivity():
    """Checks if the internet connection is available."""
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False
# Check internet connectivity only once
if check_internet_connectivity():
    print("Internet is available. Starting cloud upload process.")

    # Track whether internet is available for uploads
    internet_available = True
else:
    print("No internet connection. Skipping cloud upload process.")
    internet_available = False
# AWS S3 details
AWS_ACCESS_KEY = ''
AWS_SECRET_KEY = ''
BUCKET_NAME = 'eyressmartqc'
REGION_NAME = 'ap-south-1'

# Folder paths
JSON_FOLDER = "json_machine15"
INPUT_FOLDER = "input_machine15"
OUTPUT_FOLDER = "output_machine15"

# Create local folders if they don't exist
os.makedirs(JSON_FOLDER, exist_ok=True)
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Function to upload image to S3
def upload_image_to_s3(local_image_path, s3_bucket_name, s3_key):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )
    
    transfer = S3Transfer(s3_client)
    try:
        transfer.upload_file(local_image_path, s3_bucket_name, s3_key)
        print(f"Successfully uploaded {local_image_path} to {s3_bucket_name}/{s3_key}")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("AWS credentials not found or incomplete.")
    except Exception as e:
        print(f"An error occurred while uploading the file: {e}")

# Function to upload files to S3 asynchronously
def async_upload_file_to_s3(local_file_path, folder):
    def upload():
        try:
            s3_key = f"{folder}/{os.path.basename(local_file_path)}"
            upload_image_to_s3(local_file_path, BUCKET_NAME, s3_key)
            os.remove(local_file_path)  # Remove the file after upload
        except Exception as e:
            print(f"Error in async upload for {local_file_path}: {e}")
    
    threading.Thread(target=upload).start()

# Function to save and asynchronously upload JSON data to S3
def save_and_async_upload_json(insert_dict, cycle_no, formatted_datetime_db):
    sanitized_datetime = formatted_datetime_db.replace(":", "-")
    file_path = os.path.join(JSON_FOLDER, f"{cycle_no}_{sanitized_datetime}_data.json")
    
    insert_dict_serializable = {
        key: str(value) if isinstance(value, ObjectId) else value
        for key, value in insert_dict.items()
    }
    
    with open(file_path, "w") as json_file:
        json.dump(insert_dict_serializable, json_file)

    async_upload_file_to_s3(file_path, JSON_FOLDER)

def main_process_save(asi,modbus_client,MEDIA_PATH,mydb,model):
    upload_limit = 35  # Limit to 5 images per upload cycle
    upload_count = 0  # Counter to track uploaded images
    last_upload_time = time.time()  # Track last upload timestamp
    upload_interval = 3 * 60 * 60  # 3 hours in seconds
    asi.flag = False
    while (True):
        cycle_no = recent_cycle(mydb)
        print(f'Cycle Number {cycle_no}')
        current_time = datetime.now()
        formatted_datetime = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        formatted_date = datetime.strptime(formatted_datetime, "%Y-%m-%d_%H-%M-%S")
        format_date_imagename = formatted_date.strftime('%d%m%Y')
        file_raw = str(cycle_no) + '_INPUT_'+format_date_imagename+'.jpg'
        file_output = str(cycle_no) + '_OUTPUT_'+format_date_imagename+'.jpg'

        format_date_db = formatted_date.strftime('%d-%m-%Y')
        formatted_datetime_db = current_time.strftime("%d-%m-%Y %H:%M:%S")

        spm_value = modbus_client.read_holding_registers(430, 1).registers[0]
        emergency_status = modbus_client.read_holding_registers(2, 1).registers[0]
        machine_status = modbus_client.read_holding_registers(5, 1).registers[0]
        ok_count = modbus_client.read_holding_registers(421, 1).registers[0]
        ng_count = modbus_client.read_holding_registers(411, 1).registers[0]
 
        print(f"SPM: {spm_value}, Emergency: {emergency_status}, Machine: {machine_status}, "
            f"OK: {ok_count}, NG: {ng_count} ")

        if asi.flag == True:
            print("cam exit")
            break
        try:
            while (read_mem(modbus_client,61) != True):
                if asi.flag == True:
                    break
                continue
        except:
            while (modbus_client != True):
                continue
            continue
        # os.system('cls')
        start = time.time()

        if asi.flag == True:
            print("cam exit")
            break
        time.sleep(0.06)

        img = get_image(asi.device)
        img1 = cv2.merge([img, img, img])
        thread_func(nparray_to_bytes,cycle_no,mydb,file_raw,"INPUT IMAGES",img1,format_date_db,formatted_datetime_db)
        defect_image, defect_name = modelmain(cycle_no,mydb,file_output,MEDIA_PATH,img1,format_date_db,model)
        thread_func(nparray_to_bytes,cycle_no,mydb,file_output,"OUTPUT IMAGES",defect_image,format_date_db,formatted_datetime_db)

         #Decision
        if len(defect_name) >= 1:
            result = "Reject"
            write_mem(modbus_client,64, 1)
            time.sleep(0.03)
            write_mem(modbus_client,64, 0)
        else:
            result = "Accept"
            write_mem(modbus_client,63, 1)
            time.sleep(0.03)
            write_mem(modbus_client,63, 0)

        end = time.time()
        cycle_time = end-start
        print(f"Cycle Number {cycle_no} --> Decision {result}")
        
        insert_dict = {
            'cycle_no':cycle_no,
            'inspectionDatetime': formatted_datetime_db,
            'cur_date':format_date_db,
            'file_input':file_raw,
            'file_output':file_output,
            'defect_name': defect_name,
            'decision':result,
            'Machine Status':machine_status,
            'Emergency Status':emergency_status,
            'Current SPM':spm_value,
            'Accept count':ok_count,
            'Defect count':ng_count
        }
         # Check if 3 hours have passed or upload limit is reached
        current_time_sec = time.time()
        if (current_time_sec - last_upload_time >= upload_interval) or upload_count < upload_limit:
            if internet_available:  
                try:
                    # Save JSON data and upload asynchronously to S3
                    save_and_async_upload_json(insert_dict, cycle_no, formatted_datetime_db)

                    # Save images locally
                    cv2.imwrite(os.path.join(INPUT_FOLDER, file_raw), img)
                    cv2.imwrite(os.path.join(OUTPUT_FOLDER, file_output), defect_image)

                    # Upload images asynchronously to S3
                    async_upload_file_to_s3(os.path.join(INPUT_FOLDER, file_raw), INPUT_FOLDER)
                    async_upload_file_to_s3(os.path.join(OUTPUT_FOLDER, file_output), OUTPUT_FOLDER)

                    # Increment upload counter
                    upload_count += 1

                    # Reset the timer and counter if the upload interval is met
                    if current_time_sec - last_upload_time >= upload_interval:
                        last_upload_time = current_time_sec
                        upload_count = 0

                except Exception as e:
                    print(f"An error occurred during the cloud upload process: {e}")
            else:
                print("Skipping cloud upload process due to no internet connection.")
        else:
            print(f"Skipping save and upload for cycle. Conditions not met.")
        mydb["MAIN"].insert_one(insert_dict)
        end = time.time()
        cycle_time = end-start
        print(f"Cycle time {round(cycle_time,2)} in Sec")
        if cycle_time < 0.9:
            time.sleep(0.9-cycle_time)
        print("================================================")
        

def main_process_nonsave(asi, modbus_client, MEDIA_PATH, mydb, yolo_model):
    """
    Main inspection loop using ONLY YOLO logic.
    - Captures image from camera
    - Runs YOLO inference
    - Saves input & YOLO-output images
    - Sends Accept/Reject signal via Modbus
    - Logs results in MongoDB "MAIN" collection
    """

    # ---------- Create date-wise folders once (no per-iteration check) ----------
    day_folder = datetime.now().strftime("%Y-%m-%d")  # e.g., 2025-11-06
    base_day_dir = os.path.join(MEDIA_PATH, day_folder)
    CAPTURE_PATH  = os.path.join(base_day_dir, "INPUT")
    CAPTURE_PATH1 = os.path.join(base_day_dir, "YOLO_OUTPUT")
    os.makedirs(CAPTURE_PATH, exist_ok=True)
    os.makedirs(CAPTURE_PATH1, exist_ok=True)
    print(f"[Folders] Using day folder: {base_day_dir}")

    asi.flag = False
    while True:
        cycle_no = recent_cycle(mydb)
        print(f'Cycle Number {cycle_no}')

        current_time = datetime.now()
        formatted_datetime = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        formatted_date = datetime.strptime(formatted_datetime, "%Y-%m-%d_%H-%M-%S")
        format_date_imagename = formatted_date.strftime('%d%m%Y')

        # File names for saving images
        file_raw1 = os.path.join(CAPTURE_PATH,  f"{cycle_no}_INPUT_{format_date_imagename}.jpg")
        file_raw2 = os.path.join(CAPTURE_PATH1, f"{cycle_no}_OUTPUT_{format_date_imagename}.jpg")

        # File names stored in DB (relative, just names)
        file_raw = f"{cycle_no}_INPUT_{format_date_imagename}.jpg"
        file_output = f"{cycle_no}_OUTPUT_{format_date_imagename}.jpg"

        # Date/time for DB
        format_date_db = formatted_date.strftime('%d-%m-%Y')
        formatted_datetime_db = current_time.strftime("%d-%m-%Y %H:%M:%S")

        if asi.flag:
            print("cam exit")
            break

        # ---------------- Wait for Modbus trigger ----------------
        try:
            while (read_mem(modbus_client, 61) != True):
                if asi.flag:
                    break
                continue
        except:
            # If modbus read failed, wait until modbus_client is valid again
            while (modbus_client != True):
                continue
            continue

        start = time.time()

        if asi.flag:
            print("cam exit")
            break

        # Small delay before capture
        time.sleep(0.06)

        # ---------------- Capture image ----------------
        img = get_image(asi.device)          # assumed single-channel
        img1 = cv2.merge([img, img, img])    # convert to 3-channel

        # Save input image
        if not cv2.imwrite(file_raw1, img1):
            print(f"Failed to save image at {file_raw1}")
        else:
            print(f"Image saved successfully: {file_raw1}")

        # Save input image to DB (GridFS or similar) in a thread
        thread_func(
            nparray_to_bytes,
            cycle_no,
            mydb,
            file_raw,
            "INPUT IMAGES NonSave",
            img1,
            format_date_db,
            formatted_datetime_db
        )

        # ---------------- YOLO inference ONLY ----------------
        output_image, labels = run_yolo_inference_single(yolo_model, img1)
        print("YOLO labels:", labels)

        # Save YOLO output image to DB
        thread_func(
            nparray_to_bytes,
            cycle_no,
            mydb,
            file_output,
            "OUTPUT IMAGES NonSave",
            output_image,
            format_date_db,
            formatted_datetime_db
        )

        # Save YOLO output to disk
        cv2.imwrite(file_raw2, output_image)

        # ---------------- Decision using ONLY YOLO ----------------
        if len(labels) >= 1:   # at least one defect from YOLO
            result = "Reject"
            write_mem(modbus_client, 64, 1)
            time.sleep(0.02)
            write_mem(modbus_client, 64, 0)
        else:
            result = "Accept"
            write_mem(modbus_client, 63, 1)
            time.sleep(0.02)
            write_mem(modbus_client, 63, 0)

        end = time.time()
        cycle_time = end - start
        print(f"Cycle Number {cycle_no} --> Decision {result}")

        # ---------------- DB Insert (ONLY YOLO FIELDS) ----------------
        insert_dict = {
            'cycle_no': cycle_no,
            'inspectionDatetime': formatted_datetime_db,
            'cur_date': format_date_db,
            'file_input': file_raw,
            'file_output': file_output,
            'defect_name': labels,   # YOLO labels
            'decision': result,
        }
        mydb["MAIN"].insert_one(insert_dict)

        # housekeeping
        run_delete_old_five_in_thread(mydb)

        # ---------------- Cycle timing & rate limiting ----------------
        cycle_time = time.time() - start
        print(f"Cycle time {round(cycle_time, 2)} in Sec")
        if cycle_time < 0.9:
            time.sleep(0.9 - cycle_time)
        print("================================================")

    
# def main_process_nonsave(asi, modbus_client, MEDIA_PATH, mydb, model, yolo_model):
#     # ---------- Create date-wise folders once (no per-iteration check) ----------
#     day_folder = datetime.now().strftime("%Y-%m-%d")  # e.g., 2025-11-06
#     base_day_dir = os.path.join(MEDIA_PATH, day_folder)
#     CAPTURE_PATH  = os.path.join(base_day_dir, "INPUT")
#     CAPTURE_PATH1 = os.path.join(base_day_dir, "YOLO_OUTPUT")
#     CAPTURE_PATH2 = os.path.join(base_day_dir, "DETECTRON_OUTPUT")
#     os.makedirs(CAPTURE_PATH, exist_ok=True)
#     os.makedirs(CAPTURE_PATH1, exist_ok=True)
#     os.makedirs(CAPTURE_PATH2, exist_ok=True)
#     print(f"[Folders] Using day folder: {base_day_dir}")

#     asi.flag = False
#     while True:
#         cycle_no = recent_cycle(mydb)
#         print(f'Cycle Number {cycle_no}')

#         current_time = datetime.now()
#         formatted_datetime = current_time.strftime("%Y-%m-%d_%H-%M-%S")
#         formatted_date = datetime.strptime(formatted_datetime, "%Y-%m-%d_%H-%M-%S")
#         format_date_imagename = formatted_date.strftime('%d%m%Y')

#         file_raw1 = os.path.join(CAPTURE_PATH,  f"{cycle_no}_INPUT_{format_date_imagename}.jpg")
#         file_raw2 = os.path.join(CAPTURE_PATH1, f"{cycle_no}_OUTPUT_{format_date_imagename}.jpg")
#         file_raw3 = os.path.join(CAPTURE_PATH2, f"{cycle_no}_OUTPUT_{format_date_imagename}.jpg")

#         file_raw = f"{cycle_no}_INPUT_{format_date_imagename}.jpg"
#         file_output = f"{cycle_no}_OUTPUT_{format_date_imagename}.jpg"

#         format_date_db = formatted_date.strftime('%d-%m-%Y')
#         formatted_datetime_db = current_time.strftime("%d-%m-%Y %H:%M:%S")

#         if asi.flag:
#             print("cam exit")
#             break

#         try:
#             while (read_mem(modbus_client, 61) != True):
#                 if asi.flag:
#                     break
#                 continue
#         except:
#             while (modbus_client != True):
#                 continue
#             continue

#         start = time.time()

#         if asi.flag:
#             print("cam exit")
#             break

#         time.sleep(0.06)

#         img = get_image(asi.device)
#         img1 = cv2.merge([img, img, img])

#         if not cv2.imwrite(file_raw1, img1):
#             print(f"Failed to save image at {file_raw1}")
#         else:
#             print(f"Image saved successfully: {file_raw1}")

#         thread_func(nparray_to_bytes, cycle_no, mydb, file_raw, "INPUT IMAGES NonSave",
#                     img1, format_date_db, formatted_datetime_db)

#         output_image, labels = run_yolo_inference_single(yolo_model, img1)
#         defect_image, defect_name = modelmain(cycle_no, mydb, file_output, MEDIA_PATH,
#                                               img1, format_date_db, model)
#         print("defect_name:", defect_name)

#         thread_func(nparray_to_bytes, cycle_no, mydb, file_output, "OUTPUT IMAGES NonSave",
#                     output_image, format_date_db, formatted_datetime_db)

#         cv2.imwrite(file_raw2, output_image)
#         cv2.imwrite(file_raw3, defect_image)

#         # Decision
#         if len(labels) >= 1 or (defect_name and len(defect_name) > 0):
#             result = "Reject"
#             write_mem(modbus_client, 64, 1)
#             time.sleep(0.02)
#             write_mem(modbus_client, 64, 0)
#         else:
#             result = "Accept"
#             write_mem(modbus_client, 63, 1)
#             time.sleep(0.02)
#             write_mem(modbus_client, 63, 0)

#         end = time.time()
#         cycle_time = end - start
#         print(f"Cycle Number {cycle_no} --> Decision {result}")

#         insert_dict = {
#             'cycle_no': cycle_no,
#             'inspectionDatetime': formatted_datetime_db,
#             'cur_date': format_date_db,
#             'file_input': file_raw,
#             'file_output': file_output,
#             'defect_name': labels,
#             'detectron_defect': defect_name,
#             'decision': result,
#         }
#         mydb["MAIN"].insert_one(insert_dict)

#         # housekeeping
#         run_delete_old_five_in_thread(mydb)

#         cycle_time = time.time() - start
#         print(f"Cycle time {round(cycle_time, 2)} in Sec")
#         if cycle_time < 0.9:
#             time.sleep(0.9 - cycle_time)
#         print("================================================")



def main_process_save_raw(asi, modbus_client, model):
    ROOT_DIR = os.getcwd()
    MEDIA_PATH = os.path.join(ROOT_DIR, 'media')
    CAPTURE_PATH = os.path.join(MEDIA_PATH, 'Rust_Input_images')
    CAPTURE_PATH1 = os.path.join(MEDIA_PATH, 'Rust_Output_images')
 
    if not os.path.exists(MEDIA_PATH):
        os.makedirs(MEDIA_PATH)
    if not os.path.exists(CAPTURE_PATH):
        os.makedirs(CAPTURE_PATH)
    if not os.path.exists(CAPTURE_PATH1):
        os.makedirs(CAPTURE_PATH1)
 
    asi.flag = False
    cycle_count = 0
    minute_cycle_count = 0
    start_minute = time.time()  # Start time for one-minute tracking
 
    while True:
        current_time = datetime.now()
        format_date_imagename = current_time.strftime('%d%m%Y_%H%M%S_%f')[:-3]
        file_raw = os.path.join(CAPTURE_PATH, f"_INPUT_{format_date_imagename}.jpg")
        file_raw1 = os.path.join(CAPTURE_PATH1, f"_OUTPUT_{format_date_imagename}.jpg")
 
        if asi.flag:
            print("cam exit")
            break
 
        try:
            while read_mem(modbus_client, 61) != True:
                if asi.flag:
                    break
                continue
        except:
            while modbus_client != True:
                continue
            continue
 
        start = time.time()
        if asi.flag:
            print("cam exit")
            break
        time.sleep(0.06)    
        print("Trigger received, starting image capture.")
        img = get_image(asi.device)
        if img is None:
            print("Error: Failed to capture image.")
            continue
        img1 = cv2.merge([img, img, img])
        if not cv2.imwrite(file_raw, img1):
            print(f"Failed to save image at {file_raw}")
        else:
            print(f"Image saved successfully: {file_raw}")
        defect_image, defect_name = modelmain(file_raw1, MEDIA_PATH, img1, model)
        cv2.imwrite(file_raw1,defect_image)
        if len(defect_name) >= 1: 
            result = "Reject"
            write_mem(modbus_client, 64, 1)
            time.sleep(0.03)
            write_mem(modbus_client, 64, 0)
        else:
            result = "Accept"
            write_mem(modbus_client, 63, 1)
            time.sleep(0.03)
            write_mem(modbus_client, 63, 0)
 
        print(f"Decision {result}")
 
        end = time.time()
        cycle_time = end - start
        print(f"Cycle time {round(cycle_time, 2)} sec")
 
        cycle_count += 1  # Total cycle count
        minute_cycle_count += 1  # Per minute cycle count
 
        # Check if one minute has passed
        if time.time() - start_minute >= 60:
            print(f"Cycles in the last minute: {minute_cycle_count}")
            minute_cycle_count = 0  # Reset minute cycle count
            start_minute = time.time()  # Restart the timer
 
        print(f"Total cycle count: {cycle_count}")
        print("====================================================")
        


