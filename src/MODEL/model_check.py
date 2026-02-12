from torchvision.utils import draw_bounding_boxes
import torchvision.transforms.functional as F
import torch
import cv2,time
import numpy as np

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
        # print('1')
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
  # print(sta)
  nus=np.delete(nu,sta)
  # print(nus)
  b=len(nus)/4
  nus=nus.reshape(int(b),4)
  return nus
  
def torchy(frame):
    frame = cv2.resize(frame, (1333, 756))
    with torch.no_grad():
        image1 = torch.as_tensor(frame.astype("uint8").transpose(2, 0, 1))
        xy = model(image1)
        # print(xy)
        xy = filter(xy)
        print(xy)
        mask = xy[0]
        strings = [lbl(x) for x in xy[1].tolist()]
        drawn_masks = []
        colr = ['blue']*len(xy[1])
        drawn_masks.append(draw_bounding_boxes(image1, mask, strings, width=3,
                           font_size=30, colors=colr, font='C:/Windows/Fonts/arial.ttf', fill=True))
        defect_image = show(drawn_masks)
        print(strings)
        if len(xy[1] > 0):
            defect_label = strings
            # print("de",defect_label)
        else:
            defect_label = []
        return defect_image, defect_label
    
# device = torch.device('cpu')  # Use CPU
# print(device)

# model = torch.jit.load("media/weights/model_nov20.ts", map_location=device)  # Load model to CPU

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
torch.cuda.max_memory_allocated(device = None)
model = torch.jit.load(os.path.join(MEDIA_PATH,'WEIGHTS/model_nov20.ts')).to(device)
img = cv2.imread('1.jpg')
ss = time.time()
torchy(img)
dd = time.time()
print(dd-ss,'time')
