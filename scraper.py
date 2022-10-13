import argparse
import time
import json
import csv
from typing import Any
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs


with open('env.txt') as file:
    EMAIL = file.readline().split('"')[1]
    PASSWORD = file.readline().split('"')[1]

def _process_post(post_source):
    post = dict()
    post['title'] = _extract_post_user(post_source)
    post['content'] = _extract_post_text(post_source)
    post['images'] = _extract_images(post_source)

    return post

def _extract_post_user(post):
    return post.select_one('.story_body_container > header > div:nth-child(2) h3 strong a').string.strip()

def _extract_post_text(item: Any):
    body = item.select('.story_body_container > div span > p')
    text = ""
    for index in range(0, len(body)):
        if body[index].string is not None:
            text += body[index].string

    return text.strip().replace('  ', ' ')


def _extract_images(item):
    postPictures = item.select(".story_body_container > div:nth-child(2) a")
    images = list()
    for postPicture in postPictures:
        images.append(postPicture.get('href'))

    return images


def _extract_html(bs_data):
    if len(bs_data) == 0:
        print("Empty source code")

        return dict()

    #Add to check
    with open('./bs.html',"w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

    # with open('./bs.html', 'r', encoding='utf-8') as file:
    #     bs_data = bs(file.read().replace('\n', ''), 'html.parser')

    k = bs_data.select("#BrowseResultsContainer [data-testid=results] [data-module-result-type=story] > div")
    postBigDict = list()

    for item in k:
        postDict = _process_post(item)

        postBigDict.append(postDict)

        with open('./postBigDict.json','w', encoding='utf-8') as file:
            file.write(json.dumps(postBigDict, ensure_ascii=False).encode('utf-8').decode())

    return postBigDict


def _login(browser, email, password):
    browser.get("https://m.facebook.com")
    browser.maximize_window()
    browser.find_element("name", "email").send_keys(email)
    browser.find_element("name", "pass").send_keys(password)
    browser.find_element("name", 'login').click()

    print('Logged In...')
    time.sleep(5)


def _count_needed_scrolls(browser, infinite_scroll, numOfPost):
    if infinite_scroll:
        lenOfPage = browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
        )
    else:
        # roughly 8 post per scroll kindaOf
        lenOfPage = int(numOfPost / 8)
    print("Number Of Scrolls Needed " + str(lenOfPage))
    return lenOfPage


def _scroll(browser, infinite_scroll, lenOfPage):
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


def extract(page, numOfPost=8, infinite_scroll=False, scrape_comment=False):
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
    
    page_url = f"https://m.facebook.com/search/latest/?q={encodedPage}&ref=content_filter&source=typeahead"

    print("Fetching " + page_url)

    browser.get(page_url)
    lenOfPage = _count_needed_scrolls(browser, infinite_scroll, numOfPost)
    _scroll(browser, infinite_scroll, lenOfPage)

    source_data = browser.page_source

    if (page in source_data):
        print("It's logged in")
    else:
        print("It's not logged in")
        _login(browser, EMAIL, PASSWORD)

    # Throw your source into BeautifulSoup and start parsing!
    bs_data = bs(source_data, 'html.parser')

    postBigDict = _extract_html(bs_data)
    browser.close()

    return postBigDict

def _get_chrome_options():
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")
    option.add_argument("user-data-dir=selenium")
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
    required_parser.add_argument('-len', '-l', help="Number of Posts you want to scrape", type=int, required=True)
    optional_parser = parser.add_argument_group("optional arguments")
    optional_parser.add_argument('-infinite', '-i',
                                 help="Scroll until the end of the page (1 = infinite) (Default is 0)", type=int,
                                 default=0)
    optional_parser.add_argument('-usage', '-u', help="What to do with the data: "
                                                      "Print on Screen (PS), "
                                                      "Write to Text File (WT) (Default is WT)", default="WT")

    optional_parser.add_argument('-comments', '-c', help="Scrape ALL Comments of Posts (y/n) (Default is n). When "
                                                         "enabled for pages where there are a lot of comments it can "
                                                         "take a while", default="No")
    args = parser.parse_args()

    infinite = False
    if args.infinite == 1:
        infinite = True

    scrape_comment = False
    if args.comments == 'y':
        scrape_comment = True

    postBigDict = extract(page=args.page, numOfPost=args.len, infinite_scroll=infinite, scrape_comment=scrape_comment)

    #TODO: rewrite parser
    if args.usage == "WT":
        with open('output.txt', 'w') as file:
            for post in postBigDict:
                file.write(json.dumps(post))  # use json load to recover

    elif args.usage == "CSV":
        with open('data.csv', 'w',) as csvfile:
           writer = csv.writer(csvfile)
           #writer.writerow(['Post', 'Link', 'Image', 'Comments', 'Reaction'])
           writer.writerow(['Post', 'Link', 'Image', 'Comments', 'Shares'])

           for post in postBigDict:
              writer.writerow([post['Post'], post['Link'],post['Image'], post['Comments'], post['Shares']])
              #writer.writerow([post['Post'], post['Link'],post['Image'], post['Comments'], post['Reaction']])

    else:
        for post in postBigDict:
            print(post)

    print("Finished")
