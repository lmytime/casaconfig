# Copyright 2023 AUI, Inc. Washington DC, USA
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
this module will be included in the api
"""

import traceback

def measures_available(measures_site=None, logger=None):
    """
    Return a list of available measures versions at measures_site.

    This returns a list of the measures versions available at measures_site.
    If measures_site is None, then the config value of measures_site is used.

    The list of available measures is sorted so that the most recent file
    appears at the end of the list.

    The measures_site may be a single string value or a list of strings.
    If measures_site is a list then the elements are used in order until
    an appropriate list of available measures is found (see more below). 
    If measures_site is not provide then the measures_site config value 
    is used.

    The version parameter of measures_update must be one of the values in 
    the list returned by measures_available when set. If that parameter is
    not set in measures_update then the last element (the most 
    recent tar file) of that returned list is used.

    The config value of measures_site_interval is used when determining which
    site to use if measures_site is a list. When stepping through all the
    elements of measures_site, if the most recent measures tar file at that 
    site has a date that is not older than measuers_site_interval days before
    the current date then that list of measures tar files from that site
    is returned. If all of the list of measures tar files are older than
    measures_site_interval days before the current date then the list
    with the most recent tar file is returned. 

    If the returned list is older than measures_site_interval days before
    the current date then a warning is logged and printed following the
    the standard meaning of the casaconfig_verbose config value.

    When comparing the date of the most recent tar file with that of
    the current date, the date value (excluding the time) found in the
    tar file name is compared as is with the current date of the
    casaconfig user without any correction for time zone differences.
    This is an approximate age of the most recent tar file and is 
    primiarly intended to identify a site that may not be updating
    regularly (daily) as expected so that casaconfig can use another
    in the list of measures_site automatically. 

    The first element of the returned list is the measures_site where
    the list was found (the single string value used to assemble that 
    list).

    The list of available measures versions is the list of files at 
    measures_site that follow the pattern of WSRT_Measures*tar*, excluding
    files that end in ".md5".

    The site used is always logged when a logger is provided.

    Parameters
       - measures_site(str or list of str = None) - Each value is a URL where measures tar files are found. If measures_site is a list then the elements are used in order until a list can be assembled.
       - logger (casatools.logsink=None) - Instance of the casalogger to use for writing messages. Default None writes messages to the terminal. The value of config.casaconfig_verbose is used. The logger is only used if the last file in the returned list is more than config.measures_site_interval days than the current date.

    Returns
       list - version names returned as list of strings, the first element of this list is the is the site used. The file names are sorted by date and time as found in the name with the most recent name appearing at the end of the list.

    Raises
       - casaconfig.NoNetwork - Raised where there is no network seen, can not continue
       - casaconfig.RemoteError - Raised when there is an error fetching some remote content for some reason other than no network
       - ValueError - Raised when config.measures_site_interval can not be used as an int
       - Exception - Unexpected exception while getting list of available measures versions

    """
    from casaconfig import NoNetwork, RemoteError
    import urllib.error
    import re
    from datetime import date
    
    from .get_available_files import get_available_files
    from .print_log_messages import print_log_messages
    
    from .. import config as _config

    verbose = _config.casaconfig_verbose

    if measures_site is None:
        measures_site = _config.measures_site

    if isinstance(measures_site, list):
        saved_exc = None
        # this list is only used if all of the sites in the list are out of date
        # and it is necessary to find the one that's least out of date.
        # the list is a tuple of (age, file_list) where age is the age, in days, of
        # the last entry in file_list and file_list is the list of files at that
        # site
        file_age_list = []
        
        date_pattern = r".*_Measures_(\d{4})(\d{2})(\d{2})-.*"
        
        # this makes sure that measures_site_interval can be used as an int
        # this raises a ValueError if there's a problem
        measures_site_interval = int(_config.measures_site_interval)
            
        for this_site in measures_site:
            try:
                saved_exc = None
                result = measures_available(this_site)
                if len(result) > 0:
                    # get the age, in days, of the last entry in that list
                    # do not attempt to correct for time zones
                    dateMatch = re.search(date_pattern,result[-1])
                    siteDate = date(int(dateMatch.group(1)),int(dateMatch.group(2)),int(dateMatch.group(3)))
                    dateDiff = date.today() - siteDate
                    siteAge = dateDiff.days
                    if siteAge <= measures_site_interval:
                        return (result)
                    # the only way to get here is when the last file in result is more than measures_site_interval days from today
                    file_age_list.append((siteAge,result))
            except NoNetwork as exc:
                # reraise this, there's no recovering from it
                raise exc
            except Exception as exc:
                # save it, if it's still set when the loop exits, reraise it
                print("exception when trying : " + this_site)
                print(str(exc))
                print(str(type(exc)))
                saved_exc = exc

        if saved_exc is None:
            if len(file_age_list) > 0:
                # return the one with the smallest age
                thisAge = file_age_list[0][0]
                result = file_age_list[0][1]
                for age_tuple in file_age_list[1:]:
                    if age_tuple[0] < thisAge:
                        thisAge = age_tuple[0]
                        result = age_tuple[1]
                # and log that that's what's going on, not an exception
                msgs = []
                msgs.append("Warning: the most recent measures tar file at each of the sites was older than config.measures_interval_list")
                msgs.append("%s had the most recent measures tar file, returning that list" % result[0])
                msgs.append("config.measures_interval_list = %s and the most recent measures file in this list is %s days old" % (_config.measures_site_interval, thisAge))
                print_log_messages(msgs, logger, verbose)
                return(result)
            else:
                # that's odd, probably measures_site was an empty list or no files were found at any of the sites
                raise RemoteError("Unable to retrieve list of available measures versions, measures_site value may be an empty list or no files were found at any site, check and try again.")
        else:
            # saved exception
            # unsure what this should look like, need try to things out
            raise saved_exc

    else:
        # make sure it's used as a string
        measures_site = str(measures_site)

        # this pattern matches "<anything>_Measures_YYYYMMDD-HHMMSS.<anything>tar<anything>
        # where YYYY MM DD HH MM SS are all digits having exactly that number of digits.
        # "tar" must appear somewhere after the "." following the digits. This allows for
        # different compression schemes to be used and signaled in the name, so long as the
        # tarfile module can understand that compression. Note that get_available_tarfiles
        # also excludes files that end in "md5". That is currently only relevant for casarundata
        # but it may be an issue in some future site so that excludes those files.
        pattern = r".*_Measures_\d{8}-\d{6}\..*tar.*"
        
        try:
            files_list = get_available_files(measures_site, pattern)

            # because the prefix changed during the development of the NRAO/casa measures
            # tarballs this list needs to be sorted, excluded everything before "Measures_".
            # it's probably not a bad idea in general, that keeps things in time sorted order

            def sort_after_Measures(text):
                # extract the substring after "Measures_" for sorting.
                return text.split("Measures")[1]
            result = sorted(files_list, key=sort_after_Measures)
            
            # and prepend the measures_site to the list
            result.insert(0,measures_site)
            
            return (result)
    
        except NoNetwork as exc:
            # reraise this as is
            raise exc
    
        except urllib.error.URLError as urlerr:
            raise RemoteError("Unable to retrieve list of available measures versions : " + str(urlerr)) from None
        except UnicodeError as unicodeErr:
            raise RemoteError("Unable to retrieve list of available measures versions because of a UnicodeError, likely the site name is incorrect. Site : " + str(measures_site) + " error: " + str(unicodeErr)) from None
        except Exception as exc:
            msg = "Unexpected exception while getting list of available measures versions : " + str(exc)
            raise Exception(msg)

        # nothing to return if it got here, I don't think there's a way to get here, anything not already returning raises an exception
    return []
