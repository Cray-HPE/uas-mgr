#! /bin/bash

# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# Build a table of contents from a specified input file and
# present it on stdout.
#
# To build a table of contents from a file, all candidate
# sections in the input file must be of the form
#
# <heading tabs> <title> <anchor>
#
# where:
#
#    <heading tabs> is a non-space separated block of '#'
#                   characters corresponding to the heading
#                   level (e.g. '#####' for a level 5 heading)
#
#    <title> is free-form text not including a '<a'
#
#    <anchor> is an HTML anchor of the form:
#
#        <a name="this-is-the-name-of-my-anchor"></a>
#
# The lines in the table of contents will form a nested numbered
# list of internal links each named with the name of the section
# it links to.
if [ ! -f ${1} ]; then
    echo "usage mktoc.sh file" >&2
    exit 1
fi

counters=(0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0)
depth=$(( ${#counters[@]} - 1 ))
grep "^#.*<a " "${1}"  | while read l; do
    tabs="$(echo ${l} | sed -e 's/\(^##*\).*/\1/' -e 's/^#//')"
    title="$(echo ${l} | sed -e 's/^#* //' -e 's/^\(.*\)  *<a name=.*$/\1/')"
    anchor="$(echo ${l} | sed -e 's/^.*<a *name="\([^"]*\)".*$/\1/')"
    indent="$(echo ${tabs} | sed -e 's/#/    /g')"
    level=$(( $(echo ${tabs} | wc -c) - 1))
    if [ ${level} -lt ${depth} ]; then
        i=${depth}
        while [ ${i} -gt ${level} ]; do
            counters[${i}]=0
            i=$(( ${i} - 1 ))
        done
    fi
    counters[${level}]=$(( ${counters[${level}]} + 1))
    echo "${indent}${counters[${level}]}. [${title}](#${anchor})"
done
