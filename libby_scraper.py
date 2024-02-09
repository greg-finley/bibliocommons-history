from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get("https://libbyapp.com/interview/welcome#doYouHaveACard")

# Find all elements on the page
all_elements = driver.find_elements(By.XPATH, "//*")

# Print the tag name and a snippet of text for each element
for element in all_elements:
    text_snippet = element.text[:30]  # Get the first 30 characters of text
    print(f"Tag: {element.tag_name}, Text snippet: '{text_snippet}'")

do_you_have_a_card = driver.find_element(
    By.CLASS_NAME, "halo interview-episode-response emph"
)
do_you_have_a_card.click()

buttons = driver.find_elements(By.CLASS_NAME, "settings-row-button halo")

if len(buttons) >= 2:
    print(buttons[1].text)
    buttons[1].click()
else:
    print("Less than two buttons found.")

driver.quit()
