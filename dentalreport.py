import os
import cv2
import tkinter as tk
from tkinter import filedialog
import pydicom
from datetime import datetime
from PIL import Image,ImageDraw
from docxtpl import InlineImage
import json
import numpy as np
from docxtpl import DocxTemplate

def select_patient_folder():
    while True:
        want_to_enter_name = input("Select a patient folder? (yes/no): ").lower()
        if want_to_enter_name == 'no':
            print("Patient folder not selected,process terminating!!")
            exit()
        else:
            patient_name = input("Enter the patient name: ")
            print("Patient name:", patient_name)
            selected_folder = open_folder_explorer()
            print("Selected patient path:", selected_folder)
            return patient_name, selected_folder

def open_folder_explorer():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    return folder_path

def get_dicom_file(folder_path):
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith('.dcm'):
                dcm_filepath = os.path.join(root, filename)
                return dcm_filepath
    return None


def read_dcm_attributes(dcm_file, attribute_tags):
    print("Debug: DICOM file path:", dcm_file)
    ds = pydicom.dcmread(dcm_file)
    attributes = {}
    for param in attribute_tags:
        attributes[param['name']] = ds[param['name']].value
    return attributes


def get_patient_id_from_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith('.dcm'):
                file_path = os.path.join(root, filename)
                dataset = pydicom.dcmread(file_path)
                patient_id = dataset.get('PatientID', 'Null')
                return patient_id
    return("Null")


def validate_region_number(region_number):
    valid_region_numbers = [
        '11', '12', '13', '14', '15', '16', '17', '18',
        '21', '22', '23', '24', '25', '26', '27', '28',
        '31', '32', '33', '34', '35', '36', '37', '38', 
        '41', '42', '43', '44', '45', '46', '47', '48'
    ]
    return region_number in valid_region_numbers

def get_quadrant_and_region(region_number):
    quadrant = int((int(region_number) - 1) / 8) + 1
    region_names = {
        '11': 'Upper right third molar',
        '12': 'Upper right second molar',
        '13': 'Upper right first molar',
        '14': 'Upper right second premolar',
        '15': 'Upper right first premolar',
        '16': 'Upper right canine',
        '17': 'Upper right lateral incisor',
        '18': 'Upper right central incisor',
        '31': 'Lower left third molar',
        '32': 'Lower left second molar',
        '33': 'Lower left first molar',
        '34': 'Lower left second premolar',
        '35': 'Lower left first premolar',
        '36': 'Lower left canine',
        '37': 'Lower left lateral incisor',
        '38': 'Lower left central incisor',
        '41': 'Lower right central incisor',
        '42': 'Lower right lateral incisor',
        '43': 'Lower right canine',
        '44': 'Lower right first premolar',
        '45': 'Lower right second premolar',
        '46': 'Lower right first molar',
        '47': 'Lower right second molar',
        '48': 'Lower right third molar',
    }
    region_name = region_names.get(region_number, 'Null')
    return quadrant, region_name

def draw_line(image, p1, p2):
    draw = ImageDraw.Draw(image)
    draw.line([p1, p2], fill='green', width=3)
    return image

def add_text(image,pt,text_to_display):
    I1 = ImageDraw.Draw(image)
    I1.text(pt, text_to_display, fill="green")
    return image

def apply_window(pixel_array, window_center, window_width):
    window_min = window_center - window_width / 2
    window_max = window_center + window_width / 2
    pixel_array = np.clip(pixel_array, window_min, window_max)
    pixel_array = (pixel_array - window_min) / (window_max - window_min)
    pixel_array = np.clip(pixel_array, 0.0, 1.0)
    return pixel_array

while True:
    patient_name, selected_folder = select_patient_folder()
    patient_id = get_patient_id_from_folder(selected_folder)
    if patient_id != 'Null':
        print("Patient ID from DICOM file in the folder:", patient_id)
        break
    else:
        print("Patient ID not applicable. Please select a different patient folder.")

confirm = input("Do you confirm this patient ID? (yes/no): ").lower()
if confirm != 'yes':
    print("Confirmation denied. Exiting...")
    exit()

while True:
    region_number = input("Enter the region number: ")
    if validate_region_number(region_number):
        break
    else:
        print("Invalid region number. Please enter a valid FDI teeth number (11-48).")
        image_path = 'pic4.png'
        img = Image.open(image_path)
        img.show()

quadrant, region_name = get_quadrant_and_region(region_number)
print("The selected tooth is in the:")
print(f"Quadrant: {quadrant}")
print(f"Region Name: {region_name}")

generate_report = input("Do you want to generate a pre-filled report? (yes/no): ").lower()
if generate_report == 'yes':
    
    dcm_file = get_dicom_file(selected_folder)
    json_file = 'middle.json'  
    template_file = 'dental_Report_template.docx'  
    
    with open(json_file) as f:
        json_data = json.load(f)
    
    attribute_tags = json_data['content']
    attributes = read_dcm_attributes(dcm_file, attribute_tags)

    ds = pydicom.read_file(dcm_file)
    window_center = ds.WindowCenter
    window_width = ds.WindowWidth

    pixel_array = ds.pixel_array
    windowed_pixel_array = apply_window(pixel_array, window_center, window_width)

    windowed_pixel_array = (windowed_pixel_array * 255).astype(np.uint8)
    cv2.imwrite("windowed_image.jpg", windowed_pixel_array)
    image = Image.open("windowed_image.jpg")
    image = image.convert('RGB')
    image = draw_line(image, (100,200), (200,300))

    rows = ds.Rows
    columns = ds.Columns

    point1 = (rows // 2, 0)
    point2 = (0, columns // 2)
    point3 = (rows // 2, columns)
    point4 = (rows, columns // 2)

    image = add_text(image, (200,300), "200mm")
    image = add_text(image, (169,0), "H")
    image = add_text(image, (0,169), "R")
    image = add_text(image, (169,330), "F")
    image = add_text(image, (330,169), "L")

    image.save("result.jpg")


    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    attributes['RegionNumber'] = region_number
    attributes['RegionName'] = region_name
    attributes['date_now'] = current_datetime
   
   
    to_fill_in = {'img1': 'result.jpg', 'img2': 'result.jpg'}
    template = DocxTemplate(template_file)
    context = {}
    for key, value in to_fill_in.items():
        image = InlineImage(template, value)
        context[key] = image
    template.render(context)  # Render images into the template

    
    report_filename = f"{patient_name}_{current_datetime}.docx"
    report_filepath = os.path.join(selected_folder, report_filename)
    template.save(report_filepath)
    print("Report generated and saved as:", report_filepath)
    print("Successfully generated report! Thank you.")
else:
    print("No report will be generated. Thank you.")
