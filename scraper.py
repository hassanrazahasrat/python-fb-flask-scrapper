import argparse
import string
import time
import json
import re

from typing import Any
from unittest import result
from urllib.parse import quote

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs, Tag

FACEBOOK_URL = "https://m.facebook.com"
with open('env.txt') as file:
    line = file.read().split('\n')
    EMAIL = line[0].split('"')[1]
    PASSWORD = line[1].split('"')[1]

def _process_post(postTag: Tag):
    post = dict()
    post['user'] = _extract_post_user(postTag)
    post['group'] = _extract_post_group(postTag)
    post['content'] = _extract_post_text(postTag)
    post['image'] = _extract_post_images(postTag)
    post['content_link'] = _extract_post_link(postTag)
    post['permalink'] = _format_link(_extract_post_permalink(postTag))
    post['time'] = _extract_post_time(postTag)

    return post

def _extract_post_user(post: Tag):
    user_tag = post.select_one('.story_body_container > header > div:nth-child(2) h3 strong:first-child')

    return None if user_tag is None else {
        'name': user_tag.text.strip(),
        'profile_url': user_tag.select_one('a').get('href')
    }

def _extract_post_group(post: Tag):
    group_tag = post.select_one('.story_body_container > header > div:nth-child(2) h3 strong:last-child')
    
    return None if group_tag is None else {
        'name': group_tag.text.strip(),
        'profile_url': group_tag.select_one('a').get('href')
    }

def _extract_post_text(post: Tag):
    body = post.select_one('.story_body_container > div span:first-child')
    text = body.text if body is not None else ""

    return text.strip().replace('  ', ' ')

def _extract_post_images(post: Tag):
    picture = post.select_one(".story_body_container > div + div  a i.img")
    text = picture.get('style') if picture is not None else ""

    search = re.search('url(.*)\);', text)

    return search.group(1).replace('\\3a ', ':').replace("'", '').removeprefix('(') if search is not None else ""

def _extract_post_link(post: Tag):
    link_html = post.select_one(".story_body_container > div + div > section > a")

    return link_html.get('href') if link_html is not None else ""

def _extract_post_permalink(post: Tag):
    link_html = post.select_one(".story_body_container + footer > div > div + div > div + div > a")

    return link_html.get('href') if link_html is not None else ""

def _extract_post_time(post: Tag):
    return post.select_one('.story_body_container > header > div:nth-child(2) h3 + div > a > abbr').text.strip()

def _extract_html(bs_data: bs):
    if bs_data is None:
        print("Empty source code")

        return dict()

    # Add to check
    with open('./bs.html',"w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

    k = bs_data.select("#BrowseResultsContainer [data-testid=results] [data-module-result-type=story] > div")
    postBigDict = list()

    for item in k:
        postDict = _process_post(item)

        postBigDict.append(postDict)

        # For testing
        with open('./postBigDict.json','w', encoding='utf-8') as file:
            file.write(json.dumps(postBigDict, ensure_ascii=False).encode('utf-8').decode())

    return postBigDict

def _format_link(link: str):
    _final = link
    if link.startswith('/'):
        _final = "https://www.facebook.com" + link
    
    return _final

def _login(browser: WebDriver, email: str, password: str):
    browser.get(FACEBOOK_URL)
    browser.maximize_window()

    user_button = browser.find_element(By.CSS_SELECTOR, '[role=button][aria-label^="Tap to log in to Facebook"]')
    if user_button is not None:
        user_button.click()

        password_field = browser.find_element('name', 'pass')
        if password_field is not None:
            password_field.send_keys(password)
            browser.find_element(By.CSS_SELECTOR, 'button[type=submit][value="Log in"]').click()

        not_button = browser.find_element(By.LINK_TEXT, 'Not Now')
        if not_button is not None:
            not_button.click()

        time.sleep(5)
    else:
        browser.find_element("name", "email").send_keys(email)
        browser.find_element("name", "pass").send_keys(password)
        browser.find_element("name", 'login').click()

    print('Logged In...')
    time.sleep(5)

def _count_needed_scrolls(browser: WebDriver, infinite_scroll, numOfPost):
    if infinite_scroll:
        lenOfPage = browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
        )
    else:
        # roughly 8 post per scroll kindaOf
        lenOfPage = int(numOfPost / 8)
    print("Number Of Scrolls Needed " + str(lenOfPage))
    return lenOfPage

def _scroll(browser: WebDriver, infinite_scroll, lenOfPage):
    lastCount = -1
    match = False

    while not match:
        if infinite_scroll:
            lastCount = lenOfPage
        else:
            lastCount += 1

        # wait for the browser to load, this time can be changed slightly ~3 seconds with no difference, but 5 seems
        # to be stable enough
        time.sleep(5)

        if infinite_scroll:
            lenOfPage = browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return "
                "lenOfPage;")
        else:
            browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return "
                "lenOfPage;")

        if lastCount == lenOfPage:
            match = True

def extract(page, numOfPost=8, infinite_scroll=False):
    if page is None:
        return {
            'error': 'enter a query'
        }

    if len(EMAIL) == 0 or len(PASSWORD) == 0:
        return {
            'error': 'enter your facebook credetials'
        }

    encodedPage = quote(page)
    
    # chromedriver should be in the same folder as file
    browser = webdriver.Chrome(executable_path="./chromedriver", options=_get_chrome_options())
    
    source_data = _search_facebook(browser, encodedPage)

    if (page in source_data and "Facebook Search" in source_data):
        print("It's logged in")
    else:
        print("It's not logged in")
        _login(browser, EMAIL, PASSWORD)
        source_data = _search_facebook(browser, encodedPage)

        if "Log in with one" in source_data:
            print("Post login shit 'Log in with one tap' trying to skip")
            not_button = browser.find_element(By.LINK_TEXT, 'Not Now')
            if not_button is not None:
                not_button.click()
            else:
                print("Couldn't found the skip button :-(")

    lenOfPage = _count_needed_scrolls(browser, infinite_scroll, numOfPost)
    _scroll(browser, infinite_scroll, lenOfPage)

    # Throw your source into BeautifulSoup and start parsing!
    bs_data = bs(source_data, 'html.parser')

    postBigDict = _extract_html(bs_data)
    browser.close()

    return postBigDict

def _search_facebook(browser: WebDriver, term: str) -> str :
    page_url = f"{FACEBOOK_URL}/search/latest/?q={term}&ref=content_filter&source=typeahead"
    print("Fetching " + page_url)
    browser.get(page_url)

    return browser.page_source

def _get_chrome_options():
    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")
    option.add_argument("user-data-dir=selenium")
    option.add_argument("--disable-dev-shm-usage")
    option.headless = True

    # Pass the argument 1 to allow and 2 to block
    option.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 1
    })

    return option

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Page Scraper")
    required_parser = parser.add_argument_group("required arguments")
    required_parser.add_argument('-page', '-p', help="The Facebook Public Page you want to scrape", required=True)
    optional_parser = parser.add_argument_group("optional arguments")
    optional_parser.add_argument('-len', '-l', 
                            help="Number of Posts you want to scrape", type=int, default=2)
    optional_parser.add_argument('-infinite', '-i',
                            help="Scroll until the end of the page (1 = infinite) (Default is 0)", type=int,
                            default=0)
    args = parser.parse_args()

    infinite = False
    if args.infinite == 1:
        infinite = True

    postBigDict = extract(page=args.page, numOfPost=args.len, infinite_scroll=infinite)

    for post in postBigDict:
        print(post)

    print("Finished")
