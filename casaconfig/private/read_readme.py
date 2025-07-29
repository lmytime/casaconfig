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

def read_readme(path):
    """
    Read and parse the contents of a readme.txt file used by casaconfig.

    A dictionary containing the 'version', 'date', 'site', and 'extra' (containing
    a list of optional extra lines found). On error, the return values is None.

    The extra lines are stripped and do not include lines begining with '#'

    The format is assumed to be:
        a line begining with #, which is ignored.
        a line "site: the site url string"
        a line "version : the versions string"
        a line "date : the date"
        optional extra lines (the manifest of installed files for the main readme)

    The version, site and date strings are stripped of leading and trailing whitespace.

    The site string only appears in measures data and is missing is early readme
    files for measures data. If no site string is seen the value in the dictionary
    is None.

    Parameters
       - path (str) - the path to the file to be read

    Returns
       Dictionary of 'site' ( the site URL or None), 'version' (the version string), 
             'date' (the date string), 'extra' (a list of any extra lines found). 
             The return value is None on error except that format errors raise
             a BadReadme exception.

    Raises
       - casaconfig.BadReadme - raised when there is a format error in the file at path
    """

    import os
    from casaconfig import BadReadme

    site = None
    version = ""
    date = ""
    extra = []
    result = None

    try:
        with open(path, 'r') as fid:
            readmeLines = fid.readlines()
            # order is unimportant except the first line must start with
            # an "#" and the second line starting with "#" indicates the
            # start of the "extra" lines
            # duplicate instances of the same key in key : value lines are accepted
            # the last value associated with key is used, that should never happen.
            inExtraLines = False
            if readmeLines[0][0] != '#':
                raise BadReadme('Readme file missing required "#" at start of first line, %s' % path)
            for line in readmeLines[1:]:
                if inExtraLines and not (line[0] == '#'):
                    extra.append(line.strip())
                elif line[0] == '#':
                    inExtraLines = True
                else:
                    splitLine = line.split(':')
                    if len(splitLine) < 2:
                        raise BadReadme('A line did not have an expected ":" separating into at least two parts, %s' % path)
                    key = splitLine[0].strip()
                    if key == 'site':
                        # the URL likely also has a ":" so rejoin the second part and then strip that
                        siteURL = "".join(splitLine[1:])
                        site = siteURL.strip()
                    elif key == 'version':
                        version = splitLine[1].strip()
                    elif key == 'date':
                        date = splitLine[1].strip()
                    # anything else is OK and silently ignored
        result = {'site':site, 'version':version, 'date':date, 'extra':extra}
    except BadReadme as exc:
        # reraise it
        raise
    except Exception as exc:
        # silently return None, handled elsewhere
        result = None
        

    return result
