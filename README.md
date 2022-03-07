# check_mk_vplex_plugin
Plugin to integrate Dell EMC Vplex Systems into Check_MK

Although the plugin is designed to be used in Check_MK it is implemented as a NAGIOS plugin with Check_MK specific extentions. Thereofore it should be also possible to used it in NAGIOS. 

#Installation
Copy the plugin to /opt/omd/sites/{SITE NAME}/local/lib/nagios/plugins 

usage: vplex.py [-h] -H HOSTNAME -u USERNAME -p PASSWORD -m
                {configuration,back-end,front-end,cache,consistency-group,wan,hardware,cluster_witness,vpn,io-aborts,stats}
                [-c]

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTNAME, --hostname HOSTNAME
                        hostname or IP address
  -u USERNAME, --username USERNAME
                        username
  -p PASSWORD, --password PASSWORD
                        user password
  -m {configuration,back-end,front-end,cache,consistency-group,wan,hardware,cluster_witness,vpn,io-aborts,stats}, --module {configuration,back-end,front-end,cache,consistency-group,wan,hardware,cluster_witness,vpn,io-aborts,stats}
                        Requested MODULE for getting status. Possible options
                        are: configuration | back-end | front-end | cache | consistency-group | wan hardware | cluster_witness | vpn io-aborts | stats
  -c, --config          build new metric config file


The plugin can be used to get performance values as well as health status
To get performance values use the "-m stats" option. The filter file "vplex_stats_filter" will define the list of relevant values (substrings in the filter file will be considered)
To get health status information use the -m option followed by the Vplex platform context (configuration | back-end | front-end | cache | consistency-group | wan hardware | cluster_witness | vpn io-aborts

Define a check within Check_MK under "Classical active and passive Monitoring checks".

To initially create the metric config file use the -c option (directly from the CLI not from Check_MK/nagios)
The plugin will auto-create a metric config file in /opt/omd/sites/<site>/local/share/check_mk/web/plugins/metrics which allows to beautify the diagrams in Check_MK
  
---
  
Copyright (c) 2022 Dell Technologies

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
