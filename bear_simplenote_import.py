# encoding=utf-8
# python3.6
# bear_simplenote_import.py
# Developed with Visual Studio Code with MS Python Extension.

'''
# Text import to Bear from Simlenote local xml database  
Version 1.0.0 - 2018-02-11 at 20:38 EST
github/rovest, rorves@twitter

Extracts from simplenote's local xml-database file,
and should work with simplenote.app Version 1.2 (1200)from Mac appstore installed.
Open simplenote.app and let it finish any pending sync before running this script.

* Import Simplenotes directly into Bear.
* Or export to temp as files: `simplenote_id_#.txt`,  
with both cre- and mod-dates from Simplenote :)  
* And Then import manually in Bear with option:  
`Keep original creation and modification date` checked.

NOTE! Make sure nvALT is not active!

NOTE! Does not delete old exports, so if running this several times, 
you should delete old export manually before running this second time!
'''

direct_import = False   # If `True`, cre and mod dates are not preserved, but notes are 
                        # imported directly into Bear.
                        # If `False`, exported to temp as files: `id-number.txt`, 
                        # and Simplenote cre- and mod-dates are both set to files :)
                        # Then import manually in Bear with option: 
                        # `Keep original creation and modification date` checked.

simplenote_tag = '#simplenote'      # Root for nested tags, and applied to all notes without tags
use_as_root_for_other_tags = True   # If False, tags will not appear under `simplenote_tag`
simplenote_tag2 = '#.simplenote import#'    # Flat tag to all notes that can easily be 
                                            # deleted in Bear after successful import
include_trash = False
trash_tag = '#.simplenote/trashed'

import datetime
import re
import subprocess
import urllib.parse
import os
import time
import shutil
import fnmatch
import json
import xml.etree.ElementTree as ET

HOME = os.getenv('HOME', '')
simplenote_db = os.path.join(HOME, 'Library/Containers/com.automattic.SimplenoteMac/Data/Library/Simplenote/Simplenote.storedata')
export_path = os.path.join(HOME, 'simple_to_bear_notes')


def main():    
    if not os.path.exists(export_path):
        os.makedirs(export_path)
    get_simplenotes()
    if not direct_import:
        subprocess.call(['open', export_path])
    

def get_simplenotes():    
    xml_text = read_file(simplenote_db)
    xml_doc = ET.fromstring(xml_text)
    xnotes = xml_doc.findall(".//object[@type='NOTE']")
    for xnote in xnotes:
        deleted = xnote.find("attribute[@name='deleted']").text == '1'
        if deleted and not include_trash:
            continue
        note_id = xnote.attrib['id']
        markdown = xnote.find("attribute[@name='markdown']").text == '1'
        pinned = xnote.find("attribute[@name='pinned']").text == '1'
        modificationdate = xnote.find("attribute[@name='modificationdate']").text
        creationdate = xnote.find("attribute[@name='creationdate']").text
        raw_content = xnote.find("attribute[@name='content']").text
        tags = xnote.find("attribute[@name='tags']").text
        taglist = json.loads(tags)
        if raw_content is not None:
            # Fix xml unicode escaped '< > & \':
            # (other things like emojis are not fixed here ;(
            content = raw_content.replace('\\u3c00', '<').replace('\\u3e00', '>').replace('\\u2600', '&').replace('\\\\', '\\')

        if deleted:
            text_tags = trash_tag
        else:
            bear_taglist = []
            if pinned:
                bear_taglist.append('#.pinned')
            if markdown:
                if simplenote_tag != '':
                    bear_taglist.append(f'{simplenote_tag}/_markdown')
                else:
                    bear_taglist.append('#.markdown')
            if simplenote_tag2 != '':
                # Add simplenote_tag2 to all notes:
                bear_taglist.append(simplenote_tag2)
            if taglist:
                # Notes with tags:
                for tag in taglist:
                                    # Notes with tags:
                    if use_as_root_for_other_tags and simplenote_tag != '':
                        bear_tag = f'{simplenote_tag}/{tag}'
                    else:
                        bear_tag = f'#{tag}'
                    if ' ' in bear_tag: bear_tag += "#"
                    bear_taglist.append(bear_tag)
            elif simplenote_tag != '':
                # Add simplenote_tag if no other tags
                bear_taglist.append(simplenote_tag)
            text_tags = ' '.join(bear_taglist)
        note_text = content + '\n\n' +  text_tags + '\n'
        make_bear_note(note_text, creationdate, modificationdate, note_id)


def make_bear_note(note_text, creationdate, modificationdate, note_id):
    note_lines = note_text.splitlines()
    if not note_lines[0].startswith('#'):
        note_lines[0] = f'# {note_lines[0]}'
    if direct_import:
        x_command = 'bear://x-callback-url/create?show_window=no&text=' 
        x_command_text = x_command + urllib.parse.quote('\n'.join(note_lines))
        subprocess.call(["open", x_command_text])
        time.sleep(.2)
    else:
        file_name = os.path.join(export_path, f'simplenote_id_{note_id}.txt')
        write_file(file_name, '\n'.join(note_lines))
        # By setting creationdate first and modificationdate second,
        # both dates are set with the same `os.utime` command! :)
        set_file_date(file_name, creationdate)
        set_file_date(file_name, modificationdate)

        # Import to Bear by opening files does not keep file cre and mod dates:
        # So manual import of exporthed simplenotes must be done instead ;( 
        # subprocess.call(['open', '-a', '/applications/bear.app', file_name])
        # time.sleep(.2)
        

def read_file(file_name):
    with open(file_name, "r", encoding='utf-8') as f:
        file_content = f.read()
    return file_content


def write_file(filename, file_content):    
    with open(filename, "w", encoding='utf-8') as f:
        f.write(file_content)


def set_file_date(filename, ts_string):
    ts_fl = float(ts_string)
    ts_int = int(ts_fl)
    ts = dt_conv(ts_int)
    os.utime(filename, (-1, ts))


def dt_conv(dtnum):
    # Formula for date offset based on trial and error:
    # Not tested for different time-zones!
    hour = 3600 # seconds
    year = 365.25 * 24 * hour
    offset = year * 31 + hour * 6
    return dtnum + offset


if __name__ == '__main__':
    main()
