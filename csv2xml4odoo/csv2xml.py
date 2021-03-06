#!/usr/bin/env python
# coding: utf-8

# based on this code
# http://code.activestate.com/recipes/577423-convert-csv-to-xml/

# v1.2

# Changelog
# v1.2  add more args and help
# v1.1  add args capability
# v1    fix m2m


import csv
import glob
import sys

NOUPDATE = 1
BOOLEAN = ('True', 'False')
ERP_HEADER = """<?xml version="1.0"?>
<openerp>
    <data noupdate="%s">"""

ERP_FOOTER = """
    </data>
</openerp>
"""


def help():
    print """
HELP
----
Use: csv2xml.py [OPTION]... [FILE]
Convert Odoo csv files in xml files
    csv is easy to maintain but xml data have 'noupdate' feature
    (required for production environnement)

Options:
    -a, --all       Convert all csv files of the folder
    -u, --update    Set 'noupdate' attribute to 0 instead of 1

Limitations:
- relation field One2many is NOT SUPPORTED
- ambiguous columns: char type but contains float string,
  should have special suffix on column name '|char'
- relationnal fields notation in csv should be:
    myfield_id/id for m2o or myfield_ids/id for m2m

    """


def check_arg(argument):
    if '--%s' % argument in sys.argv or '-%s' % argument[0] in sys.argv:
        return True


def convert_relationnal_field2xml(tag, value):
    mytag = tag
    for elm in ['/ids', '/id', ':id']:
        mytag = mytag.replace(elm, '')
    if tag[-6:] == 'ids/id':
        # many2many
        xml_ids = value.split(',')
        members = ["ref('%s')" % x for x in xml_ids]
        line = '%s" eval="[(6, 0, [%s])]"/>' % (mytag, ', '.join(members))
    else:
        # many2one
        line = '%s" ref="%s"/>' % (mytag, value)
    return line


def convert_file(csv_file):
    global NOUPDATE
    xml_file = csv_file.replace('.', '_').replace('_csv', '_data.xml')
    csv_data = csv.reader(open(csv_file))
    xml_data = open(xml_file, 'w')
    xml_data.write(ERP_HEADER % NOUPDATE + "\n\n\n")
    row_num = 0
    for row in csv_data:
        if row_num == 0:
            tags = row
            for i in range(len(tags)):
                tags[i] = tags[i].replace(' ', '_')
            if 'id' in tags:
                id_position = tags.index('id')
            else:
                print ("EXCEPTION: No 'id' in %s: impossible to generate "
                       "the xml file\n" % csv_file)
                return
        else:
            for i in range(len(tags)):
                char = False
                # ambiguous column (char type but contains float string)
                # should be mark by suffix |char
                if tags[i][-5:] == '|char':
                    char = True
                numeric = False
                begin = '    <field name="'
                try:
                    float(row[i])
                    numeric = True
                except Exception:
                    pass
                if tags[i] == 'id':
                    line = ('<record id="%s" model="%s">\n'
                            % (row[id_position], csv_file[:-4]))
                elif '/' in tags[i] or ':' in tags[i]:
                    # relationnal fields
                    xml_suffix = convert_relationnal_field2xml(tags[i], row[i])
                    line = '%s%s\n' % (begin, xml_suffix)
                elif char:
                    # numeric ghar field
                    line = '%s%s">%s</field>\n' % (begin, tags[i][:-5], row[i])
                elif numeric or row[i] in BOOLEAN:
                    line = '%s%s" eval="%s"/>\n' % (begin, tags[i], row[i])
                else:
                    # basic fields
                    line = '%s%s">%s</field>\n' % (begin, tags[i], row[i])
                if row[i] or tags[i] == 'id':
                    xml_data.write(line)
            xml_data.write('</record>' + "\n\n")
        row_num += 1
    xml_data.write(ERP_FOOTER)
    xml_data.close()
    print "'%s' file has been created from '%s'\n" % (xml_file, csv_file)


def process():
    global NOUPDATE
    if check_arg('help'):
        help()
        return True
    if len(sys.argv) == 1:
        print 'Arguments should be provided with this script'
        help()
        return True
    if check_arg('update'):
        NOUPDATE = 0
    if check_arg('all'):
        for csv_file in glob.glob('*.csv'):
            convert_file(csv_file)
    else:
        number = 0
        for csv_file in sys.argv:
            if csv_file[-4:] in ('.csv', '.CSV'):
                convert_file(csv_file)
                number += 1
        if number == 0:
            print "No csv file provided: see Help for more information"
            print "---------------------------------------------------"
            help()


if __name__ == '__main__':
    process()
