import cv2
import os
import numpy as np
import pymongo
from gridfs import GridFS
import threading

def nparray_to_bytes(cycle_no,db,filename,collection_name,img_array,format_date_db,formatted_datetime_db):
    # Convert the image data to bytes
    image_bytes = cv2.imencode('.jpg', img_array)[1].tobytes()
    # Create a new GridFS object
    fs = GridFS(db,collection_name)
    # Store the image in GridFS
    file_id = fs.put(image_bytes,cycle_no=cycle_no,filename=filename,cur_date=format_date_db,cur_datetime=formatted_datetime_db)
    db[collection_name+".files"].create_index([("cur_date", pymongo.ASCENDING)])
    
def recent_cycle(mydb):
    file_collection = mydb['MAIN']  # Replace with your actual collection name
    # Query to find the document with the latest inspectionDatetime
    pipeline = [
        {"$project": {
            "_id": 1,
            "cycle_no": 1,
            "inspectionDatetime": {
                "$dateFromString": {
                    "dateString": "$inspectionDatetime",
                    "format": "%d-%m-%Y %H:%M:%S"
                }
            }
        }},
        {"$sort": {"inspectionDatetime": -1}},  # Sort documents by inspectionDatetime in descending order
        {"$limit": 1},  # Limit the result to the first document
        {"$project": {"cycle_no": 1}}  # Project only the cycle_no field
    ]

    recent_cycle = file_collection.aggregate(pipeline)
    # Check if any document is found
    if recent_cycle.alive:
        for doc in recent_cycle:
            recent_cycle_no = doc.get("cycle_no")
            if recent_cycle_no:
                recent_cycle_no = int(recent_cycle_no) + 1  # Increment cycle_no
                return recent_cycle_no
            else:
                return 1
    else:
        return 1  # Return 1 if no documents are found
        
def db_to_images(cycle, db, download_loc):
    # Assuming 'fs.files' contains metadata and 'fs.chunks' contains the actual data
    fs_files = db['OUTPUT IMAGES.files']
    fs_chunks = db['OUTPUT IMAGES.chunks']

    file_list = fs_files.find_one({'cycle_no': cycle}, {'_id': False, 'filename': True})

    # Find the document containing the image you want to extract
    image_document = fs_files.find_one(file_list)
    if image_document:
        # Get the ObjectID of the file
        file_id = image_document['_id']

        # Retrieve chunks associated with the file
        chunks = fs_chunks.find({"files_id": file_id}).sort("n")

        # Concatenate the binary data from each chunk
        binary_data = b"".join(chunk["data"] for chunk in chunks)
        download_path = os.path.join(download_loc,file_list["filename"])
        # Save the binary data to a file
        with open(download_path, "wb") as f:
            f.write(binary_data)

        print("Image extracted successfully.")
    else:
        print("Image not found.")

def db_to_images_bulk_output(db, download_loc, start_datetime, end_datetime):
    # Assuming 'fs.files' contains metadata and 'fs.chunks' contains the actual data
    fs_files = db['OUTPUT IMAGES.files']
    fs_chunks = db['OUTPUT IMAGES.chunks']
    # Find documents within the datetime range
    query = {'cur_datetime': {'$gte': start_datetime, '$lte': end_datetime}}
    file_list = list(fs_files.find(query, {'_id': True, 'filename': True}))
    if file_list:
        for image_document in file_list:
            # Get the ObjectID of the file
            file_id = image_document['_id']

            # Retrieve chunks associated with the file
            chunks = fs_chunks.find({"files_id": file_id}).sort("n")

            # Concatenate the binary data from each chunk
            binary_data = b"".join(chunk["data"] for chunk in chunks)
            download_path = os.path.join(download_loc, image_document["filename"])
            # Save the binary data to a file
            with open(download_path, "wb") as f:
                f.write(binary_data)

            print("Image extracted successfully:", image_document["filename"])
    else:
        print("No images found within the specified datetime range.")

def db_to_images_bulk_raw(db, download_loc, start_datetime, end_datetime):
    # Assuming 'fs.files' contains metadata and 'fs.chunks' contains the actual data
    fs_files = db['INPUT IMAGES.files']
    fs_chunks = db['INPUT IMAGES.chunks']
    # Find documents within the datetime range
    query = {'cur_datetime': {'$gte': start_datetime, '$lte': end_datetime}}
    file_list = list(fs_files.find(query, {'_id': True, 'filename': True}))
    if file_list:
        for image_document in file_list:
            # Get the ObjectID of the file
            file_id = image_document['_id']

            # Retrieve chunks associated with the file
            chunks = fs_chunks.find({"files_id": file_id}).sort("n")

            # Concatenate the binary data from each chunk
            binary_data = b"".join(chunk["data"] for chunk in chunks)
            download_path = os.path.join(download_loc, image_document["filename"])
            # Save the binary data to a file
            with open(download_path, "wb") as f:
                f.write(binary_data)

            print("Image extracted successfully:", image_document["filename"])
    else:
        print("No images found within the specified datetime range.")


def thread_func(target_func,cycle_no,db,filename,collection_name,img_array,format_date_db,formatted_datetime_db):
    m_ThreadHandle=threading.Thread(target=(target_func),args=(cycle_no,db,filename,collection_name,img_array,format_date_db,formatted_datetime_db))
    m_ThreadHandle.start()
    m_ThreadHandle.join(0)

def load_env(ROOT_DIR):
    file_path=os.path.join(ROOT_DIR,'.env')
    env_vars = {}
    with open(file_path, "r") as file:
        for line in file:
            # Skip comments and empty lines
            if line.startswith("#") or not line.strip():
                continue

            # Split the line into key and value
            key, value = line.strip().split("=")
            env_vars[key] = value

    return env_vars

def delete_old_five(db):
    collection_names = ["INPUT IMAGES NonSave.files","INPUT IMAGES NonSave.chunks","OUTPUT IMAGES NonSave.chunks","OUTPUT IMAGES NonSave.files"]
    for collection_name in collection_names:
        collection = db[collection_name]

        # Check if collection contains more than 500 documents
        count = collection.count_documents({})

        if count > 2:
            # Sort documents based on timestamp (assuming 'timestamp' field exists)
            oldest_documents = collection.find().sort('timestamp', 1).limit(count - 2)

            # Delete the oldest documents
            for doc in oldest_documents:
                collection.delete_one({'_id': doc['_id']})
                # print("Deleted document with _id:", doc['_id'])

def run_delete_old_five_in_thread(db):
    thread = threading.Thread(target=delete_old_five, args=(db,))
    thread.start()