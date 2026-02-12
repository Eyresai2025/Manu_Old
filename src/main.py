import os,time
import cv2
from datetime import datetime
from src.MODEL.detectron import modelmain
from src.COMMON.common import nparray_to_bytes,recent_cycle,thread_func,delete_old_five


def main_process_save(asi,MEDIA_PATH,mydb,model):
    num_cycles = 10
    cycle_count = 0

    while cycle_count < num_cycles:
    # while (True):
        st_time = time.time()
        cycle_no = recent_cycle(mydb)
        print('cycle_no',cycle_no)
        current_time = datetime.now()
        formatted_datetime = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        formatted_date = datetime.strptime(formatted_datetime, "%Y-%m-%d_%H-%M-%S")
        format_date_imagename = formatted_date.strftime('%d%m%Y')
        file_raw = str(cycle_no) + '_INPUT_'+format_date_imagename+'.jpg'
        file_output = str(cycle_no) + '_OUTPUT_'+format_date_imagename+'.jpg'

        format_date_db = formatted_date.strftime('%d-%m-%Y')
        formatted_datetime_db = current_time.strftime("%d-%m-%Y %H:%M:%S")

        #Model
        img = cv2.imread(os.path.join(MEDIA_PATH,'RAW IMAGES/2.jpg'))
        thread_func(nparray_to_bytes,cycle_no,mydb,file_raw,"INPUT IMAGES",img,format_date_db,formatted_datetime_db)
        defect_image, defect_name = modelmain(cycle_no,mydb,file_output,MEDIA_PATH,img,format_date_db,model)
        thread_func(nparray_to_bytes,cycle_no,mydb,file_output,"OUTPUT IMAGES",defect_image,format_date_db,formatted_datetime_db)

        #Decision
        if len(defect_name) >= 1:
            result = "Reject"
        else:
            result = "Accept"
        print(result,"result")

        insert_dict = {
            'cycle_no':cycle_no,
            'inspectionDatetime': formatted_datetime_db,
            'cur_date':format_date_db,
            'file_input':file_raw,
            'file_output':file_output,
            'defect_name': defect_name,'decision':result
        }
        mydb["MAIN"].insert_one(insert_dict)
        en_time = time.time()
        print(en_time-st_time,'cycle time')
        cycle_count += 1
    

def main_process_nonsave(asi,MEDIA_PATH,mydb,model):
    num_cycles = 10
    cycle_count = 0

    while cycle_count < num_cycles:
    # while (True):
        st_time = time.time()
        cycle_no = recent_cycle(mydb)
        print('cycle_no',cycle_no)
        current_time = datetime.now()
        formatted_datetime = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        formatted_date = datetime.strptime(formatted_datetime, "%Y-%m-%d_%H-%M-%S")
        format_date_imagename = formatted_date.strftime('%d%m%Y')
        file_raw = str(cycle_no) + '_INPUT_'+format_date_imagename+'.jpg'
        file_output = str(cycle_no) + '_OUTPUT_'+format_date_imagename+'.jpg'

        format_date_db = formatted_date.strftime('%d-%m-%Y')
        formatted_datetime_db = current_time.strftime("%d-%m-%Y %H:%M:%S")

        #Model
        img = cv2.imread(os.path.join(MEDIA_PATH,'RAW IMAGES/2.jpg'))
        thread_func(nparray_to_bytes,cycle_no,mydb,file_raw,"INPUT IMAGES NonSave",img,format_date_db,formatted_datetime_db)
        defect_image, defect_name = modelmain(cycle_no,mydb,file_output,MEDIA_PATH,img,format_date_db,model)
        thread_func(nparray_to_bytes,cycle_no,mydb,file_output,"OUTPUT IMAGES NonSave",defect_image,format_date_db,formatted_datetime_db)

        #Decision
        if len(defect_name) >= 1:
            result = "Reject"
        else:
            result = "Accept"
        print(result,"result")

        insert_dict = {
            'cycle_no':cycle_no,
            'inspectionDatetime': formatted_datetime_db,
            'cur_date':format_date_db,
            'file_input':file_raw,
            'file_output':file_output,
            'defect_name': defect_name,'decision':result
        }
        mydb["MAIN"].insert_one(insert_dict)
        en_time = time.time()
        print(en_time-st_time,'cycle time')
        delete_old_five(mydb)
        cycle_count += 1
    
