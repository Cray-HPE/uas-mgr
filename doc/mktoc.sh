#! /bin/bash

# Copyright 2020 Hewlett Packard Enterprise Development LP#
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
