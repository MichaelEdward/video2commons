#! /usr/bin/python
# -*- coding: UTF-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

"""Wrapper around youtube-dl."""

import os
import youtube_dl  # https://github.com/rg3/youtube-dl


def download(
    url, ie_key, formats, subtitles, outputdir,
    statuscallback=None, errorcallback=None
):
    """Download a video from url to outputdir."""
    outputdir = os.path.abspath(outputdir)
    statuscallback = statuscallback or (lambda text, percent: None)
    errorcallback = errorcallback or (lambda text: None)
    outtmpl = outputdir + '/dl.%(ext)s'

    params = {
        'format': formats,
        'outtmpl': outtmpl,
        'writedescription': True,
        'writeinfojson': True,
        'writesubtitles': subtitles,
        'writeautomaticsub': False,
        'allsubtitles': True,
        'subtitlesformat': 'srt/ass/vtt/best',
        'cachedir': '/tmp/',
        'noplaylist': True,  # not implemented in video2commons
        'postprocessors': [{
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'srt',
        }],
        'max_filesize': 5 * (1 << 30),
        'retries': 10,
        'fragment_retries': 10,
        'prefer_ffmpeg': True,  # avconv do not have srt encoder
        'prefer_free_formats': True
    }

    def progresshook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            percentage = int(100.0 * d['downloaded_bytes'] / total)\
                if total else None
            statuscallback(
                'Downloading to ' + (d['tmpfilename'] or d['filename']),
                percentage
            )
        elif d['status'] == 'finished':
            statuscallback('Postprocessing...', -1)
        elif d['status'] == 'error':
            errorcallback('Error raised by YoutubeDL')

    statuscallback('Creating YoutubeDL instance', -1)
    dl = youtube_dl.YoutubeDL(params)
    dl.add_progress_hook(progresshook)

    statuscallback('Preprocessing...', -1)
    info = dl.extract_info(url, download=True, ie_key=ie_key)

    filename = outtmpl % {'ext': info['ext']}
    if not os.path.isfile(filename):
        # https://github.com/rg3/youtube-dl/issues/8349
        filename = outtmpl % {'ext': 'mkv'}
        assert os.path.isfile(filename), \
            'Failed to determine the path of the downloaded video. ' + \
            'Is the video too large?'

    ret = {
        'extractor': ie_key,
        'subtitles': {},
        'target': filename,
    }

    for key in info.get('subtitles', {}):
        # Postprocesed: converted to srt
        filename = outtmpl % {'ext': key + '.srt'}
        if os.path.isfile(filename):
            ret['subtitles'][key] = filename

    return ret
