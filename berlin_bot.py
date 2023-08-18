import time
import os
import logging
from platform import system

import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

Target="Study"

Visa_Extend=2
Visa_Class=Visa_Extend

# Study
study_type=dict(
    Language_Course="SERVICEWAHL_DE479-0-2-3-324289",
    Study="SERVICEWAHL_DE479-0-2-3-305244",
)

# Work
work_type=dict(
    Acadamic_Graduate="SERVICEWAHL_DE479-0-2-1-329328",
    Find_Job="SERVICEWAHL_DE479-0-2-1-324661",
    Blue_Card="SERVICEWAHL_DE479-0-2-1-324659",
)

visa_class_2_map=dict(
    study_type=1,
    work_type=3,
)

Visa_Class_2 = None

if Target == "Study":
    Visa_Class_2=visa_class_2_map["study_type"]
elif Target == "Work":
    Visa_Class_2=visa_class_2_map["work_type"]


system = system()

default_time_sleep = 2
max_time_resubmit = 60 * 15

sound_file = "./alarm.wav"

logging.basicConfig(
    format='%(asctime)s\t%(levelname)s\t%(message)s',
    level=logging.INFO,
)

class WebDriver:
    def __init__(self):
        self._driver: webdriver.Chrome

    def __enter__(self) -> webdriver.Chrome:
        logging.info("Open browser")

        # some stuff that prevents us from being locked out
        options = webdriver.ChromeOptions() 
        options.add_argument('--disable-blink-features=AutomationControlled')
        self._driver = webdriver.Chrome(os.path.join(os.getcwd(), "chromedriver"), options=options)
        self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        self._driver.quit()

class BerlinBot:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message = """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte"""
        self.start_time = time.time()

    def get_wait_time(self, init:list = [10, 20]):
        options = range(init[0], init[1], 1)
        chose_time = random.choice(options)
        return chose_time


    def clickPATH(self, path: str):
        time.sleep(default_time_sleep)
        try:
            WebDriverWait(self.driver, self.get_wait_time()).until(EC.element_to_be_clickable((By.XPATH, path)))
            self.driver.find_element(By.XPATH, path).click()
        except:
            self.clickPATH(path)

    
    def clickID(self, id: str):
        time.sleep(default_time_sleep)
        try:
            WebDriverWait(self.driver, self.get_wait_time()).until(EC.element_to_be_clickable((By.ID, id)))
            self.driver.find_element(By.ID, id).click()
        except:
            time.sleep(3)
            self.clickID(id)

    def select(self, id: str, text: str):
        time.sleep(default_time_sleep)
        try:
            element = self.driver.find_element(By.ID, id)   
            s = Select(element)
            s.select_by_visible_text(text)
        except:
            time.sleep(3)
            self.select(id, text)


    def enter_start_page(self):
        logging.info("Visit start page")
        self.driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")

        self.clickPATH('//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    def tick_off_some_bullshit(self):
        logging.info("Ticking off agreement")

        self.clickPATH('//*[@id="xi-div-1"]/div[4]/label[2]/p')
        self.clickID('applicationForm:managedForm:proceed')
        time.sleep(5)

    def enter_form(self):
        
        # select china
        self.wait_for_text("Staatsangehörigkeit")
        self.select('xi-sel-400', 'China')

        # eine person
        self.wait_for_text("Anzahl der Personen")
        self.select('xi-sel-422', 'eine Person')

        # no family
        self.wait_for_text("Leben Sie in Berlin zusammen mit einem Familienangehörigen (z.B. Ehepartner, Kind)")
        self.select('xi-sel-427', 'nein')

        # extend stay
        self.clickPATH(f'//*[@id="xi-div-30"]/div[{Visa_Class}]/label/p')

        # click employment
        self.clickPATH(f'//*[@id="inner-479-0-2"]/div/div[{Visa_Class_2}]/label/p')

        # on blue card
        self.clickPATH('//*[@id="SERVICEWAHL_DE479-0-2-1-324659"]')

        logging.info("Fill out form")


    def submit(self):
        wait_time = self.get_wait_time([default_time_sleep, default_time_sleep*2])
        time.sleep(wait_time)
        try:
            self.clickPATH('//*[@id="applicationForm:managedForm:proceed"]')
        except:
            logging.info("Retry fill out form")
            self.enter_form()
    
    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            self._play_sound(self._sound_file, 10)
            time.sleep(5)

    def wait_for_text(self, text: str, timeout: int = 30):
        while text not in self.driver.page_source:
            time.sleep(default_time_sleep)
            timeout -= 1
            if timeout == 0:
                raise TimeoutException("Timeout while waiting for text")
        time.sleep(default_time_sleep)

    @staticmethod
    def run_once():
        with WebDriver() as driver:
            bot = BerlinBot(driver)
            bot.enter_start_page()
            bot.tick_off_some_bullshit()
            bot.enter_form()
            time.sleep(default_time_sleep)

            # retry submit
            while time.time() - bot.start_time < max_time_resubmit:
                bot.submit()
                if "Auswahl Uhrzeit" in bot.driver.page_source:
                    bot._success()
                elif bot._error_message in bot.driver.page_source:
                    logging.info("Retry submission")
                else:
                    pass

    @staticmethod
    def run_loop():
        # play sound to check if it works
        BerlinBot._play_sound(sound_file)
        while True:
            logging.info("One more round")
            BerlinBot.run_once()
            time.sleep(5)

    # stolen from https://github.com/JaDogg/pydoro/blob/develop/pydoro/pydoro_core/sound.py
    @staticmethod
    def _play_sound(sound, t = 0):
        logging.info("Play sound")

        from playsound import playsound
        playsound(sound_file)
        time.sleep(t)

if __name__ == "__main__":
    BerlinBot.run_loop()
