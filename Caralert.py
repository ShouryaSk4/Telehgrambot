from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import re
import time
from pathlib import Path

import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')


# --- Cars to Watch: name + link ---
CAR_LINKS = [
    ("Corolla Altis CVT", "https://www.olx.in/en-in/gujarat_g2001154/cars_c84?filter=make_eq_toyota%2Cmodel_eq_toyota-corolla-altis%2Cpetrol_eq_petrol%2Ctransmission_eq_1%2Cyear_between_2014_to_2025"),
    ("Jetta Automatic", "https://www.olx.in/en-in/gujarat_g2001154/cars_c84?isSearchCall=false&filter=make_eq_volkswagen%2Cmodel_eq_volkswagen-jetta%2Cpetrol_eq_diesel%2Ctransmission_eq_1%2Cyear_between_2014_to_2025"),
    ("Jetta Manual", "https://www.olx.in/en-in/gujarat_g2001154/cars_c84?isSearchCall=true&filter=make_eq_volkswagen%2Cmodel_eq_volkswagen-jetta%2Cpetrol_eq_diesel%2Ctransmission_eq_2%2Cyear_between_2015_to_2025"),
    ("Octavia Manual", "https://www.olx.in/en-in/gujarat_g2001154/cars_c84?filter=make_eq_skoda%2Cmodel_eq_skoda-octavia%2Cpetrol_eq_petrol%2Ctransmission_eq_2%2Cyear_between_2014_to_2025&isSearchCall=false&sorting=asc-price"),
    ("Octavia Automatic", "https://www.olx.in/en-in/gujarat_g2001154/cars_c84?filter=make_eq_skoda%2Cmodel_eq_skoda-octavia%2Cpetrol_eq_petrol%2Ctransmission_eq_1%2Cyear_between_2014_to_2025&isSearchCall=false&sorting=asc-price"),
    ("Jeep Compass","https://www.olx.in/en-in/gujarat_g2001154/cars_c84?sorting=asc-price&filter=model_eq_jeep-compass")
]

# --- Thresholds ---
MAX_PRICE = 400000
MIN_YEAR = 2014

# --- Telegram Message ---
def send_telegram_alert(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': msg,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

# --- Start Browser ---
def start_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={Path(__file__).parent / 'chrome_profile'}")
    return webdriver.Chrome(options=options)

# --- Scrape One Car ---
BLOCKED_LINKS = {
    "https://www.olx.in/en-in/item/cars-c84-used-volkswagen-jetta-in-umiya-nagar-mundra-iid-1809228455"
}

# --- Scrape One Car ---
def scrape_car(driver, car_name, url):
    print(f"\n🚗 Checking {car_name}...")
    driver.get(url)
    time.sleep(11)

    ads = driver.find_elements(By.XPATH, '//li[contains(@data-aut-id, "itemBox")]')
    print(f"🔍 {len(ads)} listings found for {car_name}")

    found = False

    for ad in ads:
        try:
            title = ad.find_element(By.CSS_SELECTOR, '[data-aut-id="itemTitle"]').text.strip()
            price_text = ad.find_element(By.CSS_SELECTOR, '[data-aut-id="itemPrice"]').text.strip()
            year_km = ad.find_element(By.CSS_SELECTOR, '[data-aut-id="itemSubTitle"]').text.strip()
            location = ad.find_element(By.CSS_SELECTOR, '[data-aut-id="itemDetails"]').text.strip()
            link = ad.find_element(By.TAG_NAME, 'a').get_attribute('href')

            # 🔒 Skip blocked listings
            if link in BLOCKED_LINKS:
                print(f"⛔ Skipped blocked link: {link}")
                continue

            # Clean price
            price = int(re.sub(r"[^\d]", "", price_text))

            # Extract year (first 4 digits of subtitle)
            year_match = re.search(r'\b(20\d{2})\b', year_km)
            year = int(year_match.group(1)) if year_match else 0

            if price <= MAX_PRICE and year >= MIN_YEAR:
                msg = f"<b>🚘 {car_name} Found!</b>\n\n" \
                      f"<b>Title:</b> {title}\n" \
                      f"<b>Price:</b> ₹{price:,}\n" \
                      f"<b>Year & KM:</b> {year_km}\n" \
                      f"<b>Location:</b> {location}\n" \
                      f"<b>Link:</b> {link}"
                send_telegram_alert(msg)
                print("✅ Alert sent!")
                found = True

        except Exception as e:
            continue

    if not found:
        print(f"❌ No {car_name} found under ₹{MAX_PRICE:,} and year ≥ {MIN_YEAR}")
# --- Master Run Function ---
def run_all():
    driver = start_browser()
    for name, link in CAR_LINKS:
        scrape_car(driver, name, link)
    driver.quit()

# --- Entry Point ---
run_all()
