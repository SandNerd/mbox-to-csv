# MBOX to CSV

![Python 3.8.3](https://img.shields.io/badge/python-3.8.3-yellow.svg)

Extract emails from an MBOX file into a CSV file.

## Example

```bash
# make a copy of capture.example.py named capture.py
cp capture.examples.py capture.py

# make a copy of rules.example.py named rules.py
cp rules.examples.py rules.py

# make a copy of .env.example named .env
cp .env.example .env

# launch virtual environment with included dependencies
source env/bin/activate

# run tool using example file
python3 mbox_parser.py example.mbox

# deactivate virtual environment
deactivate
```

## Embedding Python Interpreter and Dependencies into Platypus-Built App

With some manual effort, it is possible to package this script as a drag-and-drop Platypus-built Mac app. In order to do this, we are required to bundle a python installation (interpreter and dependencies) within the app's resources. This is possible by following the guide below.

- [Adding Embedded Python Interpreter](http://joaoventura.net/blog/2016/embeddable-python-osx/)

Once you are done with this guide, then you need to remove the `python3.8/lib/python3.8/site-packages` symlink and replace it with the `site-packages` that have been installed in your virtual environment as you were developing.

## References

- [Python Virtual Environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
- [Email Address and MIME Parsing](https://github.com/mailgun/flanker)
- [Signature Stripping Solution](https://github.com/mailgun/talon)
- [MBOX Parsing Example: Mining the Social](https://www.oreilly.com/library/view/mining-the-social/9781449368180/ch06.html)
- [Gmail MBOX Parser](https://github.com/alejandro-g-m/Gmail-MBOX-email-parser)
- [Mail Parser Package](https://pypi.org/project/mail-parser/)
