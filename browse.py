import logging
import os
import sys
import urllib
from zipfile import ZipFile
from contextlib import contextmanager
from functools import partial
from os import makedirs, path
from random import random
from time import sleep
from types import FunctionType
import bs4
import regex as re
import requests
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.remote_connection import LOGGER as S_LOGGER
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

cwd = os.getcwd()
log_path = path.join(path.split(cwd)[0], __file__)
logging.basicConfig(filename='{0}.log'.format(log_path), level=logging.INFO)

class Browser(object):
	"""
	WebRunner runs an instance of Selenium and adds a lot of helpful
	browser methods.

	Generally this class aims to make the experience of using Selenium
	better overall.

	Many functions take a "selector" argument.
	These can be any valid CSS selector..
	See https://developer.mozilla.org/en-US/docs/Web/Guide/CSS/Getting_started/Selectors
	"""

	# Variables for configuration
	# browser = None
	# extra_verbose = False
	# silence = open(os.devnull, 'w')
	options = webdriver.ChromeOptions()
	profile = {"plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}], # Disable Chrome's PDF Viewer
               "plugins.always_open_pdf_externally":True,
               "download.extensions_to_open": "applications/pdf",
			"user-agent"                  : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 "
											"Safari/537.36",
			"download.default_directory"  : "C:\\Users\\Ahmad\\OneDrive\\Documents\\Downloads",
			"download.prompt_for_download": False,
			"download.directory_upgrade"  : True

			}

	options.add_experimental_option('prefs', profile)
	# options.add_argument('load-extension={0}'.format("C:\\Users\\Ahmad\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Extensions\\mhjhnkcfbdhnjickkkdbjoemdmbfginb\\1.1_0"))
	options.add_argument('--ignore-certificate-errors')
	options.add_argument('--ignore-ssl-errors')
	options.add_argument('log-level=3')
	def __init__(self, link, headless=False, download_dir = False, maximize=False, path_to_chrome_driver=None):
		"""
		:type download_dir: str or bool
		"""
		if headless is True:
			self.options.headless = True
		else:
			self.options.headless = False
		print("Download DIR", download_dir)
		if download_dir:
			if not path.isdir(download_dir):
				os.makedirs(download_dir)
			self.profile["download.default_directory"] = str(download_dir)
			self.options.add_experimental_option('prefs', self.profile)
		if path_to_chrome_driver:
			try:
				self.driver = webdriver.Chrome(executable_path=path_to_chrome_driver, chrome_options=self.options)
			except SessionNotCreatedException or WebDriverException as e:
				exception_string = str(e)
				print(exception_string)
				# NEED TO
				if ("version" in exception_string.lower() and "chromedriver" in exception_string.lower()) or ("executable" in exception_string.lower() and "path" in exception_string.lower()):
					# Go to Chromedriver download page
					driver_download_page = requests.get("https://chromedriver.chromium.org/home")
					# Soup Page Contents
					dp_soup = bs4.BeautifulSoup(driver_download_page.text)
					# Get Current Stable Releases element
					current_releases_text = dp_soup.find(string=re.compile(r'current stable', flags=re.I))
					li_parent = current_releases_text.find_parent("li")
					# Find the first li tag, select the first a tag with an href and get the href
					download_href = li_parent.select('a[href]')[0].get('href')
					# Parse the href for the directory of the path of the most recent chromedriver zip file
					parsed_dl_href = urllib.parse.urlparse(download_href)
					# Create a link to the most recent chromedriver zip file
					download_link = urllib.parse.urljoin(download_href, parsed_dl_href.query.replace("path=","")) + "chromedriver_mac64.zip"
					# Get the link to the Zip File
					file_html = requests.get(download_link)
					# Download the Zip File to the path given
					zip_file_path = path_to_chrome_driver + ".zip"
					print(path_to_chrome_driver)
					with open(zip_file_path, "wb") as f:
						f.write(file_html.content)
					# Extract Zip File contents to that dir
					with ZipFile("zip_file_path", 'r') as zip:
						zip.extractall()

					raise WebDriverException(f"Downloaded ChromeDriver Zip Folder. Go to {os.getcwd()} to extract the chromedriver")




		else:
			try:
				self.driver=webdriver.Chrome(options=self.options)
			except WebDriverException:
				self.driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\Google\Chrome\Application\76.0.3809.100\chromedriver.exe", options=self.options)
		self.root_path = '/'
		if maximize:
			self.driver.maximize_window()
		self.driver.get(link)
		self.errors = False
		self.timeout = 10
		self.width = 1440
		self.height = 1200
		self.default_offset = 0
		self.js_error_collector = True
		self.KEYS = Keys
		self.yaml_funcs = {}
		self.yaml_vars = {}
		self.actions = ActionChains(self.driver)
		S_LOGGER.setLevel(logging.WARNING)

	def wait_for(self, method, **kwargs):
		"""
		Wait for the supplied method to return True. A simple wrapper for _wait_for().

		Parameters
		----------
		method: callable
				The function that determines the conditions for the wait to finish
		timeout: int
				Number of seconds to wait for `method` to return True
				:param method:
				:param kwargs:
		"""
		self._wait_for(method, **kwargs)

	def back(self):
		"""
		Goes one step back in the browser's history.
		Just a convenient wrapper around the browser's back command

		:return:
		"""

		self.driver.back()
		if self.alert_present():
			self.close_alert()


	def forward(self):
		"""
		Goes one step forward in the browser's history.
		Just a convenient wrapper around the browser's forward command

		:return:
		"""
		self.driver.forward()

	def click(self, selector, elem=None, timeout=None):
		"""
		Clicks an element.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector..
			:param timeout:
			:param elem:

		"""
		self.wait_for_presence(selector, timeout=timeout)
		self.scroll_to_element(selector)
		self.wait_for_clickable(selector, timeout=timeout)

		if not elem:
			elem = self.get_element(selector)


		elem.click()

	def maximize_window(self):
		"""
		Maximizes the window.
		"""
		self.driver.maximize_window()

	def set_window_size(self, width=None, height=None):
		"""
		Sets the window size.

		Parameters
		----------
		width: int
			Width of window in pixels
		height: int
			Height of the window in pixels

		"""
		if not width:
			width = self.width
		if not height:
			height = self.height

		self.driver.set_window_size(int(width), int(height))

	def get_js_errors(self):
		"""
		Uses the JSErrorCollector plugin for Chrome / Firefox to get any JS errors.
		[
			{
				'sourceName': u'tests/html/js_error.html',
				'pageUrl': u'tests/html/js_error.html',
				'errorMessage': 'ReferenceError: b is not defined',
				'lineNumber': 7
			}
		]
		"""
		if self.driver in ('Chrome', 'Firefox'):
			return self.js('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []')
		else:
			print("Checking for JS errors with this method only works in Firefox or Chrome")
			return []

	def get_log(self, log=None):
		"""
		Gets the console log for the browser.
		"""
		if not log:
			log = 'browser'
		log_list = self.driver.get_log(log)
		return log_list

	def set_timeout(self, timeout=90):
		"""
		Sets the global wait timeout.

		Parameters
		----------
		timeout: int
			Amount of time to wait (in seconds) before accepting that an action cannot occur. (Crash)

		"""
		self.timeout = int(timeout)

	def set_default_offset(self, default_offset=0):
		"""
		Sets the global default offset for scroll_to_element.

		Parameters
		----------
		offset: int
			The offset in pixels.
			:param default_offset:

		"""
		self.default_offset = int(default_offset)

	def focus_window(self, windex=None):
		"""
		Focuses on the window with index (#).

		Parameters
		----------
		windex: int
			The index of the window to focus on. Defaults to the first window opened.

		"""
		if not windex:
			windex = 0
		self.driver.switch_to.window(self.driver.window_handles[windex])

	def focus_browser(self):
		"""
		Raises and closes an empty alert in order to focus the browser app in most OSes.
		"""
		self.js('alert("");')
		self.close_alert()

	def get_log_text(self):
		"""
		Gets the console log text for the browser.
		[{u'level': u'SEVERE',
		u'message': u'ReferenceError: foo is not defined',
		u'timestamp': 1450769357488,
		u'type': u''},
		{u'level': u'INFO',
		u'message': u'The character encoding of the HTML document was not declared. The document will render with garbled text in some browser
		configurations if the document contains characters from outside the US-ASCII range. The character encoding of the page must be declared in
		the document or in the transfer protocol.',
		u'timestamp': 1450769357498,
		u'type': u''}]
		"""
		log = self.get_log()
		log_text = ''
		log_items = [item['message'] for item in log]
		for item in log_items:
			log_text += item + '\n'
		return log_text
##change
	@staticmethod
	def bail_out(line=None, exception=None, caller=None):
		"""
		Method for reporting and, optionally, bypassing errors during a command.

		Parameters
		----------
		exception: Exception
			The exception object.
		caller: str
			The method that called the bail_out.
			:param line:
			:param exception:
			:param caller:

		"""
		print(line)
		print(caller)
		print(exception)


	def click_all(self, selector):
		"""
		Clicks all elements.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector..
			All matching elements will be clicked.

		"""

		elements = self.get_elements(selector)
		for element in elements:
			if element.is_displayed:
				element.click()

	def get_page_source(self):
		"""
		Gets the source code of the page.
		"""
		src = self.driver.page_source
		return src

	def is_text_on_page(self, text):
		"""
		Finds text if it is present on the page.

		Parameters
		----------
		text: str
			The text to search for.

		"""
		src = self.get_page_source()
		# try:
		#     src = src.encode('ascii', errors='ignore')
		#     return bool(text in src)
		# except TypeError:
		index = src.find(text)
		if index == -1:
			return False
		return True

	def scroll_browser(self, amount, direction='down'):
		"""
		Scrolls the browser by the given amount in the specified direction.

		Parameters
		----------
		amount: int
			number of pixels to scroll

		direction: str
			(up, down, left, right) defaults to 'down'
		"""
		if direction in ('up', 'right'):
			amount = amount * -1

		if direction in ('up', 'down'):
			scroll_string = "window.scrollBy(0, {0});".format(amount)

		if direction in ('right', 'left'):
			scroll_string = "window.scrollBy({0}, 0);".format(amount)

		if scroll_string:
			self.js(scroll_string)

	def newtab(self):
		"""
		opens link in new tab and switches to that tab.

		Parameters
		----------
		link: url to open in new window.
		"""
		self.driver.execute_script(f"window.open('');")

		recent_tab = self.driver.window_handles[-1]
		self.driver.switch_to.window(recent_tab)
	
	def close_current_tab(self):
		self.close_window(self.driver.current_window_handle)
	
	def open_in_new_tab(self, webelement):
		self.move_to(webelement)
		webelement.send_keys(Keys.CONTROL + Keys.ENTER)
		self.wait(2)
		recent_tab = self.driver.window_handles[-1]
		self.driver.switch_to.window(recent_tab)
		
	
		
	def scroll_to_element(self, selector, offset=None, offset_selector=None):
		"""
		Scrolls the given element into view.

		Parameters
		----------
		selector: str
			Any valid css selector
		offset: number
			Number of pixels to offset the scroll
		offset_selector: str
			A selector whose corresponding element's height
			will be added to the offset
		"""
		if offset is None:
			offset = self.default_offset

		if offset_selector:
			offset_el = self.get_element(offset_selector)
			if offset_el:
				offset += offset_el.size['height']

		scroll_to_el = self.get_element(selector)

		scroll_location = scroll_to_el.location['y'] - offset
		self.js("window.scrollTo(0, arguments[0]);", scroll_location)
		self.wait(0.5)  # no good way to wait for scrolling to finish

	def set_select_by_text(self, select, text):
		"""
		Set the selected value of a select element by the visible text.

		Parameters
		----------
		select: str or selenium.webdriver.remote.webelement.WebElement
			Any valid CSS selector or a selenium element
		text: str
			The visible text in the select element option. (Not the value)

		"""
		if isinstance(select, str):
			elem = self.get_element(select)
		else:
			elem = select

		sel = Select(elem)
		sel.select_by_visible_text(text)

	def set_select_by_value(self, select, value):
		"""
		Set the selected value of a select element by the value.

		Parameters
		----------
		select: str or selenium.webdriver.remote.webelement.WebElement
			Any valid CSS selector or a selenium element
		value: str
			The value on the select element option. (Not the visible text)

		"""
		if isinstance(select, str):
			elem = self.get_element(select)
		else:
			elem = select

		sel = Select(elem)
		sel.select_by_value(value)

	def download(self, file_url, filepath=None, filename=None):
		"""
		Download a file.

		Parameters
		----------
		filepath: str
			The location and name of the file.
		src: str
			The URL to download
			:param src:
			:param filepath:
		"""
		
		if not filename:
			filename = urllib.parse.unquote(os.path.basename(file_url))
		print(f"{'_'*100}\nCurrently Downloading: {filename}")
		filepath = os.path.join(filepath, filename)
		urllib.request.urlretrieve(file_url, filepath)
		print(f"Download Complete.")
	def save_image(self, filepath, selector=None, elem=None):
		"""
		Download an image.

		Parameters
		----------
		filepath: str
			The location and name of the file.
		selector: str
			Any valid CSS selector
			:param elem:
		"""
		if selector:
			elem = self.get_element(selector)

		if elem:
			src = elem.get_attribute('src')
			download_file(src, filepath)



	def search(self, search_bar_xpath, query):
		"""
		Search Website for Query

		Paramters
		---------
		search_bar_xpath: The location of the search bar.
		query: The query used to search the site.

		"""
		if search_bar_xpath.startswith('//'):
			search_bar = self.find_element_by_xpath(search_bar_xpath)
		else:
			search_bar = self.find_element(search_bar_xpath)
		success=False
		try:
			#	Check that the page has a search bar.
			if search_bar:
				self.move_to(search_bar_xpath, click=True)
				print("Searching for {0}.".format(query))
				#	Get the search bar element.
				#	Clear Search Text
				search_bar.clear()
				#	Input Search Term
				search_bar.send_keys(query)
				with self.wait_for_page_load():
					# Search for the submit button
					search_bar.send_keys(self.KEYS.RETURN)
				success = True
				print("Search for {0} succeeded.".format(query))
		except UnexpectedAlertPresentException as e:
			#	If an alert is present, accept it. If that does not work, dismiss it.
			self.accept_alert()
			if self.alert_present():
				self.dismiss_alert()
			self.search(search_bar_xpath, query)
		except TimeoutException as e:
			print("Search Failed: Website not responding.\nURL: {0}".format(self.url))
			logging.exception("Search Failed: Website not responding - {0}\nException: {1}\nTraceback: {2}".format(self.url, str(e), str(sys.exc_info())))
			success = False
		except ElementNotInteractableException as e:
			print("Search Failed: Could not interact with search bar.\nError: {}.".format(str(e)))
			logging.exception("Search Failed: Could not interact with search bar - {0}\nException: {2}\nTraceback: {1}".format(self.url, str(sys.exc_info()), str(e)))
			success = False
		except ElementNotVisibleException as e:
			print("Search Failed: Element not visible.\nURL: {0}\nTraceback:{1}".format(self.url, str(sys.exc_info())))
			self.js('arguments[0].sendKeys("{0} + {1}");'.format(query, self.KEYS.RETURN), search_bar)
			logging.exception("Search Failed: Could not interact with invisible search bar - {0}\nException: {1}\nTraceback: {2}".format(self.url, str(e),str(sys.exc_info())))
		except BaseException as e:
			print("Search Failed: {0}".format(str(e)))
			logging.exception("Search Failed: {0}\nTraceback: {1}".format(str(e), str(sys.exc_info())))
			success = False
		finally:
			return success

	def set_element_attr(self, element, attr, value):
		self.driver.execute_script("return arguments[0].setAttribute('{0}', '{1}');".format(attr, value), element)

	def get_element_html(self, element, inner=True):
		"""

		:param element: Selected WebElement
		:param inner: if true, gets inner html of element. Default is True.
		:return: Element HTML
		"""
		try:
			if inner:
				return self.driver.execute_script("return arguments[0].innerHTML;", element)
			else:
				return self.driver.execute_script("return arguments[0].outerHTML;", element)
		except StaleElementReferenceException as e:
			logging.exception("Could not get html.\nELEMENT NAME: {0}\nELEMENT TEXT: {1}\nException: {2}\nTraceback: {3}".format(element.tag_name, element.text, str(e), str(sys.exc_info())))
			return ''

	@staticmethod
	def is_abs(link):
		"""
		Check if a given link is absolute or not.
		"""
		try:
			test = bool('http' in urllib.parse.urlparse(link).scheme.lower())
			return test
		except TypeError:
			return bool('http' in link.lower())

	def make_abs(self, href):
		"""
		If href is not absolute, make it absolute and return the absolute link
		"""
		if not self.is_abs(href):
			absolute = urllib.parse.urljoin(self.url, href)
			return absolute
		return href



	def result_type(self, result_element):
		"""
		Given an element with an href, will request the link to check the type of _response returned.
		"""

		link = self.get_link_from_element(result_element)
		# MASK AUTOMATION
		headers = requests.utils.default_headers()
		headers.update({
		'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
		})
		resp = requests.get(link, headers)
		content_type = resp.headers["Content-Type"].split(';',1)[0].split('/', 1)[-1]
		return content_type

	def move_to(self, selector=False, click=False, xpath=False, new_window=False):
		"""
		Move to the element matched by selector or passed as argument.

		Parameters
		----------
		selector: str
			Any valid CSS selector
		click: bool
			Whether or not to click the element after hovering
			defaults to False
			:param xpath:
		"""
		action = webdriver.ActionChains(self.driver)
		if isinstance(selector, WebElement):
			try:
				elem = selector
				action.move_to_element(elem)
				action.perform()
				if new_window:
					self.open_in_new_tab(elem)
					return
				if click:
					action.click(elem)
					action.perform()
			except WebDriverException as e:
				print("move_to isn't supported with this browser driver.\nTraceback: {0}".format(sys.exc_info()))

		elif isinstance(selector, str):
			if xpath:
				try:
					elem = self.driver.find_element_by_xpath(xpath)

					action.move_to_element(elem)
					if click:
						action.click(elem)

					action.perform()
				except WebDriverException as e:
					print("move_to isn't supported with this browser driver.\nTraceback:{0}".format(sys.exc_info()))
			elif selector:
				try:
					elem = self.get_element(selector)
					action = webdriver.ActionChains(self.driver)
					action.move_to_element(elem)
					if click:
						action.click(elem)
					action.perform()
				except WebDriverException:
					logging.exception("move_to isn't supported with this browser driver.\nTraceback:{0}".format(sys.exc_info()))
		else:
			raise BaseException("Selector Not Found")

	def hover(self, selector, click=False):
		"""
		Hover over the element matched by selector and optionally click it.

		Parameters
		----------
		selector: str
			Any valid CSS selector
		click: bool
			Whether or not to click the element after hovering
			defaults to False
		"""
		try:
			self.move_to(selector, click)
		except WebDriverException:
			logging.exception("hover isn't supported with this browser driver.\nTraceback:{0}".format(sys.exc_info()))

	def _selector_or_elements(self, what):
		if isinstance(what, WebElement) or isinstance(what, list):
			return what
		else:
			elements = self.get_elements(what)
			len_elements = len(elements)
			if len_elements > 1:
				return elements
			elif len_elements == 1:
				return elements[0]
			else:
				return None

	def get_link_elements_by_partial_text(self, text):
		links = []
		_links = self.find_elements('a')
		for link in _links:
			if re.search(text, link.text, flags=re.I):
				links.append(link)
		return links

	def get_links(self, what='a[href]'):
		"""
		Gets links by CSS selector or WebElement list.

		Parameters
		----------
		what: str or list of WebElement
			A CSS selector to search for. This can be any valid CSS selector.
			-- or --
			A list of previously selected WebElement instances.

		Returns
		-------
		list of str
			A list of URL strings.

		"""
		elements = self._selector_or_elements(what)
		urls = []
		for elem in elements:
			href = elem.get_attribute('href')
			#if href:
			urls.append(href)
		return urls

	def get_elements(self, selector):
		"""
		Gets elements by CSS selector.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		Returns
		-------
		list of selenium.webdriver.remote.webelement.WebElement
			A list of selenium element objects.

		"""
		elements = self.find_elements(selector)

		# Extend all the elements
		if elements:
			elements = [WebRunnerElement(elem._parent, elem._id, elem._w3c) for elem in elements]
			return elements
		else:
			raise NoSuchElementException

	def get_elements_by_xpath(self, xpath):
		"""
		Gets elements by CSS selector.

		Parameters
		----------
		selector: str A CSS selector to search for. This can be any valid CSS selector.
		Returns
		-------
		list of selenium.webdriver.remote.webelement.WebElement
		A list of selenium element objects.
		"""

		elements = self.find_elements_by_xpath(xpath)

		# Extend all the elements
		if elements:
			_elements = [WebRunnerElement(elem._parent, elem._id, elem._w3c) for elem in elements]
			return _elements
		else:
			raise NoSuchElementException

	def get_element(self, selector):
		"""
		Gets element by CSS selector.

		Parameters
		----------
		selector: str
			A CSS/XPATH selector to search for. This can be any valid CSS/XPATH selector.

		Returns
		-------
		selenium.webdriver.remote.webelement.WebElement
			A selenium element object.

		"""
		elem = self.find_element(selector)
		if elem:
			return WebRunnerElement(elem._parent, elem._id, elem._w3c)
		else:
			raise NoSuchElementException

	def get_element_by_xpath(self, xpath):
		"""
		Gets element by CSS selector.

		Parameters
		----------
		selector: str
		A CSS/XPATH selector to search for. This can be any valid CSS/XPATH selector.

		Returns
		-------
		selenium.webdriver.remote.webelement.WebElement
		A selenium element object.
		"""
		elem = self.find_element_by_xpath(xpath)
		if elem:
			return WebRunnerElement(elem._parent, elem._id, elem._w3c)
		else:
			raise NoSuchElementException

	def get_text(self, selector=None, elem=None):
		"""
		Gets text from inside of an element by CSS selector.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		Returns
		-------
		str
			The text from inside of a selenium element object.
			:param elem:

		"""
		if selector and not elem:
			elem = self.get_element(selector)

		return elem.text

	def get_texts(self, selector):
		"""
		Gets all the text from all elements found by CSS selector.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		Returns
		-------
		list of str
			A list of text strings from inside of all found selenium element objects.

		"""
		elements = self.get_elements(selector)
		texts = [e.text for e in elements]
		return texts

	def get_value(self, selector):
		"""
		Gets value of an element by CSS selector.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		Returns
		-------
		str
			The value of a selenium element object.

		"""
		elem = self.get_element(selector)
		if self.driver == 'Gecko':
			# Let's do this the stupid way because Mozilla thinks geckodriver is so incredibly amazing.
			tag_name = elem.tag_name
			if tag_name == 'select':
				select = Select(elem)
				return select.all_selected_options[0].get_attribute('value')
			else:
				return elem.get_attribute('value')
		else:
			return elem.get_attribute('value')

	def send_key(self, selector, key, wait_for='presence', **kwargs):
		"""
		Sets value of an element by CSS selector.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		key: str
			A str representation of a special key to send.

			Some available keys and their string representations:
			::
				'ADD' = u'\ue025'
				'ALT' = u'\ue00a'
				'ARROW_DOWN' = u'\ue015'
				'ARROW_LEFT' = u'\ue012'
				'ARROW_RIGHT' = u'\ue014'
				'ARROW_UP' = u'\ue013'
				'BACKSPACE' = u'\ue003'
				'BACK_SPACE' = u'\ue003'
				'CANCEL' = u'\ue001'
				'CLEAR' = u'\ue005'
				'COMMAND' = u'\ue03d'
				'CONTROL' = u'\ue009'
				'DECIMAL' = u'\ue028'
				'DELETE' = u'\ue017'
				'DIVIDE' = u'\ue029'
				'DOWN' = u'\ue015'
				'END' = u'\ue010'
				'ENTER' = u'\ue007'
				'EQUALS' = u'\ue019'
				'ESCAPE' = u'\ue00c'
				'F1' = u'\ue031'
				'F10' = u'\ue03a'
				'F11' = u'\ue03b'
				'F12' = u'\ue03c'
				'F2' = u'\ue032'
				'F3' = u'\ue033'
				'F4' = u'\ue034'
				'F5' = u'\ue035'
				'F6' = u'\ue036'
				'F7' = u'\ue037'
				'F8' = u'\ue038'
				'F9' = u'\ue039'
				'HELP' = u'\ue002'
				'HOME' = u'\ue011'
				'INSERT' = u'\ue016'
				'LEFT' = u'\ue012'
				'LEFT_ALT' = u'\ue00a'
				'LEFT_CONTROL' = u'\ue009'
				'LEFT_SHIFT' = u'\ue008'
				'META' = u'\ue03d'
				'MULTIPLY' = u'\ue024'
				'NULL' = u'\ue000'
				'NUMPAD0' = u'\ue01a'
				'NUMPAD1' = u'\ue01b'
				'NUMPAD2' = u'\ue01c'
				'NUMPAD3' = u'\ue01d'
				'NUMPAD4' = u'\ue01e'
				'NUMPAD5' = u'\ue01f'
				'NUMPAD6' = u'\ue020'
				'NUMPAD7' = u'\ue021'
				'NUMPAD8' = u'\ue022'
				'NUMPAD9' = u'\ue023'
				'PAGE_DOWN' = u'\ue00f'
				'PAGE_UP' = u'\ue00e'
				'PAUSE' = u'\ue00b'
				'RETURN' = u'\ue006'
				'RIGHT' = u'\ue014'
				'SEMICOLON' = u'\ue018'
				'SEPARATOR' = u'\ue026'
				'SHIFT' = u'\ue008'
				'SPACE' = u'\ue00d'
				'SUBTRACT' = u'\ue027'
				'TAB' = u'\ue004'
				'UP' = u'\ue013'

		kwargs:
			passed on to wait_for_*
		"""
		self._wait_for_presence_or_visible(selector, wait_for, **kwargs)

		elem = self.get_element(selector)

		if hasattr(Keys, key.upper()):
			elem.send_keys(getattr(Keys, key.upper()))

	def drag_and_drop(self, from_selector, to_selector):
		"""
		Drags an element into another.

		Parameters
		----------
		from_selector: str
			A CSS selector to search for. This can be any valid CSS selector.
			Element to be dragged.

		to_selector: str
			A CSS selector to search for. This can be any valid CSS selector.
			Target element to be dragged into.

		"""

		from_element = self.get_element(from_selector)
		to_element = self.get_element(to_selector)
		ActionChains(self.driver).drag_and_drop(from_element, to_element).perform()

	def drag_and_drop_xpath(self, from_xpath, to_xpath):
		"""
		Drags an element into another.

		Parameters
		----------
		from_selector: str
			A CSS selector to search for. This can be any valid CSS selector.
			Element to be dragged.

		to_selector: str
			A CSS selector to search for. This can be any valid CSS selector.
			Target element to be dragged into.
			:param from_xpath:

		"""

		from_element = self.get_element_by_xpath(from_xpath)
		to_element = self.get_element_by_xpath(to_xpath)
		ActionChains(self.driver).drag_and_drop(from_element, to_element).perform()

	def set_values(self, values, clear=True, blur=True, **kwargs):
		"""
		Sets values of elements by CSS selectors.

		Parameters
		----------
		values: list of list or dict or list of dict
			A list of lists where index 0 is a selector string and 1 is a value.

		clear: bool
			Whether or not we should clear the element's value first.
			If false, value will be appended to the current value of the element.

		blur: bool
			Whether or not we should blur the element after setting the value.
			Defaults to True

		kwargs:
			passed on to wait_for_visible

		"""
		if isinstance(values, dict):
			# If the entire var is a dict, just use all the key/value pairs
			for key in values:
				self.set_value(key, values[key], clear=clear, blur=blur, **kwargs)
		else:
			# If not a dict it's a list/tuple of things (dicts or lists / tuples)
			for row in values:
				if isinstance(row, dict):
					# If it is a dict use it's key / value pairs.
					for key in row:
						self.set_value(key, row[key], clear=clear, blur=blur, **kwargs)
				else:
					# Otherwise just use the list / tuple positions
					self.set_value(row[0], row[1], clear=clear, blur=blur, **kwargs)

	def wait(self, seconds=500):
		"""
		Sleeps for some amount of time.

		Parameters
		----------

		seconds: int
			Seconds to sleep for.

		"""
		# You probably shouldn't use this for anything
		# real in tests. I use this for pausing execution.
		sleep(seconds)

	def set_value(self, selector, value, clear=True, blur=True, **kwargs):
		"""
		Sets value of an element by CSS selector.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		value: str
			The value to set on the element matched by the selector.

		clear: bool
			Whether or not we should clear the element's value first.
			If false, value will be appended to the current value of the element.

		blur: bool
			Whether or not we should blur the element after setting the value.
			Defaults to True

		kwargs:
			passed on to wait_for_visible

		"""
		typing = kwargs.get('typing', False)
		typing_speed = kwargs.get('typing_speed', 3)
		typing_max_delay = kwargs.get('typing_max_delay', .33)
		self.wait_for_visible(selector, **kwargs)

		elem = kwargs.get('elem')
		if not elem:
			elem = self.get_element(selector)

		if elem.tag_name == 'select':
			self.set_select_by_value(elem, value)
		else:
			if clear:
				self.clear(selector)
			if typing:
				for k in value:
					delay = random() / typing_speed
					if delay > typing_max_delay:
						delay = typing_max_delay
					sleep(delay)
					elem.send_keys(k)
			else:
				elem.send_keys(value)

			if self.driver == 'Gecko':
				# Thank you so much Mozilla. This is awesome to have to do.
				self.js("arguments[0].setAttribute('value', '{0}')".format(value), elem)

		if blur:
			elem.send_keys(Keys.TAB)

	def set_selectize(self, selector, value, text=None, clear=True, blur=False):
		"""
		Sets visible value of a selectize control based on the "selectized" element.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		value: str
			The value of the option to select.
			(Stored Value)

		text: str
			The visible value that the user sees.
			(Visible value, if different than the stored value)

		clear: bool
			Whether or not we should clear the selectize value first.
			Defaults to True

		blur: bool
			Whether or not we should blur the element after setting the value.
			This corresponds to the 'selectOnTab' selecize setting.
			Defaults to False
		"""
		selectize_control = '{0} + .selectize-control'.format(selector)
		selectize_input = '{0} input'.format(selectize_control)
		# Make sure the selectize control is active so the input is visible
		self.click(selectize_control)
		input_element = self.get_element(selectize_input)

		if clear:
			input_element.send_keys(Keys.BACK_SPACE)

		input_element.send_keys(text or value)

		# Wait for options to be rendered
		self.wait_for_visible('{0} .has-options'.format(selectize_control))

		if blur:
			input_element.send_keys(Keys.TAB)
		else:
			# Click the option for the given value
			self.click('{0} .option[data-value="{1}"]'.format(selectize_control, value))

	def clear(self, selector_or_xpath):
		"""
		Clears value of an element by CSS selector.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		"""
		if selector_or_xpath.startswith('//'):
			elem = self.get_element_by_xpath(selector_or_xpath)
		else:
			elem = self.get_element(selector_or_xpath)
		if elem:
			elem.clear()

	def current_url(self):
		"""
		Gets current URL of the browser object.

		Returns
		-------
		str
			The curent URL.

		"""
		return self.driver.current_url

	def go_to(self, address, new_tab=False):
		"""
		Go to a web address. (self.browser should be available, but not needed.)

		Parameters
		----------
		address: str
			The address (URL)

		"""
		self.url = address

		if not new_tab:
			self.driver.get(self.url)
		else:
			self.newtab(self.url)

	def count(self, selector):
		"""
		Counts the number of elements that match CSS/XPATH selector.

		Parameters
		----------
		selector: str
			A CSS/XPATH selector to search for. This can be any valid CSS/XPATH selector.

		Returns
		-------
		int: Number of matching elements.

		"""
		return len(self.get_elements(selector))

	def find_element(self, selector):
		"""
		Finds an element by CSS/XPATH selector.

		Parameters
		----------
		selector: str
			A CSS/XPATH selector to search for. This can be any valid CSS/XPATH selector.

		Returns
		-------
		selenium.webdriver.remote.webelement.WebElement or None
			Returns an element or nothing at all

		"""
		elem = None
		try:
			if selector.startswith('/'):

				elem = self.driver.find_element_by_xpath(selector)
			else:
				elem = self.driver.find_element_by_css_selector(selector)
		except NoSuchElementException:
			logging.exception("Element Not Found with Selector: {0}.\nTraceback:{1}".format(selector, sys.exc_info()))
		except StaleElementReferenceException:
			return self.find_element(selector)
		return elem

	def find_elements(self, selector):
		"""
		Finds elements by CSS/XPATH selector.

		Parameters
		----------
		selector: str
			A CSS/XPATH selector to search for. This can be any valid CSS/XPATH selector.

		Returns
		-------
		list of selenium.webdriver.remote.webelement.WebElement or list
			Returns a list of elements or empty list

		"""
		elems = []
		try:
			if selector.startswith('/'):
				elems = self.driver.find_elements_by_xpath(selector)
			else:
				elems = self.driver.find_elements_by_css_selector(selector)
		except NoSuchElementException:
			logging.exception("Element Not Found with Selector: {0}.\nTraceback:{1}".format(selector, sys.exc_info()))
		except StaleElementReferenceException:
			return self.find_elements(selector)
		return elems

	def find_elements_by_text(self, text):

		try:
			elems = self.driver.find_elements_by_xpath('//*[contains(text(), "{0}")]'.format(text))
		except NoSuchElementException:
			logging.exception("Element Not Found with Text: {0}.\nTraceback:{1}".format(text,sys.exc_info()))
		return elems

	def find_elements_by_xpath(self, xpath):

		try:
			elems = self.driver.find_elements_by_xpath(xpath)
		except NoSuchElementException:
			logging.exception("Element Not Found with XPATH: {0}.\nTraceback:{1}".format(xpath, sys.exc_info()))
			elems = None
		return elems


	def find_element_by_text(self, text):
		try:
			elem = self.driver.find_element_by_xpath('//*[contains(text(), "{0}")]'.format(text))
			return elem
		except NoSuchElementException:
			raise(NoSuchElementException)

	def find_element_by_xpath(self, xpath):
		try:
			elem = self.driver.find_element_by_xpath(xpath)
		except NoSuchElementException:
			elem = None
			logging.exception("Element Not Found with XPATH: {0}.\nTraceback:{1}".format(xpath, sys.exc_info()))
		return elem

	def add_cookie(self, cookie_dict):
		"""
		Adds a cookie from a dict.

		Parameters
		----------
		cookie_dict: dict
			A dict with the cookie information
		"""
		self.driver.add_cookie(cookie_dict)

	def delete_cookie(self, cookie_name):
		"""
		Adds a cookie from a dict.

		Parameters
		----------
		cookie_name: str
			The name of the cookie to delete
		"""
		self.driver.delete_cookie(cookie_name)

	def delete_all_cookies(self):
		"""
		Deletes all cookies

		"""
		self.driver.delete_all_cookies()

	def refresh(self):
		"""
		Refreshes the page using the selenium binding.
		"""
		self.driver.refresh()

	def refresh_page(self, refresh_method="url"):
		"""
		Refreshes the current page using either a URL redirect or JavaScript

		Parameters
		----------
		method: str
			The method used to refresh the page.
			Defaults to "url" which navigates to the current_url

		"""
		if refresh_method == "url":
			self.driver.get(self.driver.current_url)
		elif refresh_method == "js":
			self.js('window.location.reload(true);')

	def js(self, js_str, *args):
		"""
		Run some JavaScript and return the result.

		Parameters
		----------
		js_str: str
			A string containing some valid JavaScript to be ran on the page.

		Returns
		-------
		str or bool or list or dict
			Returns the result of the JS evaluation.

		"""
		return self.driver.execute_script(js_str, *args)

	def _find_elements(self, row):
		"""
		Find elements using a name, css selector, class, xpath, or id.

		Parameters
		----------
		row: dict
			A dict where the key is the search method
			and the value is what is passed to Selenium

		Returns
		-------
		list of selenium.webdriver.remote.webelement.WebElement
			A list of selenium element objects.

		"""
		elems = []
		try:
			if 'name' in row:
				elems = self.driver.find_elements_by_name(row['name'])
			elif 'css' in row:
				elems = self.driver.find_elements_by_css_selector(row['css'])
			elif 'class' in row:
				elems = self.driver.find_elements_by_class_name(row['class'])
			elif 'xpath' in row:
				elems = self.driver.find_elements_by_xpath(row['xpath'])
			else:
				elems = self.driver.find_elements_by_id(row['id'])
		except NoSuchElementException:

			pass
		finally:
			return elems

	def save_page_source(self, path='/tmp/selenium-page-source.html'):
		"""
		Saves the raw page html in it's current district. Takes a path as a parameter.

		Parameters
		----------
		path: str
			Defaults to: /tmp/selenium-page-source.html

		"""
		page_source = self.driver.page_source

		out_file = open(path, 'w')
		out_file.write(page_source.encode('utf8'))
		out_file.close()

	def screenshot(self, path=None):
		"""
		Saves a screenshot. Takes a path as a parameter.

		Parameters
		----------
		path: str
			Defaults to: /tmp/selenium-screenshot.png

		"""
		if not path:
			path = '/tmp/selenium-screenshot.png'

		# if isinstance(self.browser, webdriver.remote.webdriver.WebDriver):
		#     # Get base64 screenshot from the remote.
		#     base64_data = self.browser.get_screenshot_as_base64()
		#     ss_data = base64.decodestring(base64_data)
		#     with open(path, 'w') as f:
		#         f.write(ss_data)
		#         f.close()
		# else:
		if self.driver == 'chrome-headless':
			print("You are running Chrome in headless mode. Screenshots will be blank.")
		else:
			self.driver.save_screenshot(path)

	def fill(self, form_dict):
		"""
		Fills a form using Selenium. This helper will save a lot of time
		and effort because working with form data can be tricky and gross.

		Parameters
		----------
		form_dict: dict
			Takes in a dict where the keys are CSS selectors
			and the values are what will be applied to them.

		"""
		form_list = []
		for key in form_dict:
			form_list.append({'css': key, 'value': form_dict[key]})
		self.fill_form(form_list)

	def fill_form(self, form_list):
		"""
		This helper can be used directly but it is much easier
		to use the "credentials" method instead.

		Parameters
		----------
		form_list: list of dict
			A list of dictionaries where the key is the search method
			and the value is what is passed to Selenium
		clear: bool
			True/False value indicating whether or not to clear out
			the input currently in any text inputs.

		"""
		for row in form_list:
			elems = self._find_elements(row)
			# If the length is greater than 1, it should be a checkbox or radio.
			if len(elems) > 1:
				# Get the element type we are dealing with.
				tag_name = elems[0].tag_name
				tag_type = elems[0].get_attribute('type')

				if tag_type == 'radio':
					for elem in elems:
						tag_value = elem.get_attribute('value')
						if tag_value == row['value']:
							# Select the right radio button
							elem.click()

				elif tag_type == 'checkbox':
					# We need to handle checkboxes differently than radio buttons.
					# (More than one can be checked so we must handle that.)
					for elem in elems:
						tag_value = elem.get_attribute('value')
						if not isinstance(row['value'], list):
							# Put single items in a list so we can loop.
							row['value'] = [row['value']]

						for value in row['value']:
							# Loop over all the values and check the ones we want.
							# Un-check the ones we don't want.
							if tag_value == value:
								if not elem.is_selected():
									elem.click()
							else:
								if elem.is_selected() and tag_value not in row['value']:
									elem.click()

			elif len(elems) == 1:
				# Handle every other form element type since they are much
				# more straightforward.
				elem = elems[0]
				tag_name = elem.tag_name

				if tag_name in ('input', 'textarea') or tag_name == 'select':
					# File upload needs a path to a file.
					self.set_value('', row['value'], elem=elem)


			else:
				print("{0} Element not found.".format(row))

	# Custom asynchronous wait helpers
	def _wait_for(self, wait_function, **kwargs):
		"""
		Wrapper to handle the boilerplate involved with a custom wait.

		Parameters
		----------
		wait_function: func
			This can be a builtin selenium wait_for class,
			a special wait_for class that implements the __call__ method,
			or a lambda function
		timeout: int
			The number of seconds to wait for the given condition
			before throwing an error.
			Overrides WebRunner.timeout

		"""
		try:
			wait = WebDriverWait(self.driver, kwargs.get('timeout') or self.timeout)
			wait.until(wait_function)
		except TimeoutException:
			if self.driver == 'Gecko':
				logging.exception("Geckodriver can't use the text_to_be_present_in_element_value wait for some reason.\nTraceback:{0}".format(sys.exc_info()))
			else:
				raise

	def wait_for_alert(self, **kwargs):
		"""
		Shortcut for waiting for alert. If it not ends with exception, it
		returns that alert.
		"""
		self._wait_for(self.alert_present, **kwargs)

	def wait_for_presence(self, selector='', **kwargs):
		"""
		Wait for an element to be present. (Does not need to be visible.)

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		kwargs:
			Passed on to _wait_for

		"""
		if selector.startswith('/'):
			by = By.XPATH
		else:
			by = By.CSS_SELECTOR
		self._wait_for(ec.presence_of_element_located((by, selector)) or
					   ec.presence_of_all_elements_located((by, selector)),
					   **kwargs)

	def wait_for_clickable(self, selector='', **kwargs):
		"""
		Wait for an element to be clickable.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		kwargs:
			Passed on to _wait_for

		"""

		if selector.startswith('/'):
			by = By.XPATH
		else:
			by = By.CSS_SELECTOR
		self._wait_for(ec.element_to_be_clickable((by, selector)), **kwargs)

	def wait_for_ko(self, selector='', **kwargs):
		"""
		Wait for an element to be bound by Knockout JS.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.
		kwargs:
			Passed on to _wait_for
		"""
		self.wait_for_presence(selector)

		ieo_func = 'function __isEmptyObject(obj){var name;for(name in obj){return false;}return true;}'
		js_check_bound = "{0}return !__isEmptyObject(ko.dataFor(document.querySelectorAll('{1}')[0]));".format(ieo_func, selector)
		self.wait_for_js(js_check_bound, **kwargs)

	def wait_for_url(self, url='', **kwargs):
		"""
		Wait for the current url to match the given url.

		Parameters
		----------
		url: str
			A regular expression to match against the current url
		kwargs:
			Passed on to _wait_for

		"""
		self._wait_for(expect_url_match(url), **kwargs)

	def wait_for_visible(self, selector='', **kwargs):
		"""
		Wait for an element to be visible.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		kwargs:
			Passed on to _wait_for

		"""
		if selector.startswith('/'):
			by = By.XPATH
		else:
			by = By.CSS_SELECTOR
		self._wait_for(ec.visibility_of_element_located((by, selector)),
					   **kwargs)

	def _wait_for_presence_or_visible(self, selector, wait_for, **kwargs):
		"""
		Wrapper around wait_for_presence and wait_for_visible that takes a
		string to decide which one to use.
		"""
		if wait_for == 'presence':
			self.wait_for_presence(selector, **kwargs)
		elif wait_for == 'visible':
			self.wait_for_visible(selector, **kwargs)

	def wait_for_invisible(self, selector='', **kwargs):
		"""
		Wait for an element to be invisible.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		kwargs:
			Passed on to _wait_for

		"""
		if selector.startswith('/'):
			by = By.XPATH
		else:
			by = By.CSS_SELECTOR
		self._wait_for(ec.invisibility_of_element_located((by, selector)),
					   **kwargs)

	def wait_for_all_invisible(self, selector='', **kwargs):
		"""
		Wait for all elements that match selector to be invisible.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		kwargs:
			Passed on to _wait_for

		"""
		all_matches = self.get_elements(selector)

		for match in all_matches:
			self._wait_for(invisibility_of(match), **kwargs)

	def wait_for_js(self, js_script, **kwargs):
		"""
		Wait for the given JS to return true.

		Parameters
		----------
		js_script: str
			valid JS that will run in the page dom

		kwargs:
			passed on to _wait_for

		"""
		self._wait_for(lambda driver: bool(driver.execute_script(js_script)),
					   **kwargs)

	def wait_for_text_on_page(self, text):
		self._wait_for(lambda s: text in s.page_source)

	def wait_for_text(self, selector='', text='', **kwargs):
		"""
		Wait for an element to contain a specific string.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		text: str
			The string to look for. This must be precise.
			(Case, punctuation, UTF characters... etc.)
		kwargs:
			Passed on to _wait_for

		"""
		if selector.startswith('/'):
			by = By.XPATH
		else:
			by = By.CSS_SELECTOR
		self._wait_for(ec.text_to_be_present_in_element((by, selector),
														text), **kwargs)

	def help(self):
		methods = [x for x, y in Browser.__dict__.items() if type(y) == FunctionType and not x.startswith('_')]
		methods.sort()
		for method in methods:
			print(method)

	def wait_for_text_in_value(self, selector='', text='', **kwargs):
		"""
		Wait for an element's value to contain a specific string.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		text: str
			The string to look for. This must be precise.
			(Case, punctuation, UTF characters... etc.)
		kwargs:
			Passed on to _wait_for

		"""
		if selector.startswith('/'):
			by = By.XPATH
		else:
			by = By.CSS_SELECTOR
		self._wait_for(ec.text_to_be_present_in_element_value((by, selector),
															  text), **kwargs)

	def wait_for_selected(self, selector='', selected=True, **kwargs):
		"""
		Wait for an element (checkbox/radio) to be selected.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		selected: bool
			Whether or not the element should be selected. Default True

		kwargs:
			Passed on to _wait_for

		"""
		if selector.startswith('/'):
			by = By.XPATH
		else:
			by = By.CSS_SELECTOR
		self._wait_for(ec.element_located_selection_state_to_be((by, selector),
																selected), **kwargs)

	def wait_for_title(self, title, **kwargs):
		"""
		Wait for the page title to match given title.

		Parameters
		----------
		title: str
			The page title to wait for

		kwargs:
			Passed on to _wait_for

		"""
		self._wait_for(ec.title_is(title), **kwargs)

	def wait_for_value(self, selector='', value='', **kwargs):
		"""
		Wait for an element to contain a specific string.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		value: str
			The string to look for. This must be precise.
			(Case, punctuation, UTF characters... etc.)
		kwargs:
			Passed on to _wait_for

		"""
		if selector.startswith('/'):
			by = By.XPATH
		else:
			by = By.CSS_SELECTOR
		self._wait_for(ec.text_to_be_present_in_element_value((by, selector),
															  value), **kwargs)

	def wait_for_opacity(self, selector, opacity, **kwargs):
		"""
		Wait for an element to reach a specific opacity.

		Parameters
		----------
		selector: str
			A CSS selector to search for. This can be any valid CSS selector.

		opacity: float
			The opacity to wait for.

		kwargs:
			Passed on to _wait_for

		"""

		def _wait_for_opacity(self, browser):
			return str(self.get_element(selector).value_of_css_property('opacity')) == str(opacity)

		self._wait_for(partial(_wait_for_opacity, self), **kwargs)

	@contextmanager
	def wait_for_page_load(self, timeout: int = 30) -> int:
		"""
		Logic
			Enter Context
			get current page html
			yield control back to navigator,
			once move is made,
			wait till old page is stale then get the element of the new page
			Wait till new page is visible
		:param timeout:
		:return:
		"""
		#	Action to take upon entering context
		old_page = self.driver.find_element_by_tag_name('html')
		#	Get the html tag of the current page. Turn control over to the context block and execute any code there.
		yield
		#	Action to take before exiting context.
		try:
			#	Wait until the old html goes stale, which signifies that a new one is loaded.

			WebDriverWait(self.driver, timeout).until(ec.staleness_of(old_page))
			new_page = self.driver.find_element_by_tag_name('html')
			WebDriverWait(self.driver, timeout).until(ec.visibility_of(new_page))
		except UnexpectedAlertPresentException:
			self.accept_alert()
			new_page = self.driver.find_element_by_tag_name('body')
			#	Wait until the old html goes stale, which signifies that a new one is loaded.
			WebDriverWait(self.driver, timeout).until(ec.staleness_of(old_page) and ec.visibility_of(new_page))

	def switch_to_window(self, window_name=None, title=None, url=None):
		"""
		Switch to window by name, title, or url.

		Parameters
		----------
		window_name: str
			The name of the window to switch to.

		title: str
			The title of the window you wish to switch to.

		url: str
			URL of the window you want to switch to.

		"""
		if window_name:
			self.driver.switch_to.window(window_name)
			return

		else:
			for window_handle in self.driver.window_handles:
				self.driver.switch_to.window(window_handle)

				if title and self.driver.title == title:
					return

				if url and self.driver.current_url == url:
					return

		raise NoSuchWindowException('Window not found: {}, {}, {}'.format(window_name, title, url))

	def close_window(self, window_name=None, title=None, url=None):
		"""
		Close window by name, title, or url.

		Parameters
		----------
		window_name: str
			The name of the window to switch to.

		title: str
			The title of the window you wish to switch to.

		url: str
			URL of the window you want to switch to.

		"""
		if window_name and title and url:
			self.switch_to_window(window_name, title, url)
			self.driver.close()
		else:
			original_window = self.driver.window_handles[0] # Get the original window
			self.driver.close() # Close the current window first before switching to the original window
			self.driver.switch_to.window(original_window)
			if self.driver.current_window_handle == original_window:
				return
			else:
				self.wait(10)
		

	def close_all_other_windows(self):
		"""
		Closes all windows except for the currently active one.
		"""
		main_window_handle = self.driver.current_window_handle
		for window_handle in self.driver.window_handles:
			if window_handle == main_window_handle:
				continue

			self.switch_to_window(window_handle)
			self.driver.close()

		self.switch_to_window(main_window_handle)

	def accept_alert(self, ignore_exception=False):
		"""
		Closes (accepts) any alert that is present. Raises an exception if no alert is found.

		Parameters
		----------

		ignore_exception: bool
			Does not throw an exception if an alert is not present.

		"""
		try:
			self.close_alert(action='accept', ignore_exception=ignore_exception)
		except NoAlertPresentException as e:
			print(str(e))
			pass


	def dismiss_alert(self, ignore_exception=False):
		"""
		Closes (cancels) any alert that is present. Raises an exception if no alert is found.

		Parameters
		----------

		ignore_exception: bool
			Does not throw an exception if an alert is not present.

		"""
		self.close_alert(action='dismiss', ignore_exception=ignore_exception)

	def close_alert(self, action='accept', ignore_exception=False):
		"""
		Closes any alert that is present. Raises an exception if no alert is found.

		Parameters
		----------

		ignore_exception: bool
			Does not throw an exception if an alert is not present.

		"""
		try:
			alert = self.get_alert()
			if action == 'dismiss':
				alert.dismiss()
			else:
				alert.accept()

		except NoAlertPresentException:
			if not ignore_exception:
				raise

	def get_alert(self):
		"""
		Returns instance of :py:obj:`~selenium.webdriver.common.alert.Alert`.
		"""
		return Alert(self.driver)

	def alert_present(self):
		"""
		Checks to see if an alert is present.
		"""

		alert = Alert(self.driver)
		try:
			alert.text
			return True

		except NoAlertPresentException:

			return False

	def dialog_present(self):
		"""
				Checks to see if a dialog box is present.
				"""
		try:
			dialog = self.wait_for_presence('aside[role="dialog"]')
			return True
		except TimeoutException:
			return False

	def dismiss_dialog(self):
		self.find_element('aside[role="dialog"] input[type="submit"]').click()
	

	def close(self):
		self.driver.close()

class WebRunnerElement(WebElement):
	""" Checks for a known element to be invisible.
		Much like the builtin visibility_of:
		https://github.com/SeleniumHQ/selenium/search?utf8=%E2%9C%93&q=visibility_of
	"""

	def has_class(self, name):
		return name in self.classes



	@property
	def classes(self):
		_classes = self.get_attribute('class') or []
		if _classes:
			_classes = _classes.split(' ')

		return _classes


class expect_url_match(object):
	"""Checks for the current url to match. """

	def __init__(self, url_check):
		self.url_check = url_check

	def __call__(self, driver):
		return re.search(self.url_check, driver.current_url)



class invisibility_of(object):
	""" Checks for a known element to be invisible.
		Much like the builtin visibility_of:
		https://github.com/SeleniumHQ/selenium/search?utf8=%E2%9C%93&q=visibility_of
	"""

	def __init__(self, element):
		self.element = element

	def __call__(self, driver):
		try:
			return (not self.element.is_displayed())
		except ec.StaleElementReferenceException:
			# If the element reference is no longer valid,
			# it was likely removed from the dom and is no longer visible
			return True


class Login(Browser):
	
	@classmethod
	def credentials(cls, username, password):
		cls.username = username
		cls.password = password
	
	def password_field(self):
		try:
			self._password_field = self.find_element('input[id*="password"]')
		except NoSuchElementException as e:
			raise BaseException("Cannot Locate Password Field\nTraceback Error:{0}".format(str(e)))
		return self._password_field
	
	def username_field(self):
		try:
			self._username_field = self.find_element("input[id*='user']")
		except NoSuchElementException as e:
			raise BaseException("Cannot Locate Username Field\nTraceback Error:{0}".format(str(e)))
		return self._username_field
	
	def enter_username(self):
		user_field_element = self.username_field()
		# Step 1: Click on username field
		# self.actions.move_to_element(user_field_element)
		# self.actions.click()
		# self.actions.perform()
		# self.actions.reset_actions()
		# Step 2: Enter username
		user_field_element.send_keys(str(self.username))
	
	def enter_password(self):
		pw_field_element = self.password_field()
		# Step 1: Click on password field
		self.actions.move_to_element(pw_field_element)
		self.actions.click()
		self.actions.perform()
		self.actions.reset_actions()
		
		# Step 2: Enter Password
		pw_field_element.send_keys(str(self.password))
	
	def submit(self):
		sbmt = self.sbmt_button()
		self.actions.move_to_element(sbmt)
		self.actions.click()
		self.actions.perform()
		self.actions.reset_actions
	
	def sbmt_button(self):
		try:
			self._submit_button = self.find_element("[id*=Sbmt]")
		except NoSuchElementException:
			raise BaseException("Cannot Locate Submit Button\nTraceback Error:{0}".format(str(e)))
		return self._submit_button
	
	def execute(self):
		self.enter_username()
		self.enter_password()
		self.submit()
	
	def sign_in(self, username, password):
		self.credentials(username, password)
		self.execute()