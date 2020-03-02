import requests 
import json

addr = 'http://127.0.0.1:5000'

iris_url = addr + '/predict_petal_length_api'
data = {'petal_width': 2}

r = requests.post(iris_url, json=data)

# print(r.status_code)
# print(r.text)

planet_url = addr + '/upload_file_api'

files = {
    'file1': open('data/raw/test-jpg/test_11.jpg', 'rb'),
    'file2': open('data/raw/test-jpg/test_14.jpg', 'rb')
    }   
 
r = requests.post(planet_url, files=files)
print(r.status_code)
print(r.text)

# curl -F "file=@data/raw/test-jpg/test_11.jpg" http://localhost:5000/upload_file_api