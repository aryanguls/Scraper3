from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def ensure_directory_exists(directory_path):
    os.makedirs(directory_path, exist_ok=True)

def download_audio(audio_url, save_path, file_name):
    response = requests.get(audio_url, stream=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_file_name = f"{file_name}_{timestamp}.mp3"
    full_path = os.path.join(save_path, unique_file_name)
    with open(full_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=128):
            f.write(chunk)
    print(f"Downloaded: {full_path}")
    return full_path

def append_metadata_to_json(metadata, metadata_file_path):
    try:
        with open(metadata_file_path, 'r+') as file:
            existing_metadata = json.load(file)
    except FileNotFoundError:
        existing_metadata = []
    except json.JSONDecodeError:
        existing_metadata = []

    existing_metadata.append(metadata)
    with open(metadata_file_path, 'w') as file:
        json.dump(existing_metadata, file, indent=4)

def get_element_text(element, selector):
    try:
        return element.find_element(By.CSS_SELECTOR, selector).text
    except NoSuchElementException:
        return ""

def scrape_and_download_audio(driver, base_url, save_path, number_of_files='ALL'):
    page_number = 1
    downloaded_files = 0
    metadata_file_path = "metadata.json"  # Main directory for metadata

    while True:
        driver.get(f"{base_url}&page={page_number}")
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.shared-item_cards-card_component__root")))
        audio_elements = driver.find_elements(By.CSS_SELECTOR, "div.shared-item_cards-card_component__root")

        if not audio_elements or (number_of_files.upper() != 'ALL' and downloaded_files >= int(number_of_files)):
            break

        for element in audio_elements:
            if number_of_files.upper() != 'ALL' and downloaded_files >= int(number_of_files):
                break

            audio_link = element.find_element(By.CSS_SELECTOR, "div.shared-audio_player_component__root[data-file]").get_attribute("data-file")
            name = get_element_text(element, "h3.shared-item_cards-item_name_component__root a")
            # Modification: Extract the href attribute for the link
            item_link = element.find_element(By.CSS_SELECTOR, "a.shared-item_cards-list-audio_card_component__itemLinkOverlay").get_attribute("href")

            saved_file_path = download_audio(audio_link, save_path, name.replace(" ", "_").replace("/", "_"))

            # Modification: Add the link to the metadata
            metadata = {
                "name": name,
                "audio_link": audio_link,
                "downloaded_file_path": saved_file_path,
                "link": item_link  # Include the link here
            }

            append_metadata_to_json(metadata, metadata_file_path)
            downloaded_files += 1

        page_number += 1


if __name__ == "__main__":
    user_input = input("Enter the number of audio files you want to download or type 'ALL' for all available files: ").strip()
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    
    base_url = "https://audiojungle.net/search?sort=rating#content"
    save_path = "./audio_files"
    ensure_directory_exists(save_path)
    
    scrape_and_download_audio(driver, base_url, save_path, user_input)
    driver.quit()
