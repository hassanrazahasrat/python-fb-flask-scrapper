# Scrapper using flask API

Scrape FB Public Posts without using Facebook API 

## Install Requirements

Install Python

Please make sure chrome is installed and ```chromedriver``` is placed in the same directory as the file

Find out which version of ```chromedriver``` you need to download in this link [Chrome Web Driver](https://sites.google.com/chromium.org/driver/downloads).

Place your login credentials into ```env.txt```


```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

flask run --host=0.0.0.0 --reload
```

If ```flask``` isn't in your path:
add this in your ```.zshrc``` or ```.bashrc```

```sh
export PATH="$PATH:/home/$USER/.local/bin"
```

and then run 

```sh
flask run --host=0.0.0.0 --reload
```
