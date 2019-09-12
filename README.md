# DPoS Monitoring Tool for Delegates Across Multiple Chains

## Installation

Basic install:
```sh
git clone https://github.com/geopsllc/delegate-check -b productivity-statistics
cd delegate-check
bash install.sh
nano config.py
```
- change config.py with productivity-statistics enabled nodes
- test the script in cli mode by running ```python3 delcheck.py```

Frontend setup:
- add a crontab entry (```crontab -e```) to run the script every minute:
```* * * * * cd $HOME/delegate-check && python3 delcheck.py > /dev/null 2>&1```
- install and setup a webserver (apache/nginx) to serve folder web

## General

This is a DPoS Monitoring Tool for Multiple Delegates Across Multiple Networks.
- This release works only with alessiodf's productivity-statistics enabled APIs.
- Supports Core v2 only.
- Requires Python 3.6.7 or above - native on Ubuntu 18.04.
- The backend is async coded so most api calls are made almost simultaneously.
- You can use it in cli mode or bring up a web interface that refreshes every minute. 
- You can enable AWS SNS intergration to send a SMS meesage when a delegate misses a block.
- [Sample Website](http://dashboard.geops.net)

## Changelog
### 1.0

- official release

### 0.2

- added productivity column

### 0.1

- initial release

## Security

If you discover a security vulnerability within this package, please open an issue. All security vulnerabilities will be promptly addressed.

## Credits

- [All Contributors](../../contributors)
- [galperins4](https://github.com/galperins4)
- [Georgi Stoyanov](https://github.com/geopsllc)

## License

- [MIT](LICENSE) © [galperins4](https://github.com/galperins4)
- [MIT](LICENSE) © [geopsllc](https://github.com/geopsllc)

