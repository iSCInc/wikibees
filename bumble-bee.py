#! /usr/bin/env python

import os
import sys
import datetime
import ConfigParser
import argparse
import socket
import MySQLdb as mdb
import simplejson
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError
from simplemediawiki import MediaWiki


def get_config(config_file='bumble-bee.cfg'):
    try:
        config = ConfigParser.ConfigParser()
        config.read(config_file)
    except IOError:
        print "Cannot open %s." % config_file

    return config


def get_args():
    parser = argparse.ArgumentParser(prog="Bumble Bee",
                        description="retrieves usage and statistic information for WikiApiary")
    parser.add_argument("-s", "--segment",
                help="only work on websites in defined segment")
    parser.add_argument("-d", "--debug", action="store_true",
                help="do not write any changes to wiki or database")
    parser.add_argument("--config", default="bumble-bee.cfg",
                help="use an alternative config file")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                help="increase output verbosity")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1")

    # All set, now get the arguments
    args = parser.parse_args()

    return args


def get_websites(wiki, segment):
    global config
    global args

    segment_string = ""
    if segment is not None:
        if args.verbose >= 1:
            print "Only retrieving segment %s." % args.segment
        segment_string = "[[Has bot segment::%d]]" % int(args.segment)

    # Build query for sites
    my_query = "[[Category:Website]][[Is validated::True]][[Is active::True]][[Collect statistics::+]][[Collect semantic statistics::+]]"
    my_query += segment_string
    my_query += "|?Has API URL|?Check every|?Creation date|?Has ID|?Collect statistics|?Collect semantic statistics"
    my_query += "|sort=Creation date|order=asc|limit=500"

    sites = wiki.call({'action': 'ask', 'query': my_query})

    # We could just return the raw JSON object from the API, however instead we are going to clean it up into an
    # easier to deal with array of dictionary objects.
    # To keep things sensible, we'll use the same name as the properties
    if len(sites['query']['results']) > 0:
        my_sites = []
        for pagename, site in sites['query']['results'].items():
            if args.verbose >= 2:
                print "Adding %s." % pagename.encode('utf8')
            my_sites.append({
                'pagename':pagename.encode('utf8'),
                'Has API URL':site['printouts']['Has API URL'][0],
                'fullurl':site['fullurl'].encode('utf8'),
                'Check every':site['printouts']['Check every'][0],
                'Collect statistics':(site['printouts']['Collect statistics'][0]=="t"), # This is a boolean but it's returned as t or f, let's make it a boolean again
                'Has ID':site['printouts']['Has ID'][0],
                'Collect semantic statistics':(site['printouts']['Collect semantic statistics'][0]=="t") # This is a boolean but it's returned as t or f, let's make it a boolean again
                })

        return my_sites
    else:
        raise Exception("No sites were returned to work on.")


def main():
    # Set global socket timeout for all our web requests
    socket.setdefaulttimeout(5)

    # Get command line options
    global args
    args = get_args()

    # Get configuration settings
    global config
    config = get_config(args.config)

    # Setup our database connection and get a cursor to work with
    apiarydb = mdb.connect(
        host=config.get('ApiaryDB', 'hostname'),
        db=config.get('ApiaryDB', 'database'),
        user=config.get('ApiaryDB', 'username'),
        passwd=config.get('ApiaryDB', 'password'))

    # Setup our connection to the wiki too
    wiki = MediaWiki(config.get('WikiApiary', 'API'))
    wiki.login(config.get('WikiApiary', 'Username'), config.get('WikiApiary', 'Password'))

    sites = get_websites(wiki, args.segment)

    if args.verbose >= 3:
        for i in sites:
            print i

# Run main
if __name__ == '__main__':
    main()
