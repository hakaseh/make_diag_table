#!/usr/bin/env python
"""

Generate MOM5 diag_table file

The MOM diag_table format is defined here:
https://github.com/mom-ocean/MOM5/blob/master/src/shared/diag_manager/diag_table.F90
and some of the available diagnostics are listed here:
https://raw.githubusercontent.com/COSIMA/access-om2/master/MOM_diags.txt
https://github.com/COSIMA/access-om2/wiki/Technical-documentation#MOM5-diagnostics-list

"""

from __future__ import print_function
import yaml

def set_filename(**kwargs):
    # define standardised filename as in https://github.com/COSIMA/access-om2/issues/185
    adjectives = {'years': 'yearly',
                   'months': 'monthly',
                   'days': 'daily',
                   'hours': 'hourly',
                   'minutes': 'minutely',
                   'seconds': 'secondly'}
    fn = kwargs['file_name']
    if isinstance(fn, list):
        if kwargs['reduction_method'] == 'average':  # omit 'average' from filename
            fn = [v for v in fn if v != 'reduction_method']
        fn = [str(kwargs[k]) for k in fn]
        fn = [adjectives.get(v, v) for v in fn]
        return kwargs['file_name_separator'].join(fn)
    else:
        return fn

def strout(v):
    if isinstance(v, str):
        return '"' + v + '"'
    else:
        return str(v)

indata = yaml.load(open('diag_table_source.yaml', 'r'))
outstrings = []

# global section
d = indata['global_defaults']['global_section']
outstrings.append(d['title'])
outstrings.append(' '.join([str(x) for x in d['base_date']]))
outstrings.append('')
outstrings.append('#########################################################################################################')
outstrings.append('#                                                                                                       #')
outstrings.append('# DO NOT EDIT! Instead, edit diag_table_source.yaml and run make_diag_table.py to re-generate this file #')
outstrings.append('#                                                                                                       #')
outstrings.append('#########################################################################################################')

filenames = {}

# interleaved file and field sections
for k, grp in indata['diag_table'].items():
    # ensure expected entries are present in group
    print(grp)
    if grp is None:
        grp = dict()
    grp['defaults'] = grp.get('defaults', dict())
    if grp['defaults'] is None:
        grp['defaults'] = dict()
    grp['defaults']['file_section'] = grp['defaults'].get('file_section', dict())
    grp['defaults']['field_section'] = grp['defaults'].get('field_section', dict())
    grp['fields'] = grp.get('fields', dict())
    if grp['fields'] is None:
        grp['fields'] = dict()

    outstrings.append('')
    outstrings.append('# '+k)

    for field_name, field_dict in grp['fields'].items():
        if field_dict is None:
            field_dict = {}
        # combine field_dict with defaults into one dict f
        f = {**indata['global_defaults']['file_section'],
             **indata['global_defaults']['field_section'],
             **grp['defaults']['file_section'],
             **grp['defaults']['field_section'],
             **field_dict,
             'field_name': field_name}
        if f['output_name'] is None:
            f['output_name'] = f['field_name']
        fname = set_filename(**f)
        if fname not in filenames:  # to ensure that each filename is specified once only
            fnameline = [ fname, f['output_freq'], f['output_freq_units'],
                         f['file_format'], f['time_axis_units'], f['time_axis_name']]
            if 'new_file_freq' in f:
                if f['new_file_freq'] != None:
                    fnameline.extend([f['new_file_freq'], f['new_file_freq_units']])
                    if 'start_time' in f:
                        if f['start_time'] != None:
                            fnameline.append(' '.join([str(x) for x in f['start_time']]))
                            if 'file_duration' in f:
                                if f['file_duration'] != None:
                                    fnameline.extend([f['file_duration'], f['file_duration_units']])
            outstrings.append(', '.join([strout(v) for v in fnameline]))
            filenames[fname] = None
        if f['reduction_method'] == 'snap':
            f['reduction_method'] = 'none'
        fieldline = [f['module_name'], f['field_name'], f['output_name'], fname,
                     f['time_sampling'], f['reduction_method'],
                     f['regional_section'], f['packing']]
        outstrings.append(', '.join([strout(v) for v in fieldline]))

with open('diag_table_TEST', 'w') as f:
    for line in outstrings:
        f.write('%s\n' % line)
