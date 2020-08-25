# check_mk_vplex_plugin
plugin to integrate Dell EMC Vplex Systems into Check_MK

Although the plugin is designed to be used in Check_MK it is implemented as a NAGIOS plugin with Check_MK specific extentions. Thereofore it should be also possible to used it in NAGIOS. 

Installation
Copy the plugin to /opt/omd/sites/<site>/local/lib/nagios/plugins The plugin can be used to get performance values as well as health status
To get performance values use the "-m stats" option. The filter file "vplex_stats_filter" will define the list of relevant values (substrings in the filter file will be considered)
To get health status information use the -m option followed by the Vplex platform context (configuration | back-end | front-end | cache | consistency-group | wan hardware | cluster_witness | vpn io-aborts

Define a check within Check_MK under "Classical active and passive Monitoring checks" 
The plugin will auto-create a metric config file in /opt/omd/sites/<site>/local/share/check_mk/web/plugins/metrics which allows to beautify the diagrams in Check_MK
