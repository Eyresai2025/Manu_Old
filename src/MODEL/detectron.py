from torchvision.utils import draw_segmentation_masks, draw_bounding_boxes
import torchvision.transforms.functional as F
import torch
torch.cuda.empty_cache()
import cv2
import numpy as np
import os
import pymongo

def lbl(nu):
    if nu == 0:
        return "chipmark"
    elif nu == 1:
        return "cut_piece"
    elif nu == 2:
        return "out_piece"
    elif nu == 3:
        return "curling_damage"
    elif nu == 4:
        return "defect"
    elif nu == 5:
        return "dent"
    elif nu == 6:
        return "dr"

def filter(xy):
    nu=[0,0,0,0]
    labels=[2]
    for i in range(len(xy)):
      nu[i]=xy[i].cpu().detach().numpy()
    for j in labels:
        indez=np.where(nu[1] == j)[0]
        nu[0]=remove_el(indez,nu[0])
        nu[1]=np.delete(nu[1],indez)
        nu[2]=np.delete(nu[2],indez)

    nu[0]=torch.from_numpy(nu[0])
    nu[1]=torch.from_numpy(nu[1])
    nu[2]=torch.from_numpy(nu[2])
    nu[3]=torch.from_numpy(nu[3])
    return nu
    
def show(imgs):
    if not isinstance(imgs, list):
        imgs = [imgs]
    for i, img in enumerate(imgs):
        img = img.detach()
        img = F.to_pil_image(img)
        return np.asarray(img)

def remove_el(indez,nu):
  sta=[]
  for c in indez:
      indez=c
      if indez!=0:
        indez=indez*4
      a=range(indez,indez+4)
      for i in a:
        sta.append(i)
  nus=np.delete(nu,sta)
  b=len(nus)/4
  nus=nus.reshape(int(b),4)
  return nus
  
def torchy(cycle_no,mydb,model,frame,file_output,format_date_db):
    frame = cv2.resize(frame, (1333, 756))
    with torch.no_grad():
        image1 = torch.as_tensor(frame.astype("uint8").transpose(2, 0, 1))
        xy = model(image1)
        xy = filter(xy)
        mask = xy[0]
        strings = [lbl(x) for x in xy[1].tolist()]
        drawn_masks = []
        colr = ['blue']*len(xy[1])
        drawn_masks.append(draw_bounding_boxes(image1, mask, strings, width=3,
                           font_size=30, colors=colr, font='C:/Windows/Fonts/arial.ttf', fill=True))
        defect_image = show(drawn_masks)
        if len(xy[1] > 0):
            defect_label = strings
        else:
            defect_label = []

        detected_dict = []
        for i in range(len(xy[0])):
            bbox = xy[0][i].tolist()
            defect_name = strings[i]
            detected_object = {"cycle_no":cycle_no,'bbox': bbox, 'defect_name': defect_name,"file_output":file_output,"cur_date":format_date_db}
            detected_dict.append(detected_object)
        def_collection = mydb['DEFECT DETAILS']
        def_collection.create_index([("cur_date", pymongo.ASCENDING)])
        if len(detected_dict) > 0:
            def_collection.insert_many(detected_dict)
        return defect_image, defect_label
    
def torchy_warmup(frame,model):
    frame = cv2.resize(frame, (1333, 756))
    with torch.no_grad():
        image1 = torch.as_tensor(frame.astype("uint8").transpose(2, 0, 1))
        xy = model(image1)
        xy = filter(xy)
        mask = xy[0]
        strings = [lbl(x) for x in xy[1].tolist()]
        drawn_masks = []
        colr = ['blue']*len(xy[1])
        drawn_masks.append(draw_bounding_boxes(image1, mask, strings, width=3,
                           font_size=30, colors=colr, font='C:/Windows/Fonts/arial.ttf', fill=True))
        defect_image = show(drawn_masks)
        if len(xy[1] > 0):
            defect_label = strings
        else:
            defect_label = []
        return defect_image, defect_label




def modelmain(cycle_no,mydb,file_output,MEDIA_PATH,img,format_date_db,model):
    defect_image, defect_label = torchy(cycle_no,mydb,model,img,file_output,format_date_db)
    return defect_image, defect_label

# def modelmain(file_output,MEDIA_PATH,img,model):
#     defect_image, defect_label = torchy(model,img,file_output)
#     return defect_image, defect_label
