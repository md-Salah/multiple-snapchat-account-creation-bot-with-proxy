import os
import pickle
import time
import getpass
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

import os
import zipfile

class Scraper:
	# This time is used when we are waiting for element to get loaded in the html
	wait_element_time = 5

	# In this folder we will save cookies from logged in users
	cookies_folder = 'cookies' + os.path.sep

	def __init__(self, url, headless = False, proxy = False):
		self.url = url
		self.headless = headless
		self.setup_driver_options(headless, proxy)
		self.setup_driver()

	# Automatically close driver on destruction of the object
	def __del__(self):
		if self.headless == False: 
			# print('closing browser')
			pass
			
		
	# Add these options in order to make chrome driver appear as a human instead of detecting it as a bot
	# Also change the 'cdc_' string in the chromedriver.exe with Notepad++ for example with 'abc_' to prevent detecting it as a bot
	def setup_driver_options(self, headless, proxy):
		self.driver_options = Options()

		arguments = [
			'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
			'--start-maximized',
			'--disable-blink-features=AutomationControlled',
			'--disable-dev-shm-usage',
			'--no-sandbox'
		]

		experimental_options = {
			'excludeSwitches': ['enable-automation', 'enable-logging'],
			'prefs': {'profile.default_content_setting_values.notifications': 2}
		}

		for argument in arguments:
			self.driver_options.add_argument(argument)

		for key, value in experimental_options.items():
			self.driver_options.add_experimental_option(key, value)
		
		if headless:
			self.driver_options.add_argument('--headless')

		if proxy:
			# parts = proxy.split(':')
			# proxy = parts[0] + ':' + parts[1]
			# webdriver.DesiredCapabilities.CHROME['proxy'] = {
			# 	"httpProxy": proxy,
			# 	"ftpProxy": proxy,
			# 	"sslProxy": proxy,
			# 	"ProxyType": 'MANUAL',
			# }
			# webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True

			proxy= proxy.split(':')
			PROXY_HOST = proxy[0]
			PROXY_PORT = proxy[1]
			PROXY_USER = proxy[2]
			PROXY_PASS = proxy[3]

			manifest_json = """
			{
				"version": "1.0.0",
				"manifest_version": 2,
				"name": "Chrome Proxy",
				"permissions": [
					"proxy",
					"tabs",
					"unlimitedStorage",
					"storage",
					"<all_urls>",
					"webRequest",
					"webRequestBlocking"
				],
				"background": {
					"scripts": ["background.js"]
				},
				"minimum_chrome_version":"22.0.0"
			}
			"""

			background_js = """
			var config = {
					mode: "fixed_servers",
					rules: {
					singleProxy: {
						scheme: "http",
						host: "%s",
						port: parseInt(%s)
					},
					bypassList: ["localhost"]
					}
				};

			chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

			function callbackFn(details) {
				return {
					authCredentials: {
						username: "%s",
						password: "%s"
					}
				};
			}

			chrome.webRequest.onAuthRequired.addListener(
						callbackFn,
						{urls: ["<all_urls>"]},
						['blocking']
			);
			""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

			pluginfile = 'proxy_auth_plugin.zip'

			with zipfile.ZipFile(pluginfile, 'w') as zp:
				zp.writestr("manifest.json", manifest_json)
				zp.writestr("background.js", background_js)
			self.driver_options.add_extension(pluginfile)


	# Setup chrome driver with predefined options
	def setup_driver(self):
		self.s = Service(executable_path=os.path.join(os.curdir,'chromedriver'))
		self.driver = webdriver.Chrome(service=self.s, options = self.driver_options)
		self.driver.get(self.url)

	# Add login functionality and load cookies if there are any with 'cookies_file_name'
	def add_login_functionality(self, login_url, is_logged_in_selector, cookies_file_name):
		self.login_url = login_url
		self.is_logged_in_selector = is_logged_in_selector
		self.cookies_file_name = cookies_file_name + '.pkl'
		self.cookies_file_path = self.cookies_folder + self.cookies_file_name

		# Check if there is a cookie file saved
		if self.is_cookie_file():
			# Load cookies
			self.load_cookies()
			
			# Check if user is logged in after adding the cookies
			is_logged_in = self.is_logged_in(5)
			if is_logged_in:
				return
		
		# Wait for the user to log in with maximum amount of time 5 minutes
		print('Please login manually in the browser and after that you will be automatically loged in with cookies. Note that if you do not log in for five minutes, the program will turn off.')
		is_logged_in = self.is_logged_in(300)

		
		# User is not logged in so exit from the program
		if not is_logged_in:
			exit()

		# User is logged in so save the cookies
		self.save_cookies()

	# Check if cookie file exists
	def is_cookie_file(self):
		return os.path.exists(self.cookies_file_path)

	# Load cookies from file
	def load_cookies(self):
		# Load cookies from the file
		cookies_file = open(self.cookies_file_path, 'rb')
		cookies = pickle.load(cookies_file)
		
		for cookie in cookies:
			self.driver.add_cookie(cookie)

		cookies_file.close()

		self.go_to_page(self.url)

		time.sleep(5)

	# Save cookies to file
	def save_cookies(self):
		# Do not save cookies if there is no cookies_file name 
		if not hasattr(self, 'cookies_file_path'):
			return

		# Create folder for cookies if there is no folder in the project
		if not os.path.exists(self.cookies_folder):
			os.mkdir(self.cookies_folder)

		# Open or create cookies file
		cookies_file = open(self.cookies_file_path, 'wb')
		
		# Get current cookies from the driver
		cookies = self.driver.get_cookies()

		# Save cookies in the cookie file as a byte stream
		pickle.dump(cookies, cookies_file)

		cookies_file.close()

	# Check if user is logged in based on a html element that is visible only for logged in users
	def is_logged_in(self, wait_element_time = None):
		if wait_element_time is None:
			wait_element_time = self.wait_element_time

		return self.find_element(self.is_logged_in_selector, False, wait_element_time)

	# Wait random amount of seconds before taking some action so the server won't be able to tell if you are a bot
	def wait_random_time(self):
		random_sleep_seconds = round(random.uniform(0.20, 1.20), 2)

		time.sleep(random_sleep_seconds)

	# Goes to a given page and waits random time before that to prevent detection as a bot
	def go_to_page(self, page):
		# Wait random time before refreshing the page to prevent the detection as a bot
		self.wait_random_time()

		# Refresh the site url with the loaded cookies so the user will be logged in
		self.driver.get(page)

	def find_element(self, selector, exit_on_missing_element = True, wait_element_time = None):
		if wait_element_time is None:
			wait_element_time = self.wait_element_time

		# Intialize the condition to wait
		wait_until = EC.element_to_be_clickable((By.CSS_SELECTOR, selector))

		try:
			# Wait for element to load
			element = WebDriverWait(self.driver, wait_element_time).until(wait_until)
		except TimeoutException:
			if exit_on_missing_element:
				print('ERROR: Timed out waiting for the element with css selector "' + selector + '" to load')
				# End the program execution because we cannot find the element
				exit()
			else:
				return False

		return element
	
	def find_elements(self, selector, exit_on_missing_element = True, wait_element_time = None):
		collection = []

		if wait_element_time is None:
			wait_element_time = self.wait_element_time
		try:
			elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
			for element in elements:
				collection.append(element.text)
		except TimeoutException:
			if exit_on_missing_element:
				print('ERROR: Timed out waiting for the element with css selector "' + selector + '" to load')
				# End the program execution because we cannot find the element
				exit()
			else:
				return False

		return collection

	def find_element_by_xpath(self, xpath, exit_on_missing_element = True, wait_element_time = None):
		if wait_element_time is None:
			wait_element_time = self.wait_element_time

		# Intialize the condition to wait
		wait_until = EC.element_to_be_clickable((By.XPATH, xpath))

		try:
			# Wait for element to load
			element = WebDriverWait(self.driver, wait_element_time).until(wait_until)
		except TimeoutException:
			if exit_on_missing_element:
				# End the program execution because we cannot find the element
				print('ERROR: Timed out waiting for the element with xpath "' + xpath + '" to load')
				exit()
			else:
				return False

		return element

	def click_checkbox(self, selector_position):
		elements = self.driver.find_elements_by_tag_name('input[type="checkbox"]')[selector_position]
		elements.click()
	
	def select_dropdown(self, selector, val, text = False):
		element = self.find_element(selector)
		select = Select(element)
		if text:
			select.select_by_visible_text(val)
		else:
			if type(val) == int:
				val = str(val)
			select.select_by_value(val)

	def add_emoji(self, selector, text):
		JS_ADD_TEXT_TO_INPUT = """
		var elm = arguments[0], txt = arguments[1];
		elm.value += txt;
		elm.dispatchEvent(new Event('change'));
		"""
		element = self.driver.find_element_by_css_selector(selector)
		self.driver.execute_script(JS_ADD_TEXT_TO_INPUT, element, text)
		element.send_keys('.')
		element.send_keys(Keys.BACKSPACE)
		element.send_keys(Keys.TAB)

	def scroll_wait(self, selector, sleep_duration = 2):
		element = self.driver.find_element_by_css_selector(selector)
		self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", element);
		time.sleep(sleep_duration)
	
	# Wait random time before cliking on the element
	def element_click(self, selector, delay = True):
		if delay:
			self.wait_random_time()
			
		element = self.find_element(selector)
		element.click()
		
	def element_force_click(self, selector, loop_count=3, delay = True):
		element = False
		loop = 0
		while not element and loop < loop_count:
			if delay:
				self.wait_random_time()
			element = self.find_element(selector, False)
			if element:
				element.click()
			else:
				print(f"selector: {selector} not clickable yet, trying again")
				loop += 1
		if not element:
			exit()
				
	# Wait random time before cliking on the element
	def element_click_by_xpath(self, xpath, delay = True):
		if delay:
			self.wait_random_time()

		element = self.find_element_by_xpath(xpath)
		element.click()

	def element_force_click_by_xpath(self, xpath, loop_count=3, delay = True):
		element = False
		loop = 0
		while not element and loop < loop_count:
			if delay:
				self.wait_random_time()
			try:
				element = self.find_element_by_xpath(xpath)
				element.click()
			except TimeoutException:
				print(f"button: {xpath} not clickable yet, trying again")
				loop += 1

	# Wait random time before sending the keys to the element
	def element_send_keys(self, selector, text, delay = True):
		if delay:
			self.wait_random_time()

		element = self.find_element(selector)

		element.send_keys(text)

	# Wait random time before cliking on the element
	def element_click_by_xpath(self, xpath, exit_on_missing_element=False, delay = True):
		if delay:
			self.wait_random_time()

		try: 
			element = self.find_element_by_xpath(xpath)
			element.click()
		except:
			if exit_on_missing_element:
				exit()
			else:
				return False
		return element

	# scraper.input_file_add_files('input[accept="image/jpeg,image/png,image/webp"]', images_path)
	def input_file_add_files(self, selector, files):
		# Intialize the condition to wait
		wait_until = EC.presence_of_element_located((By.CSS_SELECTOR, selector))

		try:
			# Wait for input_file to load
			input_file = WebDriverWait(self.driver, self.wait_element_time).until(wait_until)
		except TimeoutException:
			print('ERROR: Timed out waiting for the input_file with selector "' + selector + '" to load')
			# End the program execution because we cannot find the input_file
			exit()

		self.wait_random_time()

		try:
			input_file.send_keys(files)
		except InvalidArgumentException:
			print('ERROR: Exiting from the program! Please check if these file paths are correct:\n' + files)
			exit()

	# Wait random time before clearing the element (popup)
	def element_clear(self, selector, delay = True):
		if delay:
			self.wait_random_time()

		element = self.find_element(selector)

		element.clear()

	def element_wait_to_be_invisible(self, selector):
		wait_until = EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))

		try:
			WebDriverWait(self.driver, self.wait_element_time).until(wait_until)
		except:
			print('Error waiting the element with selector "' + selector + '" to be invisible')
