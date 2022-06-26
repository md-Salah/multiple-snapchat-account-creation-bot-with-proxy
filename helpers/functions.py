from helpers.user import generate_user_info
import random
import os
from os import listdir
from os.path import isfile, join
import time


def read_txt(file_name):
    file_dir = os.getcwd() + "\\inputs\\" + file_name
    try:
        with open(file_dir, "r") as file:
            data = file.read()
            list = data.split("\n")
            data = []
            for site in list:
                data.append(site)
    except:
        print(f'{file_name} file not found in {file_dir}')
        exit()
    return data

def get_acc_info():
    users = read_txt('names.txt')
    data = []
    for user in users:
        user = generate_user_info(user)
        images = [f for f in listdir('images') if isfile(join('images', f))]
        index = random.randint(0,len(images)-1)
        image = os.path.abspath(os.getcwd()) + '\images\\' + images[index]
        user['img'] = image
        data.append(user)
    return data
    
def formatted_time(t, hours = False):
    m, s = divmod(t, 60)
    h, m = divmod(m, 60)
    if hours:
        return '{:d}:{:02d}:{:02d}'.format(h, m, s)
    else: 
        return '{:02d}:{:02d}'.format(m, s)

def countdown(t):
    while t:
        mins, secs = divmod(t, 60) 
        hours, mins = divmod(mins, 60)
        timer = '{:02d}:{:02d}:{:02d}'.format(hours, mins, secs) 
        print(timer, end="\r") 
        time.sleep(1) 
        t -= 1
    print('Waiting is over')
