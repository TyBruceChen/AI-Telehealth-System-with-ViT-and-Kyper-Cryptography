# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 17:03:18 2024

@author: tc922
"""

import torch 
from PIL import Image
import numpy as np

import os,sys,inspect
import cv2
import matplotlib.pyplot as plt
import io
import base64

import sys

sys.path.append('/home/piko/Documents/Flask_2/Encryp_Kyber/Kyber')

from kyber import  Kyber512 #you should also try Kyber768 and Kyber 1024
import time
from encry_decry import *
from cyphertext_proc import *


def load_model(model_path):
    model = torch.load(model_path)
    return model

def img_process(img_path,img_size=(224,224)):
    img = Image.open(img_path).convert('RGB').resize(img_size)
    img = np.expand_dims(np.array(img),axis = 0)/255  #convert the img to ndarray and expand 1 dimmension (H,W,C) -> (N,H,W,C) N is the batch size
    img = torch.from_numpy(img) #convert the numpy to torch.tensor
    img = img.permute(0,3,2,1) #(N,H,W,C) -> (N,C,H,W)
    return img.to(torch.float)

def lung_type(cls_num,ls = ['COVID-19','Lung-Opacity','Normal','Viral Pneumonia']):
    return ls[cls_num]


if __name__ == '__main__':
    
    ###################################################################
    #image processing
    root_path = './Test_Set'
    img_save_path = './results'
    key_path = './token'
    enc_path = './encrypted_data'
    img_name = os.listdir(root_path)[0]
    image_path = os.path.join(root_path,img_name)
    image = Image.open(image_path)
    
    rescale_size = (299, 299)
    rescale_image = image.resize(rescale_size, Image.BICUBIC)
    
    """
    norm_img = plt.imread(os.path.join(img_save_path,'rescale_image.png'))
    
    plt.hist(norm_img.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')
    plt.show()
    """
    
    rescale_image_bytes = io.BytesIO()
    rescale_image.save(rescale_image_bytes, format='JPEG')
    image_bytes = rescale_image_bytes.getvalue()
    
    ################################################################
    #key generation
    pub_key, sec_key = key_gen()
    
    pub_K_path = os.path.join(key_path, 'pub.key')
    with open (pub_K_path,'wb') as pub:
        pub.write(pub_key)
        
    with open (pub_K_path,'rb') as pub:
        pub_k = pub.read()
        
    sec_K_path = os.path.join(key_path, 'sec.key')
    with open (sec_K_path,'wb') as sec:
        sec.write(sec_key)
        
    with open (sec_K_path,'rb') as sec:
        sec_k = sec.read()
        
    #Encryption Part
    enc_data = kyber_encryption(public_key = pub_k, image_bytes = image_bytes)
    
    #Save data for transmission
    for i,data_chunk in enumerate(enc_data):
        data_path = os.path.join(enc_path,'enc_data-'+str(i))
        with open (data_path,'wb') as data:
            data.write(data_chunk)
    
    #Read received data
    list_enc_data = []
    for i,data_chunk in enumerate(enc_data):
        data_path = os.path.join(enc_path,'enc_data-'+str(i))
        with open (data_path,'rb') as data:
            chunk_info = data.read()
        list_enc_data.append(chunk_info)
    
    print()
    print(f'The transmitted data type from client to server \
is {type(list_enc_data)} with {type(list_enc_data[-2])}, which is encrpted string. \
          ')
    print() 
    
    #Decryption Part
    dec_img = kyber_decryption(secret_key = sec_k, ciphertexts = list_enc_data)
    
    
    #dec_img.show()
    dec_img.save(os.path.join(img_save_path,'decrypted_img.png')) 
    
    
    #######################################################################
    # Prediciton Part
    model_path = 'COVID_Detection_model.pt'
    img_path = os.path.join(img_save_path,'decrypted_img.png')
    #img_path = 'Viral Pneumonia-1254.png'
    
    img = img_process(img_path)
    print(type(img))
    test_model = load_model(model_path)
    y = test_model(img)
    print(y)
    result = int(y.argmax())
    print(result)
    