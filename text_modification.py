
class text_modification():
    def __init__(self,replace_text_path = 'templates/index.html'):
        with open (replace_text_path,'r') as f:
            self.content = f.read()

    def replace_content(self,new_element,replaced_element = 'Test Page'):
        self.content = self.content.replace(replaced_element, new_element)
        #self.replaced_element = new_element
        return self.content
    
def lung_type(cls_num,ls = ['COVID-19','Lung-Opacity','Normal','Pneumonia']):
    return ls[cls_num]