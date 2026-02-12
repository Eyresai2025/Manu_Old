import tkinter as tk
from tkinter import ttk
from datetime import datetime,timedelta
import pymongo
from PIL import Image, ImageTk
from io import BytesIO
import threading
from pymongo import MongoClient
import warnings
warnings.filterwarnings("ignore")
import os
import time
from tkcalendar import Calendar
import cv2
from pymodbus.client.sync import ModbusTcpClient
import torch
from tkinter import messagebox
from gridfs import GridFSBucket
import numpy as np
import pandas as pd
from ultralytics import YOLO

from src.COMMON.common import db_to_images_bulk_output,db_to_images_bulk_raw,load_env,run_delete_old_five_in_thread
from src.MODEL.detectron import torchy_warmup

ROOT_DIR = os.getcwd()
MEDIA_PATH = os.path.join(ROOT_DIR,'media')

env_vars = load_env(ROOT_DIR)
db_url = env_vars.get('DATABASE_URL')
db_name = env_vars.get('DATABASE_NAME')
plc_ip = env_vars.get('PLC_IP')
exp_time = env_vars.get('EXPOSURE_TIME')
weight_path_old = env_vars.get('WEIGHT_FILE_OLD')
# weight_path_three = env_vars.get('WEIGHT_FILE_0.3')
# weight_path_four = env_vars.get('WEIGHT_FILE_0.4')
weight_path_yolo = env_vars.get('WEIGHT_YOLO_FILE')
serial_number = env_vars.get('CAMERA_ID')
deployment = env_vars.get('DEPLOYMENT')
machine_no = env_vars.get('MACHINE_NO')


if deployment == "True":
    from src.main_cycle import main_process_save,main_process_nonsave,main_process_save_raw
    from src.camFile.cam_connections import *
else:
    from src.main import main_process_save,main_process_nonsave


# DB initalization
myclient = MongoClient(db_url)
mydb = myclient[db_name]

mycollec = mydb["MAIN"]
mycollec.create_index([("cur_date", pymongo.ASCENDING)])

#PLC
client = ModbusTcpClient(str(plc_ip))
modbus_client = client.connect()
print(modbus_client,'modbus_client')

if deployment == "True":
    # GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_path = os.path.join(MEDIA_PATH, f'WEIGHTS/{weight_path_old}')
    print(f"Loading model from: {model_path}")
    model = torch.jit.load(model_path).to(device)
    torch.backends.cudnn.benchmark = True
    torch.cuda.amp.autocast()
    torch.cuda.empty_cache()
else:
    # CPU
    device = torch.device("cpu")
    model_path = os.path.join(MEDIA_PATH, f'WEIGHTS/{weight_path_old}')
    print(f"Loading model from: {model_path}")
    model = torch.jit.load(model_path, map_location=device) # Load model to CPU

yolo_model = YOLO(os.path.join(MEDIA_PATH,f'WEIGHTS/{weight_path_yolo}')).to('cuda' if torch.cuda.is_available() else 'cpu')
print("YOlO model loaded successfully")

global flag
flag = False


class falg:
    def __init__(self):
        self.flag = False
        self.device = 0

asi = falg()

if deployment == "True":
    device = create_device_from_serial_number(serial_number)
    exposure_time = float(exp_time)  # change to desired value
    print(f"ExposureTime is:{exposure_time}")
    gain = 3.0 # change to desired value
    print(f"Gain is: {gain}")
    num_channels = setup(device, exposure_time, gain)
    nodemap = device.nodemap  # Get the nodemap
    # Set width and height
    try:
        width_node = nodemap.get_node("Width")
        height_node = nodemap.get_node("Height")
        if width_node.is_writable and height_node.is_writable:
            width_node.value = 1200
            height_node.value = 1200
            print("Width and Height have been set to 1120.")
        else:
            print("Width or Height is not writable.")
    except Exception as e:
        print(f"Error setting Width/Height: {e}")
        sys.exit(1)
    # Set OffsetX and OffsetY
    try:
        offsetx_node = nodemap.get_node("OffsetX")
        offsety_node = nodemap.get_node("OffsetY")
        if offsetx_node.is_writable and offsety_node.is_writable:
            offsetx_node.value = 448
            offsety_node.value = 0
            print("OffsetX and OffsetY have been set.")
        else:
            print("OffsetX or OffsetY is not writable.")
    except Exception as e:
        print(f"Error setting OffsetX/OffsetY: {e}")
        sys.exit(1)
    # Disable automatic exposure
    try:
        exposure_auto_node = nodemap.get_node("ExposureAuto")
        exposure_auto_node.value = 'Off'
        print("Automatic exposure has been turned off.")
    except Exception as e:
        print(f"Error setting ExposureAuto: {e}")
        sys.exit(1)
    # Ensure Trigger Mode is 'On'
    try:
        trigger_mode_node = nodemap.get_node("TriggerMode")
        if trigger_mode_node.value == 'Off':
            trigger_mode_node.value = 'On'
            print("Trigger Mode was 'Off' and has been set to 'On'")
        else:
            print("Trigger Mode is already 'On'")
    except Exception as e:
        print(f"Error setting TriggerMode: {e}")
        sys.exit(1)
    # Set PixelFormat to 'Mono8'
    pixel_format_node = nodemap.get_node("PixelFormat")
    if pixel_format_node.is_writable:
        pixel_format_node.value = 'Mono8'
        print("Pixel Format has been set to 'Mono8'.")
    else:
        print("Pixel Format is not writable or cannot be set to 'Mono8'.")
    # Confirm the current trigger mode status
    trigger_mode = nodemap.get_node("TriggerMode").value
    print(f"Trigger Mode is: {trigger_mode}")
    if not modbus_client:
        print("PLC error ")
        sys.exit(0)
    device.start_stream()
    asi.device = device
else:
    pass

img = cv2.imread(os.path.join(MEDIA_PATH,'RAW IMAGES/1.jpg'))

torchy_warmup(img,model)
torchy_warmup(img,model)
torchy_warmup(img,model)


# main_process(asi,modbus_client,MEDIA_PATH,mydb)


win = tk.Tk()
win.title("Manu Yantrayalay GUI")

# win.attributes('-fullscreen', True)
win.iconbitmap(os.path.join(MEDIA_PATH,"GUI IMAGES/Manu_logo.ico"))


image1 = Image.open(
    "media/GUI IMAGES/RadomeTech Logo (570 × 161 px) No Background.png")
# Resize the image to a new width and height
new_width = 200
new_height = 50
resized_image1 = image1.resize((new_width, new_height))
test = ImageTk.PhotoImage(resized_image1)
label1 = tk.Label(image=test)
label1.image = test
label1.place(relx=0.84,rely=0)

image1 = Image.open(
    "media/GUI IMAGES/Manu_logo.png")
# Resize the image to a new width and height
new_width = 200
new_height = 50
resized_image1 = image1.resize((new_width, new_height))
test = ImageTk.PhotoImage(resized_image1)
label1 = tk.Label(image=test)
label1.image = test
label1.place(relx=0,rely=0)

image1 = Image.open(
    "media/GUI IMAGES/SmartQC_logo.png")
# Resize the image to a new width and height
new_width = 100
new_height = 52
resized_image1 = image1.resize((new_width, new_height))
test = ImageTk.PhotoImage(resized_image1)
label1 = tk.Label(image=test)
label1.image = test
label1.place(relx=0.923,rely=0.92)

copy_right = "© 2024 Radome Technologies and Services. All rights reserved"
tk.Label(win, text=copy_right, font=("Helvetica", 10)).place(relx=0,rely=0.96)

def get_previous_image(fs_files):
    latest_and_previous_documents = list(fs_files.find(sort=[("uploadDate", pymongo.DESCENDING)], limit=2))
    if not latest_and_previous_documents: 
        return None
    elif len(latest_and_previous_documents) == 1:
        return None
    else:
        return latest_and_previous_documents[1]['_id']

def get_current_image(fs_files):
    latest_and_previous_documents = list(fs_files.find(sort=[("uploadDate", pymongo.DESCENDING)], limit=2))
    if not latest_and_previous_documents:
        return None
    elif len(latest_and_previous_documents) == 1:
        return latest_and_previous_documents[0]['_id']
    elif len(latest_and_previous_documents) == 2:
        return latest_and_previous_documents[0]['_id']


def display_image_pre(image):
    new_width = 432
    new_height = 270
    resized_image = image.resize((new_width, new_height))
    photo_image = ImageTk.PhotoImage(resized_image)
    label5.config(image=photo_image)
    label5.image = photo_image

def display_image_cur(image):
    new_width = 432
    new_height = 270
    resized_image = image.resize((new_width, new_height))
    photo_image = ImageTk.PhotoImage(resized_image)
    label4.config(image=photo_image)
    label4.image = photo_image

def update_image(fs_files,fs_chunks):
    try:
        latest = get_current_image(fs_files)
        if latest != None:
            chunks = fs_chunks.find({"files_id": latest})
            binary_data = b"".join(chunk["data"] for chunk in chunks)
            with BytesIO(binary_data) as f:
                image = Image.open(f)
                display_image_cur(image)
        else:
            noimage = Image.open(os.path.join(MEDIA_PATH, 'GUI IMAGES/no_image.jpg'))
            display_image_cur(noimage)
    except Exception as e:
        print(f"An error occurred in update_image: {e}")

    label4.after(500, update_image,fs_files,fs_chunks)

tk.Label(win, text="CURRENT IMAGE", font=(
    'Helvetica', 16, 'bold')).place(relx=0.1,rely=0.1)
label4 = tk.Label(win)
label4.place(relx=0.02,rely=0.14)

# update_image()

def update_image1(fs_files,fs_chunks): 
    try:
        previous = get_previous_image(fs_files)
        if previous != None:
            chunks = fs_chunks.find({"files_id": previous})
            binary_data = b"".join(chunk["data"] for chunk in chunks)
            with BytesIO(binary_data) as f:
                image = Image.open(f)
                display_image_pre(image)
        else:
            noimage = Image.open(os.path.join(MEDIA_PATH, 'GUI IMAGES/no_image.jpg'))
            display_image_pre(noimage)
    except Exception as e:
        print(f"An error occurred update_imag: {e}")

    label5.after(500, update_image1,fs_files,fs_chunks)

tk.Label(win, text="PREVIOUS IMAGE", font=(
    'Helvetica', 16, 'bold')).place(relx=0.1,rely=0.525)
label5 = tk.Label(win)
label5.place(relx=0.02,rely=0.57)
# Start the image update loop
# update_image1()


def capture_image_save():
    lbl_mode.config(text="Save Mode is ON",borderwidth=1, relief="solid",fg="#fa0a0a")
    lbl_mode.place(relx=0.4,rely=0.12)
    lbl_mode.update()
    
    print("Save Mode")
    if deployment == "True":
        # t1 = threading.Thread(target=main_process_save, args=(asi,client,MEDIA_PATH,mydb,model,))
        t1 = threading.Thread(target=main_process_save_raw, args=(asi,client,model,))
        t1.start()
    else:
        t1 = threading.Thread(target=main_process_save, args=(asi,MEDIA_PATH,mydb,model,))
        t1.start()
    fs_files = mydb['OUTPUT IMAGES.files']
    fs_chunks = mydb['OUTPUT IMAGES.chunks']
    update_image(fs_files,fs_chunks)
    update_image1(fs_files,fs_chunks)



def capture_image_nonsave():
    lbl_mode.config(text="Non Save Mode is ON",borderwidth=1, relief="solid",fg="#00FF00")
    lbl_mode.place(relx=0.4,rely=0.12)
    lbl_mode.update()
    print("Non Save Mode")
    if deployment == "True":
        t1 = threading.Thread(target=main_process_nonsave, args=(asi,client,MEDIA_PATH,mydb,yolo_model))
        # t1 = threading.Thread(target=main_process_nonsave, args=(asi,client,model,))
        t1.start()
    else:
        t1 = threading.Thread(target=main_process_nonsave, args=(asi,MEDIA_PATH,mydb,model,))
        t1.start()
    fs_files = mydb['OUTPUT IMAGES NonSave.files']
    fs_chunks = mydb['OUTPUT IMAGES NonSave.chunks']   
    update_image(fs_files,fs_chunks)
    update_image1(fs_files,fs_chunks)

def exit_btn():
    result = messagebox.askquestion("Stop", "Do you wish to proceed with exiting the application ?")
    if result == "yes":
        asi.flag = True
        win.destroy()

def exit_app():
    result = messagebox.askquestion("Exit", "Do you wish to proceed with exiting the application ?")
    if result == "yes":
        asi.flag = True
        win.destroy()
if deployment == "True":
    def sol_open(client):
        write_mem(client,13, 1)
        time.sleep(0.3)
        write_mem(client,13, 0)

    def emergency(client):
        write_mem(client,89, 1)
        time.sleep(0.3)
        write_mem(client,89, 0)
else:
    def sol_open():
        pass

    def emergency():
        pass

def open_second_window():
    def submit():
        start_date = start_calendar.get_date()
        end_date = end_calendar.get_date()
        start_time = start_time_entry.get()
        end_time = end_time_entry.get()
        start_datetime = datetime.strptime(start_date + " " + start_time, "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.strptime(end_date + " " + end_time, "%Y-%m-%d %H:%M:%S")
        start_datetime_str = start_datetime.strftime("%d-%m-%Y %H:%M:%S")
        end_datetime_str = end_datetime.strftime("%d-%m-%Y %H:%M:%S")
        batch_foldername = end_datetime.strftime("%d-%m-%Y_%H-%M-%S")
        output_dowmload_path = os.path.join(MEDIA_PATH,'PREDICTED IMAGES',batch_foldername)
        input_dowmload_path = os.path.join(MEDIA_PATH,'RAW IMAGES',batch_foldername)
        if select_box.get() == "Both":
            if not os.path.exists(output_dowmload_path):
                os.makedirs(output_dowmload_path)
                os.makedirs(input_dowmload_path)
            db_to_images_bulk_output(mydb,output_dowmload_path,start_datetime_str,end_datetime_str)
            db_to_images_bulk_raw(mydb,input_dowmload_path,start_datetime_str,end_datetime_str)
        elif select_box.get() == "Output Images":
            if not os.path.exists(output_dowmload_path):
                os.makedirs(output_dowmload_path)
            db_to_images_bulk_output(mydb,output_dowmload_path,start_datetime_str,end_datetime_str)
        elif select_box.get() == "Input Images":
            if not os.path.exists(input_dowmload_path):
                os.makedirs(input_dowmload_path)
            db_to_images_bulk_raw(mydb,input_dowmload_path,start_datetime_str,end_datetime_str)

        second_window.destroy()

    second_window = tk.Toplevel(win)
    second_window.iconbitmap(os.path.join(MEDIA_PATH,"GUI IMAGES/Manu_logo.ico"))
    second_window.title("Select the Date and Time Range")

    screen_width = second_window.winfo_screenwidth()
    screen_height = second_window.winfo_screenheight()
    window_width = 530
    window_height = 400
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    second_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Date Selection
    start_date_label = tk.Label(second_window, text="Start Date:")
    start_date_label.grid(row=0, column=0, padx=5, pady=5)
    start_calendar = Calendar(second_window, selectmode="day", date_pattern="yyyy-mm-dd")
    start_calendar.grid(row=1, column=0, padx=5, pady=5)
    
    end_date_label = tk.Label(second_window, text="End Date:")
    end_date_label.grid(row=0, column=1, padx=5, pady=5)
    end_calendar = Calendar(second_window, selectmode="day", date_pattern="yyyy-mm-dd")
    end_calendar.grid(row=1, column=1, padx=5, pady=5)

    # Time Selection
    start_time_label = tk.Label(second_window, text="Start Time:")
    start_time_label.grid(row=2, column=0, padx=5, pady=5)
    start_time_entry = tk.Entry(second_window)
    start_time_entry.insert(0, (datetime.now() - timedelta(hours=1)).strftime("%H:%M:%S"))  # Default to current time
    start_time_entry.grid(row=2, column=1, padx=5, pady=5)

    end_time_label = tk.Label(second_window, text="End Time:")
    end_time_label.grid(row=3, column=0, padx=5, pady=5)
    end_time_entry = tk.Entry(second_window)
    end_time_entry.insert(0, datetime.now().strftime("%H:%M:%S"))  # Default to current time
    end_time_entry.grid(row=3, column=1, padx=5, pady=5)

    options = ["Output Images","Input Images","Both"]
    selected_option = tk.StringVar()
    select_label = tk.Label(second_window, text="Select the options:")
    select_label.grid(row=4, column=0, padx=5, pady=5)
    select_box = ttk.Combobox(second_window, textvariable=selected_option, values=options)
    select_box.grid(row=4, column=1, padx=5, pady=5)

    # Submit button
    process_button = tk.Button(second_window, text="Submit", command=submit)
    process_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

def delete_old_files():
    # List of GridFS collection names
    gridfs_collection_names = ['OUTPUT IMAGES', 'INPUT IMAGES']
    
    # Define the cutoff date (2 days ago)
    cutoff_date = datetime.utcnow() - timedelta(days=2)
    
    # Loop through each GridFS collection
    for gridfs_collection_name in gridfs_collection_names:
        fs = GridFSBucket(mydb, bucket_name=gridfs_collection_name)
        
        # Find files older than cutoff date
        old_files = fs.find({'uploadDate': {'$lt': cutoff_date}})
        
        # Delete files older than cutoff date
        for file in old_files:
            fs.delete(file._id)
            print(f"Deleted file {file.filename} from GridFS collection {gridfs_collection_name}")

# btn_SaveMode = tk.Button(win, text="Start(SaveMode)", font=('Helvetica 13 bold'),
#                         width=16, height=1, relief=tk.RAISED,bg="#96B6C5", borderwidth=3, command=capture_image_save)
# btn_SaveMode.place(relx=0.42, rely=0.67)

btn_NonSaveMode = tk.Button(win, text="Start(NonSaveMode)", font=('Helvetica 11 bold'),
                        width=16, height=1, relief=tk.RAISED,bg="#96B6C5", borderwidth=3, command=capture_image_nonsave)
btn_NonSaveMode.place(relx=0.42,rely=0.67)

btn_ok = tk.Button(win, text='Filter Images', font=('Helvetica 11 bold'),
                width=16, height=1, relief=tk.RAISED, borderwidth=3, command=open_second_window, bg="#96B6C5")
btn_ok.place(relx=0.65,rely=0.67)

btn_reset = tk.Button(win, text="Stop", font=('Helvetica 12 bold'), width=16,
                      height=1, relief=tk.RAISED, bg="#96B6C5", borderwidth=3, command=exit_btn)
btn_reset.place(relx=0.85,rely=0.67)

btn_forcestop = tk.Button(win, text="Force Stop", font=('Helvetica 11 bold'),
                        width=16, height=1, relief=tk.RAISED, bg="red",borderwidth=3, command=sol_open)
btn_forcestop.place(relx=0.65,rely=0.8)

btn_reset = tk.Button(win, text="Reset", font=('Helvetica 11 bold'),
                        width=16, height=1, relief=tk.RAISED, bg="#96B6C5",borderwidth=3, command=lambda: emergency(client))
btn_reset.place(relx=0.42,rely=0.8)

btn_destroy = tk.Button(win, text="Exit", font=('Helvetica 13 bold'),
                        width=12, height=1, relief=tk.RAISED, bg="red",borderwidth=3, command=exit_app)
btn_destroy.place(relx=0.85,rely=0.1)

btn_delete = tk.Button(win, text="Delete Images(>2 Days)", font=('Helvetica 11 bold'),
                        width=18, height=1, relief=tk.RAISED, bg="#96B6C5",borderwidth=3, command=delete_old_files)
btn_delete.place(relx=0.85,rely=0.8)


############## Date and Time################
def update_datetime():
    current_datetime = datetime.now()
    current_date = current_datetime.strftime("%d/%m/%Y")
    current_time = current_datetime.strftime('%I:%M:%S %p')
    date_label.config(text=f"DATE: {current_date}")
    time_label.config(text=f"TIME: {current_time}")
   
    win.after(1000, update_datetime)  # Update every second (1000 milliseconds)


date_label = tk.Label(win, font=('Helvetica',15, 'bold'),
                   foreground='black')
date_label.place(relx=0.2,rely=0.02)

time_label = tk.Label(win, font=('Helvetica',15, 'bold'),
                   foreground='black')

time_label.place(relx=0.68, rely=0.02)
update_datetime()  # Start the initial update
##################################################

#############inspection count#########################

def update_counts():
    today_date = datetime.now().strftime("%d-%m-%Y")

    total_count  = mycollec.count_documents({"cur_date": today_date}) or 0
    accept_count = mycollec.count_documents({"cur_date": today_date, "decision": "Accept"}) or 0
    reject_count = mycollec.count_documents({"cur_date": today_date, "decision": "Reject"}) or 0

    inslbl.config(text=total_count)
    accept_lbl_val.config(text=accept_count)

    # ✅ This is your "bad / defect" count now
    defect_lbl_val.config(text=reject_count)

    win.after(1000, update_counts)

inslbl = tk.Label(win,font=('Helvetica', 16, 'bold'),
               foreground='black')
inslbl.place(relx=0.74, rely=0.12)
tk.Label(win, text="INSPECTION COUNT :",font=(
    'Helvetica', 16,'bold')).place(relx=0.58, rely=0.12)



# --- Accept Count label ---
accept_lbl_val = tk.Label(win, font=('Helvetica', 16, 'bold'), foreground='green')
accept_lbl_val.place(relx=0.605, rely=0.48)   # adjust position as you like

tk.Label(win, text="ACCEPT COUNT :", font=('Helvetica', 16, 'bold')).place(relx=0.47, rely=0.48)

# --- Defect Count label (total defect records today) ---
defect_lbl_val = tk.Label(win, font=('Helvetica', 16, 'bold'), foreground='red')
defect_lbl_val.place(relx=0.83, rely=0.48)   # adjust position as you like

tk.Label(win, text="DEFECT COUNT :", font=('Helvetica', 16, 'bold')).place(relx=0.7, rely=0.48)
update_counts()

status_label = tk.Label(win, text="Version 3.0 (BETA)",font= ('Helvetica 11 bold'),fg="#bdbebf")
status_label.place(relx=0.46,rely=0.92)

machine_label = tk.Label(win, text=f"Machine {machine_no}",font=('Helvetica', 18, 'bold'),fg="#fa0a0a",borderwidth=2, relief="solid")
machine_label.place(relx=0.46, rely=0.02)

lbl_mode = tk.Label(win, text="", font=('Helvetica 10 bold'))
lbl_mode.place(relx=0.15, rely=0.23)


######## Information Table ##########################
def table_data(db):
    tree.delete(*tree.get_children())

    collection = db['DEFECT DETAILS']
    current_date = datetime.today().strftime("%d-%m-%Y")

    defect_types = ["chipmark", "cut_piece", "out_piece", "curling_damage", "defect", "dent", "dr"]

    # ✅ Count UNIQUE defects per tyre/inspection
    # unique_key = file_input (best) else file_output else cycle_no else _id
    pipeline = [
        {"$match": {"cur_date": current_date}},
        {"$project": {
            "defect_name": 1,
            "unique_key": {
                "$ifNull": [
                    "$file_input",
                    {"$ifNull": [
                        "$file_output",
                        {"$ifNull": [
                            {"$toString": "$cycle_no"},
                            {"$toString": "$_id"}
                        ]}
                    ]}
                ]
            }
        }},
        # 1) remove duplicates: one record per (defect_name + unique_key)
        {"$group": {
            "_id": {"defect_name": "$defect_name", "unique_key": "$unique_key"}
        }},
        # 2) count unique_key per defect_name
        {"$group": {
            "_id": "$_id.defect_name",
            "count": {"$sum": 1}
        }}
    ]

    result = list(collection.aggregate(pipeline))

    # Build a dict: defect_name -> count
    counts = {r["_id"]: r["count"] for r in result if r["_id"] is not None}

    # Insert rows in fixed order (even if missing in DB -> show 0)
    for i, dname in enumerate(defect_types, start=1):
        tree.insert('', 'end', values=(i, dname, counts.get(dname, 0)))

    win.after(1000, table_data, db)


# ---- Treeview setup (full) ----
style = ttk.Style()
style.theme_use('clam')
style.configure("Custom.Treeview.Heading", font=("Arial", 10, "bold"), background='#96B6C5')
style.configure("Custom.Treeview", font=("Arial", 13))

tree = ttk.Treeview(
    win,
    columns=("S_NO", "Defect name", "count"),
    show='headings',
    height=9,
    style="Custom.Treeview"
)

tree.column("S_NO", anchor=tk.CENTER, width=200)
tree.heading("S_NO", text="S_NO")

tree.column("Defect name", anchor=tk.CENTER, width=200)
tree.heading("Defect name", text="DEFECT NAME")

tree.column("count", anchor=tk.CENTER, width=200)
tree.heading("count", text="COUNT")

tree.place(relx=0.47, rely=0.2, relheight=0.25)

table_data(mydb)


win.mainloop()
