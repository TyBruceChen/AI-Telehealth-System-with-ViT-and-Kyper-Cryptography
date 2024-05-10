import torch 
from PIL import Image
import numpy as np

def load_model(model_path):
    model = torch.load(model_path)
    return model

def img_process(img_path,img_size=(224,224)):
    img = Image.open(img_path).convert('RGB').resize(img_size)
    img = np.expand_dims(np.array(img),axis = 0)/255  #convert the img to ndarray and expand 1 dimmension (H,W,C) -> (N,H,W,C) N is the batch size
    img = torch.from_numpy(img) #convert the numpy to torch.tensor
    img = img.permute(0,3,2,1) #(N,H,W,C) -> (N,C,H,W)
    return img.to(torch.float)


"""

if __name__ == '__main__':
    
    img_path = 'files/COVID-2.png'
    img = img_process(img_path)

    model_path = 'Diagnosis_Model.pt'
    server_model = load_model(model_path)

    y = server_model(img)
    print(y)
    result = int(y.argmax())
    with open('temp.txt','w') as f:
        f.write(str(y)+'\n'+str(result))
"""