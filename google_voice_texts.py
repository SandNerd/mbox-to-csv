#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Python script to parse google voice takeout messages into csv
# command line arguments

from bs4 import BeautifulSoup
import pandas as pd
import os
import argparse
import dateparser
import re
import pytz


def is_dst(dt):
    return pytz.timezone("US/Eastern").localize(dt, is_dst=None).tzinfo._dst.seconds != 0


def multireplace(string, replacements):
    """
    Given a string and a replacement map, it returns the replaced string.

    :param str string: string to execute replacements on
    :param dict replacements: replacement dictionary {value to find: value to replace}
    :rtype: str

    """
    # Place longer ones first to keep shorter substrings from matching
    # where the longer ones should take place
    # For instance given the replacements {'ab': 'AB', 'abc': 'ABC'} against
    # the string 'hey abc', it should produce 'hey ABC' and not 'hey ABc'
    substrs = sorted(replacements, key=len, reverse=True)

    # Create a big OR regex that matches any of the substrings to replace
    regexp = re.compile('|'.join(map(re.escape, substrs)))

    # For each match, look up the new string in the replacements
    return regexp.sub(lambda match: replacements[match.group(0)], string)


replacements_titles = {
    "Received": '\U0001F4F2 Call-Received',
    "Placed": '\U0001F4DE Call-Placed',
    "Missed": '\U0001F4F4 Call-Missed',
    "Text": '\U0001F4DF SMS',
    "Voicemail": '\U0001F4FC Voicemail'
}

replacements_tz = {
    "Standard": {
        "\n": ' ',
        "Eastern Time": 'EST',
        "Central Time": 'CST',
        "Pacific Time": 'PST'
    },
    "Daylight": {
        "\n": ' ',
        "Eastern Time": 'EDT',
        "Central Time": 'CDT',
        "Pacific Time": 'PDT'
    },
}

ISO8601 = "%Y-%m-%dT%H:%M:%SZ"

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", required=True,
                help="path to exported Google Voice directory (has 'Voice' folder inside it)")
ap.add_argument("-o", "--output", required=False,
                help="path to folder where CSV file will be saved. Google Voice directory is used if not supplied")
args = vars(ap.parse_args())
# print('input: {}'.format(args["input"]))

takeout_dir = args["input"]
exp_dir = args["output"] or takeout_dir
tko_calls_dir = os.path.join(takeout_dir, 'Voice', 'Calls')

message_df = pd.DataFrame(
    # columns=['Date', 'Time', 'From', 'Content', 'Type', 'Date (UTC)']
    columns=[
        'Title',
        'Date (GMT)',
        'Type',
        'From',
        'Content'
    ]
)


# Function to get all text log files
def get_html_files(calls_dir):
    file_list = []
    for file in os.listdir(calls_dir):
        if file.endswith(".html"):
            file_list.append(os.path.join(calls_dir, file))
        else:
            continue
    return file_list


# Function to process file
def parse_file(file_path):
    basename, extension = os.path.splitext(os.path.basename(file_path))
    number, msg_type, utc_date = basename.split(' - ')
    utc_date = utc_date.replace("_", ":")
    soup = BeautifulSoup(open(file_path), 'html.parser')
    if msg_type == 'Text':
        messages = soup.find_all('div', {'class': 'message'})
    else:
        messages = soup.find_all('div', {'class': 'haudio'})

    message_ct = len(messages)
    for x in range(message_ct):
        try:
            msg = messages[x]
            raw_dtime = msg.find_all('abbr')[0].text
            iter_date = raw_dtime.split(
                ',')[0] + raw_dtime.split(',')[1]
            iter_time = raw_dtime.split(',')[2].split('\n')[0][1:]
            # iter_number = msg_1.find_all('a')[0].text.replace('+', '')

            if is_dst(dateparser.parse(iter_date)):
                replacements = replacements_tz["Daylight"]
            else:
                replacements = replacements_tz["Standard"]

            datetime_utc = dateparser.parse(
                multireplace(raw_dtime, replacements),
                settings={'TO_TIMEZONE': 'UTC'})
            if msg_type == 'Text':
                iter_message = msg.find_all('q')[0].text
            else:
                # iter_message = msg_1.find_all('span')[4].text
                if msg_type == 'Voicemail':
                    try:
                        iter_message = "Transcription: " + msg.find_all(
                            "span", class_="full-text")[0].text
                    except Exception as e:
                        iter_message = "NO TRANSCRIPTION. SEE AUDIO FILE"
                        print("Proabably no transcription:", file_path, e)
                else:
                    try:
                        iter_message = "Call Duration: " + \
                            msg.find_all('abbr')[1].text[1:][:8]
                    except:
                        iter_message = ''

            message_df.loc[len(message_df)] = [
                # iter_date,
                # iter_time,
                replacements_titles[msg_type],  # title
                datetime_utc.strftime(ISO8601),
                replacements_titles[msg_type],
                number,
                iter_message
            ]
        except Exception as e:
            print('File {} encountered: {}', file_path, e)
            continue


# Function to save dataframe
def save_df(df):
    save_path = os.path.join(exp_dir, 'Message_Export.csv')
    df.to_csv(save_path, index=False)
    print('Message DF saved: {}'.format(save_path))

# Main function to process all files


def main():
    html_files = get_html_files(tko_calls_dir)
    for file in html_files:
        parse_file(file)
    save_df(message_df)


if __name__ == '__main__':
    main()
