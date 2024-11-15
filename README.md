# AI-Telehealth-System-with-ViT-and-Kyper-Cryptographic
An Easy-to-Implement AI Telehealth System for Medical Diagnosis and [Post-Training Interpretation](https://github.com/TyBruceChen/Animated2GradCAM) (loading Grad-CAM images from the corresponding model with the interactive [animint2](https://github.com/animint/animint2) R package) <br>

Code Source of **Conference Paper: A Highly Secure and Accurate System for COVID-19 Diagnosis from Chest X-ray Images** ([google scholar](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=r2ZKGxAAAAAJ&citation_for_view=r2ZKGxAAAAAJ:d1gkVwhDpl0C) or [IEEE](https://ieeexplore.ieee.org/abstract/document/10658795)). **Published in**: [2024 IEEE 67th International Midwest Symposium on Circuits and Systems (MWSCAS)](https://ieeexplore.ieee.org/xpl/conhome/10654782/proceeding) 

### Abstract:
Global healthcare systems face growing pressure as populations rise. This can lead to longer wait times and an increased risk of treatment delays or misdiagnosis. Artificial intelligence (AI) diagnostic systems are being developed to address these challenges, but concerns exist about their accuracy and data security. This study introduces a robust AI telehealth system that offers a two-pronged approach. It utilizes a cutting-edge image analysis method, vision transformer, to enhance diagnostic accuracy, while also incorporating post-quantum cryptography algorithm, Kyber, to ensure patient privacy. Furthermore, an [interactive visualization tool](https://github.com/TyBruceChen/Animated2GradCAM) aids in interpreting the diagnostic results, providing valuable insights into the model's decisionmaking process. This translates to faster diagnoses and potentially shorter wait times for patients. Extensive testing with various datasets has demonstrated the system's effectiveness. The optimized model achieves a remarkable 95.79% accuracy rate in diagnosing COVID-19 from chest X-rays, with the entire process completed in under five seconds.

### Implementation details: 
* The main program is ```app.py```, which is Flask-server-based. We run our code at VS Code with python 3.8. The required packages reside in the ```requirements.txt```. To run the program, enter the command ```python app.run```. The service handling port will open at ```5000``` as configured at the bottom.
* Some environment parameters need to be configured for re-deployment, they are located at the top of ```app.py```, ```Encryption_Kyber/*.py``` with well-explained comments.
* We deployed the system locally and used the [fast reverse proxy (frp)](https://github.com/fatedier/frp) to expose the service to the public by connecting it to the Amazon server.

### How it looks like:

![Web App](GitHub-Pictures/AI-Telehealth-Flask-Web-App2.jpeg)

### Reference:
    @INPROCEEDINGS{10658795,
    author={Nguyen, Tuy Tan and Chen, Tianyi and Philippi, Ian and Phan, Quoc Bao and Kudo, Shunri and Huda, Samsul and Nogami, Yasuyuki},
    booktitle={2024 IEEE 67th International Midwest Symposium on Circuits and Systems (MWSCAS)}, 
    title={A Highly Secure and Accurate System for COVID-19 Diagnosis from Chest X-Ray Images}, 
    year={2024},
    volume={},
    number={},
    pages={980-984},
    keywords={COVID-19;Computer vision;Accuracy;Data visualization;Medical services;Transformers;Artificial intelligence;Computer-aid diagnosis;Kyber;image classification;COVID-19},
    doi={10.1109/MWSCAS60917.2024.10658795}}
