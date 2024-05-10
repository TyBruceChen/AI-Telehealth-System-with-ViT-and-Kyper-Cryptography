from azure.storage.blob import BlobServiceClient, BlobClient
import os

Azure_Storage_Blob_Connection_String = 'DefaultEndpointsProtocol=https;AccountName=personalstoragenau;AccountKey=bQpPKvT5SA90REjWt9XOFa6Cr04S1tnFI/p1IvEE39nlv/rmfHVmgg8bgXhydeW1VxIBdO1cg7Wl+AStsM+NZQ==;EndpointSuffix=core.windows.net'
Container_Name = 'teleheathnau'



class blob_server_client():
    def __init__(self):
        try:
            self.blob = BlobServiceClient.from_connection_string(Azure_Storage_Blob_Connection_String) #connect to your Azure storage resource 
        except:
            print('Failed to connet to Azure Storage Service!')

    def store_file_blob(self,bin_file,filename,blob_folder = 'uploaded_imgs'):
        """
        This function upload the binary file to Azure_Storage/Container/Blob
        bin_file: the binary file you want to upload
        filename: the path that will the binary file
        """
        try:
            blob_name = os.path.join(blob_folder,filename)  # set the blob name (path + filename)
            blob_client = self.blob.get_blob_client(container = Container_Name, blob = blob_name)  #connect to the container and the underlying blob

            blob_client.upload_blob(bin_file,blob_type='BlockBlob',overwrite = True)
            print('Blob Upload Success!')
        except:
            print('Blob Upload Failure!')

    def download_file_blob(self,filename,storage_name):
        """
        filename: the storage path + file name in Azure blob
        storage_name: where you want to save to local
        """
        try:
            container_client = self.blob.get_container_client(container = Container_Name)
            with open(storage_name,'wb') as download:
                download.write(container_client.download_blob(filename).readall())
        except:
            print('Failed to download blob!')            

""" 
if __name__ == '__main__':
    try:
        print("Test packages are successfully imported.")

    except Exception as ex:
        print('Exception:')
        print(ex)
    
    blob_server_client = blob_server_client()

    test_file_path = 'files/Bart-Philip-me.png'
    storage_path = 'temp.png'
    with open(test_file_path,'rb') as bin_file:
        blob_server_client.store_file_blob(bin_file, storage_path)
   
    azure_file_path = 'models/Diagnosis_Model.pt'
    blob_server_client.download_file_blob(filename = azure_file_path,storage_name = 'Diagnosis_Model.pt')
"""