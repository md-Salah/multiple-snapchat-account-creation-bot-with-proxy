import time
from helpers.scraper import Scraper
from selenium.common.exceptions import TimeoutException
import os
import random
import pandas as pd
from helpers.functions import read_txt, countdown
from helpers.user import generate_user_info

def fill_the_form(scraper, user):
    # Fill up the user info
    scraper.element_send_keys('input[name="firstName"]', user['f_name'])
    scraper.element_send_keys('input[name="lastName"]', user['l_name'])
    scraper.element_send_keys('input[name="username"]', user['username'])
    scraper.element_send_keys('input[name="password"]', user['password'])
    scraper.element_send_keys('input[name="email"]', user['email'])
    scraper.select_dropdown('select[name="birthdayMonth"]', user['month'])
    scraper.element_send_keys('input[name="birthdayDay"]', user['day'])
    scraper.element_send_keys('input[name="birthdayYear"]', user['year'])
    
    # Click Sign Up button
    scraper.element_click_by_xpath(
        '/html/body/div/div/div/div[3]/div[1]/div[1]/div/div/div[4]/div/form/div[7]/div/button'
    )    

if __name__ == "__main__":
    credentials = []
    proxies = read_txt('proxies.txt')
    url = read_txt('websites.txt')[0]
    output_dir = os.getcwd() + "\\outputs\\" + "accounts.csv"

    n = int(input('how many accounts you want to create: '))
    
    for i in range(1, n+1):
        if i > 1:
            print('waiting 5 seconds before next account creation')

        proxy = proxies[random.randint(0, len(proxies)-1)]
        print(f'Account: {i}, proxy connected: {proxy}')

        try: 
            user = generate_user_info()
            scraper = Scraper(url, proxy=proxy)            
            fill_the_form(scraper, user)            
            credentials.append([user['email'], user['password']])
            pd.DataFrame(credentials, columns=['email', 'password']).to_csv(output_dir, index=False)
            print('waiting 15 seconds to initiate account')              
            countdown(15)
            
            scraper.find_element_by_xpath(
                '//*[@id="page-container"]/div/div/form/div/div[4]/div/button/span',
                exit_on_missing_element=False,
                wait_element_time= 20
            ).click()
            scraper.find_element_by_xpath(
                '//*[@id="page-container"]/div/div/div[1]/div/div[1]/div[2]/button[2]',
                exit_on_missing_element=False,
                wait_element_time= 20
            ).click()
            scraper.find_element_by_xpath(
                '/html/body/div[4]/div/div[2]/div/div[2]/div[3]/div/button',
                exit_on_missing_element=False,
                wait_element_time= 20
            ).click()
            
        except TimeoutException: 
            print('something unpredictable occured, retrying..')
            i -= 1

        scraper.driver.close()
        time.sleep(5)
    
    os.system('cls')
    print(f'total account created: {n}')
    print('find those in: outputs > accounts.csv')
    os.system('pause')