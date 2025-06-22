# laptop-brick

Stop wasting time on the internet! Brick your computer with a Kasa plug (when the plug is ON, websites are blocked).

[Blog post explainer](https://www.neilchen.co/blog/kasa)

## Setup

1. (optional) add/remove websites by editing `blocklist`
1. `$ pip install -r requirements.txt`
1. Get the IP address of the plug you'll use: `kasa discover`
1. `$ python main.py --ip_address=<plug IP address>`
