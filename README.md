
<div>
  <img src="http://radometechnologies.com/assets/logo.png" alt="Logo" width="300" align="left"/>
  <img src="media/GUI IMAGES/Manu_logo.png" alt="Manu Logo" width="300" align="right"/>
</div>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
 
# SmartQC+ MANU YANTRYALAY GUI Version 2.0 (BETA)

## Overview

This SmartQC+ MANU YANTRYALAY GUI contains the Graphical User Interface (GUI) for the Bear Ring Defect Inspections project, as well as the Programmable Logic Controller (PLC) connection setup and the cycle of the parts involved in the inspection process.

## Features

- **GUI**: The graphical interface designed for facilitating the inspection process. It provides user-friendly controls and displays relevant information related to the inspection.
- **PLC Connection**: Configuration files and scripts necessary for establishing communication between the GUI and the Programmable Logic Controller. This ensures seamless data exchange and control over the inspection process.
- **Cycle of Partsn**: Documentation or diagrams illustrating the workflow and cycle of parts within the inspection process. This helps in understanding the sequence of operations and the role of each component.


## Usage

To use SmartQC+ MANU YANTRYALAY GUI:

  1. Clone the repository to your local machine.
  2. Set up the necessary dependencies and environment according to the provided documentation.
  3. Run the GUI application to initiate the inspection process.
  4.  Ensure the PLC connection is properly established to communicate with the inspection equipment.
  5. Follow the documented cycle of parts to carry out inspections efficiently.

## Installation

1. Clone the project:
    ```bash
    git clone https://github.com/radometech/smartqc-manu-gui.git
    ```

2. Create a virtual environment:
    ```bash
    python -m venv manu_env
    ```

3. Activate the virtual environment:
    - For Windows:
        ```bash
        manu_env\Scripts\activate
        ```
    - For Linux/Mac:
        ```bash
        source manu_env/bin/activate
        ```

4. Navigate to the project directory:
    ```bash
    cd smartqc-manu-gui
    ```

5. Install the required packages using `requirements.txt`:
    ```bash
    pip install pymongo==4.6.1 pillow==10.2.0 tkcalendar==1.6.1 opencv-python==4.9.0.80 pymodbus==2.5.3
    # CPU only
    pip install torch==1.12.1+cpu torchvision==0.13.1+cpu torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cpu
    # CUDA 11.3
    pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
    ```

## Instructions

To run the SmartQC+ MANU GUI:

1. Ensure that you have activated the virtual environment.
2. Navigate to the project directory if you haven't already.
3. Run the GUI file:
    ```bash
    python ManuGUI.py
    ```

## Screenshots

### 1. Starting the Image Capture Process
Pressing the Start Button initiates the machine to start capturing images.

![Start Button](https://github.com/Radome-Tech/smartqc-manu-gui/assets/74447591/995516a5-de8f-4574-b293-5850aacf5869)
*Description: The image shows the interface with the Start Button highlighted, indicating the beginning of the image capturing process.*

### 2. Displaying Current and Previous Images
The interface displays the current and previous (N-1) images respectively.

![Current Image](https://github.com/Radome-Tech/smartqc-manu-gui/assets/74447591/995516a5-de8f-4574-b293-5850aacf5869)
*Description: Current image displayed in the interface.*

![Previous Image](https://github.com/Radome-Tech/smartqc-manu-gui/assets/74447591/995516a5-de8f-4574-b293-5850aacf5869)
*Description: Previous image (N-1) displayed in the interface.*

### 3. Filtering Image Files
The "Filter Images" button allows users to filter image files by selecting date and time range and choosing one of the options (Input, Output, Both). Submitted images can be downloaded into respective folders: Output images are stored in `media/PREDICTED IMAGES` directory, and Input images are stored in `media/RAW IMAGES` directory.

![Filter Images](https://github.com/Radome-Tech/smartqc-manu-gui/assets/74447591/f2e06912-2a3b-4117-ace6-ff4b2bbba436)

*Description: The image demonstrates the interface with options for filtering images and the resulting download of images into respective directories.*

### 4. MongoDB structures
   ![MongoDB Structures](https://github.com/Radome-Tech/smartqc-manu-gui/assets/74447591/10d0bf26-e754-44fc-abc2-ad0f7b437105)


   #### MongoDB Data Management System
In this section for an MongoDB Data Management System, which stores information about inspection cycles, defects detected, and images used during inspections.

  #### 4.1.MAIN Collection
  
  - **cycle_no**: Cycle number
  - **inspectionDatetime**: Date and time of inspection
  - **cur_date**: Current date
  - **file_input**: Input image file name
  - **file_output**: Output image file name
  - **defect_name**: List of detected defects
  - **decision**: Decision based on inspection results (e.g., "Reject" or "Accept")
      ```json
          {
            "cycle_no": 1,
            "inspectionDatetime": "15-02-2024 14:42:20",
            "cur_date": "15-02-2024",
            "file_input": "1_INPUT_15022024.jpg",
            "file_output": "1_OUTPUT_15022024.jpg",
            "defect_name": [
              "defect",
              "defect",
              "defect",
              "defect"
            ],
            "decision": "Reject"
          }
      ```
  
  #### 4.2.DEFECT DETAILS Collection
  
  - **cycle_no**: Cycle number
  - **bbox**: Bounding box coordinates of the defect
  - **defect_name**: Name of the defect
  - **file_output**: Output image file name
  - **cur_date**: Current date
    ```json
        {
          "cycle_no": 1,
          "bbox": [
            454.0324401855469,
            414.86639404296875,
            465.5118713378906,
            428.3740234375
          ],
          "defect_name": "defect",
          "file_output": "1_OUTPUT_15022024.jpg",
          "cur_date": "15-02-2024"
        }
    ```
  
  #### 4.3.INPUT IMAGES Collection
  
  - **cycle_no**: Cycle number
  - **filename**: Name of the image file
  - **cur_date**: Current date
  - **cur_datetime**: Date and time of the image upload
  - **chunkSize**: Size of each data chunk
  - **uploadDate**: Date and time of the image upload
     ```json
        {
          "cycle_no": 1,
          "filename": "1_INPUT_15022024.jpg",
          "cur_date": "15-02-2024",
          "cur_datetime": "15-02-2024 14:42:20",
          "chunkSize": 261120,
          "length": {
            "$numberLong": "311767"
          },
          "uploadDate": {
            "$date": "2024-02-15T09:12:21.529Z"
          }
        }
     ```
  
  #### 4.4.OUTPUT IMAGES Collection
  
  - **cycle_no**: Cycle number
  - **filename**: Name of the image file
  - **cur_date**: Current date
  - **cur_datetime**: Date and time of the image upload
  - **chunkSize**: Size of each data chunk
  - **uploadDate**: Date and time of the image upload
    ```json
        {
          "cycle_no": 1,
          "filename": "1_OUTPUT_15022024.jpg",
          "cur_date": "15-02-2024",
          "cur_datetime": "15-02-2024 14:42:20",
          "chunkSize": 261120,
          "length": {
            "$numberLong": "152421"
          },
          "uploadDate": {
            "$date": "2024-02-15T09:12:35.681Z"
          }
        }
     ```    
        
  #### 4.5.Employee Collection
  
  - **Employee_ID**: Employee ID number
  - **Employee_Name**: Employee Name
  - **LoginTime**: Login or Operating date and time
      ```json
      {
        "Employee_ID": "SAMPLE ID",
        "Employee_Name": "SAMPLE NAME",
        "LoginTime": "15-02-2024 14-42-18"
      }
    ```

## Contributors

- [Kamalesh Kannan](https://github.com/kamalkannan79)
  

## Issues

If you encounter any issues or have suggestions for improvement, please [open an issue](https://github.com/radometech/smartqc-manu-gui/issues) on GitHub.
