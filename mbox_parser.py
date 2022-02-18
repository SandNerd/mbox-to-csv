from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email_reply_parser import EmailReplyParser
from email.utils import parsedate_tz, mktime_tz
from dateutil import tz

import ast
import datetime
import mailbox
import ntpath
import os
import quopri
import re
import sys
import time
import unicodecsv as csv

# converts seconds since epoch to mm/dd/yyyy string

ISO8601 = "%Y-%m-%dT%H:%M:%SZ"


def negative_or_empty(x):
    return str(x).lower() in ["0", "false", "no", "none", ""]


def get_date(second_since_epoch, date_format, as_utc):
    if second_since_epoch is None:
        return None
    time_tuple = parsedate_tz(email["date"])
    utc_seconds_since_epoch = mktime_tz(time_tuple)
    if not negative_or_empty(as_utc):
        # if as_utc.lower() == "true" or as_utc.lower() is True:
        datetime_obj = datetime.datetime.utcfromtimestamp(
            utc_seconds_since_epoch)
    else:
        datetime_obj = datetime.datetime.fromtimestamp(utc_seconds_since_epoch)

    if negative_or_empty(date_format):
        date_format = ISO8601

    return datetime_obj.strftime(date_format)

# clean content


def clean_content(content):
    # decode message from "quoted printable" format
    content = quopri.decodestring(content)

    # try to strip HTML tags
    # if errors happen in BeautifulSoup (for unknown encodings), then bail
    try:
        soup = BeautifulSoup(content, "html.parser",
                             from_encoding="iso-8859-1")
    except Exception as e:
        return ''
    return ''.join(soup.findAll(text=True))

# get contents of email


def get_content(email):
    parts = []

    for part in email.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        content = part.get_payload(decode=True)

        part_contents = ""
        if content is None:
            part_contents = ""
        else:
            part_contents = EmailReplyParser.parse_reply(
                clean_content(content))

        parts.append(part_contents)

    return parts[0]

# get all emails in field


def get_emails_clean(field):
    # find all matches with format <user@example.com> or user@example.com
    matches = re.findall(
        r'\<?([a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,5})\>?', str(field))
    if matches:
        emails_cleaned = []
        for match in matches:
            emails_cleaned.append(match.lower())
        unique_emails = list(set(emails_cleaned))
        return sorted(unique_emails, key=str.lower)
    else:
        return []


# entry point
if __name__ == '__main__':
    argv = sys.argv

    if len(argv) != 2:
        print('usage: mbox_parser.py [path_to_mbox]')
    else:
        # load environment settings
        load_dotenv(verbose=True)

        mbox_file = argv[1]
        file_name = ntpath.basename(mbox_file).lower()
        export_file_name = mbox_file + ".csv"
        export_file = open(export_file_name, "wb")

        # get owner(s) of the mbox
        owners = []
        if os.path.exists(".owners"):
            with open('.owners', 'r') as ownerlist:
                body = ownerlist.read()
                owner_dict = ast.literal_eval(body)
            # find owners
            for owners_array_key in owner_dict:
                if owners_array_key in file_name:
                    for owner_key in owner_dict[owners_array_key]:
                        owners.append(owner_key)

        # get domain blacklist
        blacklist_domains = []
        if os.path.exists(".blacklist"):
            with open('.blacklist', 'r') as blacklist:
                blacklist_domains = [domain.rstrip()
                                     for domain in blacklist.readlines()]

        # create CSV with header row
        headers = ["DATE", "SENT_FROM", "SENT_TO", "CC", "SUBJECT", "Body"]
        headers_txt = [
            os.getenv(x) for x in headers if not negative_or_empty(os.getenv(x))]

        writer = csv.writer(export_file, encoding='utf-8')

        writer.writerow(headers_txt)

        # create row count
        row_written = 0

        for email in mailbox.mbox(mbox_file):
            # capture default content
            row = []
            if not negative_or_empty(os.getenv("DATE")):
                date = get_date(email["date"],
                                os.getenv("DATE_FORMAT"),
                                os.getenv("UTC"))
                row.append(date)
            if not negative_or_empty(os.getenv("SENT_FROM")):
                sent_from = get_emails_clean(email["from"])
                row.append(", ".join(sent_from))

            if not negative_or_empty(os.getenv("SENT_TO")):
                sent_to = get_emails_clean(email["to"])
                row.append(", ".join(sent_to))

            if not negative_or_empty(os.getenv("CC")):
                cc = get_emails_clean(email["cc"])
                row.append(", ".join(cc))

            if not negative_or_empty(os.getenv("SUBJECT")):
                subject = re.sub('[\n\t\r]', ' -- ', str(email["subject"]))
                if not negative_or_empty(os.getenv("SUBJECT_PREPEND")):
                    subject = os.getenv("SUBJECT_PREPEND") + subject
                row.append(subject)

            if not negative_or_empty(os.getenv("BODY")):
                body = get_content(email)
                row.append(body)

            # date, sent_from, sent_to, cc, subject, contents, owners, blacklist_domains, combine_to_cc
            # ["flagged", "date", "description", "from", "to", "cc", "subject", "content", "time (minutes)"]
            # write the row
            writer.writerow(row)
            row_written += 1

        # report
        report = "generated " + export_file_name + \
            " for " + str(row_written) + " messages"
        report += " (" + os.getenv("CANT_CONVERT_COUNT") + \
            " could not convert; "
        report += os.getenv("BLACKLIST_COUNT") + " blacklisted)"
        print(report)

        export_file.close()
