# import pymongo
# import pandas as pd

# # MongoDB connection URI
# uri = "mongodb://localhost:27017/"

# # Create a MongoDB client
# client = pymongo.MongoClient(uri)

# # Specify the database
# db = client["SmartQC+MANU"]

# # Collections
# collections = ["SmartQC+MANU", "MAIN"]

# # Data to be collected
# data = []

# # Function to extract cycle number and decision from a collection
# def extract_data_from_collection(collection_name):
#     collection = db[collection_name]
#     documents = collection.find({}, {"cycle number": 1, "decision": 1})
#     for doc in documents:
#         cycle_number = doc.get("cycle number")
#         decision = doc.get("decision")
#         data.append({"Collection": collection_name, "Cycle Number": cycle_number, "Decision": decision})

# # Extract data from both collections
# for collection_name in collections:
#     extract_data_from_collection(collection_name)

# # Create a DataFrame from the data
# df = pd.DataFrame(data)

# # Save the data to an Excel file
# output_file = "cycle_decision_data.xlsx"
# df.to_excel(output_file, index=False, engine="openpyxl")

# print(f"Data has been written to {output_file}")



import pymongo
import pandas as pd
from datetime import datetime

# MongoDB connection URI
uri = "mongodb://localhost:27017/"

# Create a MongoDB client
client = pymongo.MongoClient(uri)

# Specify the database
db = client["SmartQC+MANU"]

# Collections to extract from
collections = ["SmartQC+MANU", "MAIN"]

# Data to be collected
data = []

# Date range filter (change as needed)
start_date = datetime(2025, 6, 17)
end_date = datetime(2025, 6, 18)

# Function to extract and filter by date
def extract_data_from_collection(collection_name):
    collection = db[collection_name]
    documents = collection.find({}, {
        "cycle_no": 1,
        "decision": 1,
        "inspectionDatetime": 1
    })
    for doc in documents:
        inspection_dt_str = doc.get("inspectionDatetime")
        try:
            inspection_dt = datetime.strptime(inspection_dt_str, "%d-%m-%Y %H:%M:%S")
        except Exception:
            continue  # skip invalid date formats
        if start_date <= inspection_dt <= end_date:
            data.append({
                "Collection": collection_name,
                "Cycle Number": doc.get("cycle_no"),
                "Decision": doc.get("decision"),
                "Inspection Datetime": inspection_dt_str
            })

# Extract data from both collections
for collection_name in collections:
    extract_data_from_collection(collection_name)

# Create a DataFrame from the data
df = pd.DataFrame(data)

# Save the data to an Excel file
output_file = "cycle_decision_data_filtered.xlsx"
df.to_excel(output_file, index=False, engine="openpyxl")

print(f"Filtered data has been written to {output_file}")
