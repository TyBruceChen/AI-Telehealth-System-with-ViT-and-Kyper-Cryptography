# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 12:39:18 2024

@author: tc922
"""

import os,sys,inspect
import cv2
import matplotlib.pyplot as plt
from PIL import Image
import io
import base64
import numpy as np

import sys

mfolder = 'C:/Users/tc922/Downloads/CLIENT-Side/Encryp_Kyber/' #the location of encryption files

sys.path.append(os.path.join(mfolder,'Kyber'))

from kyber import  Kyber512 #you should also try Kyber768 and Kyber 1024
import os
import time
import numpy as np


def bytes_to_number_string(byte_string):
    return ','.join(str(b) for b in byte_string)


def key_gen():
    public_key, secret_key = Kyber512.keygen()
    
    return public_key, secret_key

def kyber_encryption(public_key,image_bytes):
    chunk_size = 32
    
    ciphertexts = []
    cipher_number = []
    decrypted_chunks = []

    for i in range(0, len(image_bytes), chunk_size):
        # Extract a chunk of audio data
        chunk = image_bytes[i:i+chunk_size]

        remainder = len(chunk) % 32
        if remainder != 0:
            # Pad the audio data with zeros to make it a multiple of 32 bytes
            padding_length = 32 - remainder
            chunk += b'\x00' * padding_length

        # Encrypt the chunk with the public key
        ciphertext = Kyber512._cpapke_enc(public_key, chunk, coins=os.urandom(32))
        number_string = bytes_to_number_string(ciphertext)
        ciphertexts.append(ciphertext)
        cipher_number.append(number_string)
    
    return ciphertexts
    
def kyber_decryption(secret_key, ciphertexts):
    chunk_size = 32
    len_image_bytes = 9871 # =len(image_bytes)
    
    decrypted_chunks = []
    for ciphertext in ciphertexts:
        # Decrypt the ciphertext with the secret key
        decrypted_chunk_bytes = Kyber512._cpapke_dec(secret_key, ciphertext)

        # Step 6: Remove any padding to obtain the decrypted audio data
        decrypted_chunk_bytes = decrypted_chunk_bytes[:chunk_size]

        # Convert the decrypted bytes back to a NumPy array
        decrypted_chunk = np.frombuffer(decrypted_chunk_bytes, dtype=np.float32)

        # Append the decrypted chunk to the list of decrypted chunks
        decrypted_chunks.append(decrypted_chunk)

    # Combine the decrypted chunks into the final decrypted audio data
    decrypted_img_array = np.concatenate(decrypted_chunks)
    decrypted_img_array = decrypted_img_array[:len_image_bytes]
    decrypted_img_bytes = io.BytesIO()
    decrypted_img_bytes.write(decrypted_img_array.tobytes())
    decrypted_img_bytes.seek(0)
    decrypted_img_bytes = decrypted_img_bytes.read()
    print(io.BytesIO(decrypted_img_bytes))
    decrypted_img = Image.open(io.BytesIO(decrypted_img_bytes))
    
    return decrypted_img



if __name__ == '__main__':

    root_path = './Test_Set'
    img_save_path = './results'
    key_path = './token'
    enc_path = './encrypted_data'
    img_name = os.listdir(root_path)[0]
    image_path = os.path.join(root_path,img_name)
    image = Image.open(image_path)
    
    rescale_size = (299, 299)
    rescale_image = image.resize(rescale_size, Image.BICUBIC)
    rescale_image.save(os.path.join(img_save_path,'rescale_image.png'))
    
    """
    norm_img = plt.imread(os.path.join(img_save_path,'rescale_image.png'))
    
    plt.hist(norm_img.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')
    plt.show()
    """
    
    rescale_image_bytes = io.BytesIO()
    rescale_image.save(rescale_image_bytes, format='JPEG')
    image_bytes = rescale_image_bytes.getvalue()
    
    
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
        
    
    enc_data = kyber_encryption(public_key = pub_k, image_bytes = image_bytes)
    
    for i,data_chunk in enumerate(enc_data):
        data_path = os.path.join(enc_path,'enc_data-'+str(i))
        with open (data_path,'wb') as data:
            data.write(data_chunk)
    
    list_enc_data = []
    for i,data_chunk in enumerate(enc_data):
        data_path = os.path.join(enc_path,'enc_data-'+str(i))
        with open (data_path,'rb') as data:
            chunk_info = data.read()
        list_enc_data.append(chunk_info)
    
    ciphertext_string = b''.join(enc_data)
    
    # Convert the concatenated ciphertext to base64-encoded string
    encrypted_image_string = base64.b64encode(ciphertext_string).decode('utf-8')
    
    # Create a new image with the desired size
    enc_img = Image.new('L', (299, 299)) #Use 'L' flag for gray image
    # Encode the base64-encoded string as an image
    enc_img.frombytes(base64.b64decode(encrypted_image_string), 'raw', 'L', 0, 1) #Use 'L' flag for gray image
    # Save the encrypted image to a file
    enc_img.save(os.path.join(img_save_path,'encrypted_image.png'))
    
    dec_img = kyber_decryption(secret_key = sec_k, ciphertexts = list_enc_data)
    
    
    #dec_img.show()
    dec_img.save(os.path.join(img_save_path,'decrypted_img.png')) 








"""
image_number = 1
root_path = './Test_Set'
img_save_path = "./results"

for file in os.listdir(root_path):
    print(file)
    image_path = os.path.join(root_path,file)
    image = Image.open(image_path)

    #norm_img = plt.imread(image_path)
    #plt.hist(norm_img.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')
    #plt.show()

    #print(image)
    #image_data = cv2.imread(image)
    #cv2_imshow( image_data )
    rescale_size = (299, 299)
    rescale_image = image.resize(rescale_size, Image.BICUBIC)
    rescale_image.save(os.path.join(img_save_path,'rescale_image.png'))

    norm_img = plt.imread(os.path.join(img_save_path,'rescale_image.png'))

    plt.hist(norm_img.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')
    plt.show()

    rescale_image_bytes = io.BytesIO()
    rescale_image.save(rescale_image_bytes, format='JPEG')
    image_bytes = rescale_image_bytes.getvalue()
    display(rescale_image)
    
    #plt.hist(rescale_image.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')
    #gray_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
    #reshaped_img = gray_image.reshape(89401,)

    # Step 1: Load your image data as a

    # Step 2: Generate a key pair
    public_key, secret_key = Kyber512.keygen()

    # Step 3: Define the chunk size (adjust as needed)s
    chunk_size = 32

    # Measure encryption time
    encryption_start_time = time.time()

    # Step 4: Encrypt and decrypt audio data in chunks
    ciphertexts = []
    cipher_number = []
    decrypted_chunks = []

    for i in range(0, len(image_bytes), chunk_size):
        # Extract a chunk of audio data
        chunk = image_bytes[i:i+chunk_size]

        remainder = len(chunk) % 32
        if remainder != 0:
            # Pad the audio data with zeros to make it a multiple of 32 bytes
            padding_length = 32 - remainder
            chunk += b'\x00' * padding_length

        # Encrypt the chunk with the public key
        ciphertext = Kyber512._cpapke_enc(public_key, chunk, coins=os.urandom(32))
        number_string = bytes_to_number_string(ciphertext)
        ciphertexts.append(ciphertext)
        cipher_number.append(number_string)

    # print(f"Ciphertext: ",ciphertext)

    # Measure encryption time
    encryption_end_time = time.time()

    # Concatenate ciphertexts into a single string
    ciphertext_string = b''.join(ciphertexts)

    # Convert the concatenated ciphertext to base64-encoded string
    encrypted_image_string = base64.b64encode(ciphertext_string).decode('utf-8')

    # Create a new image with the desired size
    enc_img = Image.new('L', (299, 299)) #Use 'L' flag for gray image
    # Encode the base64-encoded string as an image
    enc_img.frombytes(base64.b64decode(encrypted_image_string), 'raw', 'L', 0, 1) #Use 'L' flag for gray image
    # Save the encrypted image to a file
    enc_img.save(os.path.join(img_save_path,'encrypted_image.png'))
    display(enc_img)

    enc_hist = plt.imread(os.path.join(img_save_path,'encrypted_image.png'))
    plt.hist(enc_hist.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')
    plt.show()

    # Measure decryption time
    decryption_start_time = time.time()

    # Decrypt the ciphertexts
    decrypted_chunks = []
    for ciphertext in ciphertexts:
        # Decrypt the ciphertext with the secret key
        decrypted_chunk_bytes = Kyber512._cpapke_dec(secret_key, ciphertext)

        # Step 6: Remove any padding to obtain the decrypted audio data
        decrypted_chunk_bytes = decrypted_chunk_bytes[:len(chunk)]

        # Convert the decrypted bytes back to a NumPy array
        decrypted_chunk = np.frombuffer(decrypted_chunk_bytes, dtype=np.float32)

        # Append the decrypted chunk to the list of decrypted chunks
        decrypted_chunks.append(decrypted_chunk)

    # Combine the decrypted chunks into the final decrypted audio data
    decrypted_img_array = np.concatenate(decrypted_chunks)
    decrypted_img_array = decrypted_img_array[:len(image_bytes)]
    decrypted_img_bytes = io.BytesIO()
    decrypted_img_bytes.write(decrypted_img_array.tobytes())
    decrypted_img_bytes.seek(0)
    decrypted_img_bytes = decrypted_img_bytes.read()

    # Measure decryption time
    decryption_end_time = time.time()

    # Calculate the elapsed times
    encryption_elapsed_time = encryption_end_time - encryption_start_time
    decryption_elapsed_time = decryption_end_time - decryption_start_time

    print(f"Encryption time: {encryption_elapsed_time} seconds")
    print(f"Decryption time: {decryption_elapsed_time} seconds")

    # Convert decrypted bytes to an image
    decrypted_img = Image.open(io.BytesIO(decrypted_img_bytes))
    # decrypted_img.save('dec_img.png')
    # Display the decrypted image
    display(decrypted_img)

    rescaled_final_image = image.resize(rescale_size, Image.BICUBIC)

    rescale_image.save(os.path.join(img_save_path,'rescaled_final_image.png'))
    final_img = plt.imread(os.path.join(img_save_path,'rescaled_final_image.png'))
    plt.hist(final_img.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')
    plt.show()

    #enc_img.save('encrypted_image.png')
    #ori_img = decrypted_img_bytes.reshape(200,200)

    # Create a new image with the desired size
    #dec_img = Image.new('L', (100, 100)) #Use 'L' flag for gray image
    # Encode the base64-encoded string as an image
    #dec_img.frombytes(base64.b64decode(decrypted_img_bytes), 'raw', 'L', 0, 1) #Use 'L' flag for gray image
    # Save the encrypted image to a file
    #enc_img.save('encrypted_image.png')


    # Verify that the decrypted image data matches the original
    if np.array_equal(image_bytes, decrypted_img_bytes):
        print("Decryption successful")
    else:
        print("Decryption failed or image data mismatch.")

    image_number = image_number + 1
"""