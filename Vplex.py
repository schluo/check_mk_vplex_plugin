#!/usr/bin/env python3
# encoding: utf-8

__author__    = "Oliver Schlueter"
__copyright__ = "Copyright 2020, Dell Technologies"
__license__   = "GPL"
__version__   = "1.0.2"
__credits__   = ["Martin Rohrbach", "Stefan Schneider"]
__email__     = "oliver.schlueter@dell.com"
__status__    = "Production"

""""
############################################
#
#  DELL EMC VPLEX plugin for check__mk
#
############################################

#import modules"""
import argparse
import sys
import os
import re
import json
import requests
import urllib3
import csv
import collections
import datetime
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

###########################################
#        VARIABLE
###########################################
DEBUG = False

module_arg = {
                'configuration': '--configuration',
                'back-end': '--back-end',
                'front-end': '--front-end',
                'cache': '--cache',
                'consistency-group': '--consistency-group',
                'wan': '--wan',
                'hardware': '--hardware',
                'cluster_witness': '--cluster_witness',
                'vpn': '--vpn',
                'io-aborts': '--io-aborts',
                'stats': '--stats',
    }

###########################################
#    Methods
###########################################

def escape_ansi(line):
        ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', str(line))

def get_argument():
    global hostaddress, user, password, module, arg_cmd, create_config
    try:
        # Setup argument parser
        parser = argparse.ArgumentParser()
        parser.add_argument('-H', '--hostname',
                            type=str,
                            help='hostname or IP address',
                            required=True)
        parser.add_argument('-u', '--username',
                            type=str,
                            help='username', dest='username',
                            required=True)
        parser.add_argument('-p', '--password',
                            type=str,
                            help='user password',
                            required=True)
        parser.add_argument('-m', '--module',
                            type=str,
                            choices=['configuration',
                                     'back-end',
                                     'front-end',
                                     'cache',
                                     'consistency-group',
                                     'wan',
                                     'hardware',
                                     'cluster_witness',
                                     'vpn',
                                     'io-aborts',
                                     'stats'],
                            help='Requested MODULE for getting status. \
                                    Possible options are: configuration  | \
                                     back-end | front-end | cache | \
                                     consistency-group | wan hardware |\
                                     cluster_witness | vpn io-aborts | stats',
                            dest='module', required=True)
        parser.add_argument('-c', '--config', action='store_true', help='build new metric config file',required=False, dest='create_config')
        args = parser.parse_args()

    except KeyboardInterrupt:
        # handle keyboard interrupt #
        return 0

    hostaddress = args.hostname
    user = args.username
    password = args.password
    create_config = args.create_config
    module = args.module.lower()
    arg_cmd = module_arg[module]


###########################################
#    CLASS
###########################################

class Vplex():
    # This class permit to connect of the vplex's API

    def __init__(self):
        self.user = user
        self.password = password
        self.cmd = arg_cmd

    def send_request_stats(self):
        # send a request and get the result as dict
        global all_data

        # prepare request http
        headers = {'Username': self.user, 'Password': self.password}
        all_data = {}

        try:
            # Request cluster names
            url = 'https://' + hostaddress + '/vplex/v2/clusters'
            payload = ""
            r = requests.get(url, json=payload, headers=headers, verify=False)
            j = json.loads(r.content)

            # filter to local cluster to avoid getting info about remote clusters
            for vplex_cluster in j:
                if vplex_cluster['is_local']:
                    vplex_cluster_name =vplex_cluster['name']

        except Exception as err:
            print(timestamp + ": Not able to get cluster names: " + str(err))
            exit(1)

        # Request metrics of local cluster
        try:
            url = 'https://' + hostaddress + '/vplex/v2/clusters/' + vplex_cluster_name + '/system_monitors'
            payload = ""
            r = requests.get(url, json=payload, headers=headers, verify=False)
            j = json.loads(r.content)
        except Exception as err:
            print(timestamp + ": Not able to get metrics names: " + str(err))
            exit(1)

        # Request metric values
        try:
            for vplex_metrics in j:
                url = 'https://' + hostaddress + vplex_metrics
                payload = ""
                r = requests.get(url, json=payload, headers=headers, verify=False)
                j = json.loads(r.content)
                metric_values = j['statistics']
                # Generate Director Name from metric path
                director_name = vplex_metrics.split('/')[-1].replace('-','_')
                director_name = director_name.split('_PERPETUAL')[0]
                all_data[director_name] = metric_values
        except Exception as err:
            print(timestamp + ": Not able to get metrics values: " + str(err))
            exit(1)


    def send_request_health(self):
        try:
            # send a request and get the result string list
            global status_split
            headers = {'Username': self.user, 'Password': self.password}
            url = 'https://' + hostaddress + '/vplex/health-check'
            payload = {'args': self.cmd}
            r = requests.post(url, json=payload, headers=headers, verify=False)

            # prepare return to analyse
            j = json.loads(r.text)
            full_status = j['response']['custom-data']
            full_status = escape_ansi(full_status)
            status_split = full_status.split('\n')

            if DEBUG:
                print(status_split)

            return status_split
        except Exception as err:
            print(timestamp + ": Not able to get health status: " + str(err))
            exit(1)

    def process_stats(self):
        self.send_request_stats()

        # read filter list
        try:
            fobj = open(metric_filter_file,"r")
            stats_filter = fobj.readlines()
            fobj.close()
        except Exception as err:
            print(timestamp + ": Not able to load Vplex metrics filter file: " + str(err))
            exit(1)

        # remove \n
        stats_filter = list(map(lambda s: s.strip(), stats_filter))

        # initiate plugin output
        try:
            checkmk_output = "Perf Data successful loaded at " + timestamp +" | "
            check_mk_metric_conf = ""
            for director in sorted(all_data):
                #print(data)
                metrics = all_data[director].keys()
                filtered_metrics = list(filter(lambda x: any(xs in x for xs in stats_filter), metrics))

                for metric in sorted(filtered_metrics):
                    perf_value = all_data[director][metric]

                    # transform to basic units
                    if "KB/s" in metric:
                        perf_value = perf_value * 1024
                    if "(us)" in metric:
                        perf_value = perf_value / 1000000

                    # generate metric name for plugin output
                    metric_full_name = director + "_" + metric.replace(' ','_').replace('/','_')

                    # generate metric description for metric config file
                    metric_description = director + ": " + metric.split("(")[0]. \
                                                                  replace("be", "Back-End"). \
                                                                  replace("fe_","Front-End_"). \
                                                                  replace("avg_lat", "Average Latency"). \
                                                                  replace("_"," "). \
                                                                  replace("director.",""). \
                                                                  replace("director","Director")
                    # if command line option "-c" was set
                    if create_config:

                        if "KB/s" in metric: metric_unit = "bytes/s"
                        if "us" in metric: metric_unit = "s"
                        if "counts/s" in metric: metric_unit = "1/s"
                        if "%" in metric: metric_unit = "%"

                        check_mk_metric_conf += 'metric_info["' + metric_full_name +'"] = { ' + "\n" + \
                            '    "title" : _("' + metric_description.title() + '"),' + "\n" + \
                            '    "unit" : "' + metric_unit +'",' + "\n" + \
                            '    "color" : "' + self.random_color() + '",' + "\n" + \
                        '}' + "\n"

                    checkmk_output += "'" + metric_full_name +"'=" + ("{:.4f}".format(perf_value)).rstrip('0').rstrip('.') + ";;;; "
                    #checkmk_output += "'" + metric_full_name +"'=" + str(perf_value) + ";;;; "
            # print result to standard output
            print(checkmk_output)

            # if command line option "-c" was set
            if create_config:
                try:
                    fobj = open(metric_config_file,"w")
                    fobj.write(check_mk_metric_conf)
                    fobj.close()
                except Exception as err:
                    print(timestamp + ": Not able to write metric config file: " + str(err))
                    exit(1)

        except Exception as err:
            print(timestamp + ": Error while generating result output: " + str(err))
            exit(1)

        sys.exit(0)

    def analyse_result(self):

        """ ------------- CONFIGURATION -----------
         send and treat the data for module configuration status_split ( the return of request http ) is of the form :
         ['Configuration (CONF):',
         'Checking VPlexCli connectivity to directors........ OK',
          'Checking Directors Commission...................... OK',
          'Checking Directors Communication Status............ OK',
          'Checking Directors Operation Status................ OK',
          'Checking Inter-director management connectivity.... OK',
          'Checking ports status.............................. OK',
          'Checking Call Home Status.......................... Error',
          'Checking Connectivity.............................. OK',
          'Checking Meta Data Backup.......................... Warning',
          'Checking Meta Data Slot Usage...................... OK','',
          'Output to /var/log/VPlex/cli/health_check_full_scan.log', '', '']
        """

        self.send_request_health()

        # count occurences of key words
        
        ok_count = 0
        warning_count = 0
        error_count = 0
        none_error = 0
        
        for status in status_split:
            if str(status).lower().endswith("ok"): ok_count += 1
            if str(status).lower().endswith("warning"): warning_count += 1
            if str(status).lower().endswith("error"): error_count += 1
            if str(status).lower().endswith("degraded"): error_count += 1
            if str(status).lower().endswith("none"): none_error += 1
            
        """ok_count = str(status_split).lower().count("ok\n")
        warning_count = str(status_split).lower().count("warning\n")
        error_count = str(status_split).lower().count("error\n") + str(status_split).lower().count("degraded\n")
        none_error = str(status_split).lower().count("none\n") """

        if error_count > 0:
            print(timestamp + " - Final status: Error")
            for status in status_split:
                if status != "" and not "Output to" in  status: print(status)
            sys.exit(2)

        if warning_count > 0:
            print(timestamp + " - Final status: Warning")
            for status in status_split:
                if status != "" and not "Output to" in  status: print(status)
            sys.exit(1)

        if ok_count > 0:
            print(timestamp + " - Final status: Ok")
            for status in status_split:
                if status != "" and not "Output to" in  status: print(status)
            sys.exit(0)

        if none_error == 1:
            print(timestamp + " - Final status: No IO aborts")
            for status in status_split:
                if status != "" and not "Output to" in  status: print(status)
            sys.exit(0)

        sys.exit(3)

    # method to generate a random color in hex code
    def random_color(self):
        red = format(random.randrange(10, 254),'x');
        green = format(random.randrange(10, 254),'x');
        blue = format(random.randrange(10, 254),'x');
        return "#"+ red.zfill(2) + green.zfill(2) + blue.zfill(2)


def main(argv=None):
    # get and test arguments
    get_argument()

    # store timestamp
    global timestamp, metric_filter_file, metric_config_file
    timestamp = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")

    metric_filter_file = os.path.dirname(__file__) + "/vplex_stats_filter"
    metric_config_file = os.path.dirname(__file__).replace("/lib/nagios/plugins", "/share/check_mk/web/plugins/metrics/vplex_perf_metric_" + hostaddress.replace(".","_")+ ".py")

    # display arguments if DEBUG enabled
    if DEBUG:
        print("hostname: "+hostaddress)
        print("user: "+user)
        print("password: "+password)
        print("module: "+module)
        print("args cmd: "+arg_cmd)
    else:
        sys.tracebacklimit = 0

    myvplex = Vplex()

    # process stats
    if module == 'stats':
        myvplex.process_stats()

    # process health status
    else:
        myvplex.analyse_result()

if __name__ == '__main__':
    main()
    sys.exit(3)
