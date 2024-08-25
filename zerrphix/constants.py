from __future__ import unicode_literals, division, absolute_import, print_function

# Modified from filebot ReleaseInfo.properties https://github.com/filebot/filebot

# patterns for all video sources
pattern_video_source = r"""\b(CAMRip|CAM|PDVD|TS|TELESYNC|PDVD|PTVD|PPVRip|Screener|SCR|SCREENER|DVDSCR|DVDSCREENER|BDSCR|R4|R5(?:.?LINE)?|DVD|DVD5|DVD9|DVDRip|DVDR|TVRip|DSR|(?:P|H|S)DTV|HDTVRip|(?:DVB|DTH)(?:Rip)?|VODR(?:ip)?|B(?:D|R)(?:.?Rip)?|Blu.?Ray|BD(?:R|25|50)|3D.?BluRay|3DBD|(?:BD)?(?:Remux)|BR.?(?:Scr|Screener)|HD(?:DVD|Rip)|WorkPrint|VHS|VCD|TELECINE|WEB.?(?:Rip|DL|Cap)|ithd|iTunesHD|Laserdisc|NetflixHD|VHSRip|LaserRip|URip|UnknownRip|MicroHD)\b"""

pattern_video_source_dict = {'VHS': r"""\bVHS(?:Rip)?\b""",
                             'VCD': r"""\bS?VCD\b""",
                             'TV': r"""\b(?:P|S)DTV|(?:DVB|DTH)(?:Rip)?|TV(?:Rip)?|DSR\b""",
                             'DVD': r"""\bDVDSCR|DVDSCREENER|DVD|DVD5|DVD9|DVDRip|DVDR|DVD.?Rip\b""",
                             'HDTV': r"""\bHDTV(?:Rip)?\b""",
                             'WEB': r"""\bWEB.?(?:Rip|DL|Cap)|NetflixHD|iTunesHD\b""",
                             'BR': r"""\bB(?:D|R)(?:.?Rip)?|Blu.?Ray|BD(?:R|25|50)|3D.?BluRay|3DBD|BDRemux|BR.?(?:Scr|Screener)|BDSCR\b""",
                             'HDDVD': r"""\bHDDVD(?:.?Rip)?\b"""}

# patterns for all video tags
pattern_video_tags = r"""\b((?:Ultimate.)?(?:Director.?s|Theatrical|Remastered|Extended|Ultimate|Final|Uncensored|Unrated|Rogue|Collectors|Special|Despeciali(?:z|s)ed)(?:.Deluxe)?(?:.(?:Cut|Edition|Version))|Extended|Remastered|Uncensored|Unrated|Uncut|IMAX)\b"""

# patterns for stereoscopic 3D tags
pattern_video_s3d = r"""\b(?:3D(?:[^\w]|_)?)?(?:H|HALF|F|FULL)?(?:(?:[^\w]|_)?(?:SBS|TAB|OU))\b"""

# patterns for repack tags
pattern_video_repack = r"""\bREPACK|PROPER\b"""

# patterns for all subtitle tags
pattern_subtitle_tags = r"""\b((?:(?:forced|HI|SDH|idx|srt)(?:.subtitles)?)|subtitles|Multisub)\b"""

# additional release info patterns
pattern_video_format = r"""\b(DivX|Xvid|AVC|(x|h)[.]?(?:264|265)|HEVC|3ivx|PGS|MP[E]?G[45]?|MP[34]|(?:FLAC|AAC|AC3|DD|MA).?[2457][.]?[01]|[26]ch|(?:Multi.)?DTS(?:.HD)?(?:.MA)?|FLAC|AAC|AC3|TrueHD|Atmos|[M0]?(?:720|1080)[pi]|(?<=[-])(?:720|1080|2D|3D)|(?:10|8).?bit|(?:24|23\.97|25|29\.97|30|50|59\.94|60)FPS|Hi10[P]?|[a-z]{2,3}.(?:2[.]0|5[.]1)|CD\d+|[257].[10])\b"""

pattern_video_res_dict = {288: r"""\b288(?:p|i)?\b""",
                          480: r"""\b480(?:p|i)?\b""",
                          576: r"""\b576(?:p|i)?\b""",
                          720: r"""\b720(?:p|i)?\b""",
                          1080: r"""\b1080(?:p|i)?\b""",
                          1536: r"""\b1536(?:p|i)?\b""",
                          3072: r"""\b3072(?:p|i)?\b"""}

# Languages
pattern_language = r"""EN|FR|ES|PL|DE"""

# for tv perhaps needs all this?
# pattern_video_format: r"""DivX|Xvid|AVC|(x|h)[.]?(264|265)|HEVC|3ivx|PGS|MP[E]?G[45]?|MP[34]|(FLAC|AAC|AC3|DD|MA).?[2457][.]?[01]|[26]ch|(Multi.)?DTS(.HD)?(.MA)?|FLAC|AAC|AC3|TrueHD|Atmos|[M0]?(720|1080)[pi]|(?<=[-])(720|1080|2D|3D)|10.?bit|(24|30|60)FPS|Hi10[P]?|[a-z]{2,3}.(2[.]0|5[.]1)|(19|20)[0-9]+(.)S[0-9]+(?!(.)?E[0-9]+)|(?<=\\d+)v[0-4]|CD\\d+"""

# disk folder matcher
pattern_diskfilefolder = r"""(?P<diskfilefolder>BDMV|HVDVD_TS|VIDEO_TS|S?VCD|MovieObject\.bdmv|VIDEO_TS\.VOB)"""

pattern_unkown = r"""OAR"""

# disk file matcher
# pattern_diskfile = r"""MovieObject.bdmv|VIDEO_TS.VOB|VTS_[0-9]+_[0-9]+.VOB"""

pattern_ignore_folders = r"""@eadir"""

diskfilefolder_types_dict = {'VCD': 10,
                             'SVCD': 15,
                             'VIDEO_TS': 20,
                             'VIDEO_TS.VOB': 25,
                             'HDDVD_TS': 30,
                             'BDMV': 35,
                             'MOVIEOBJECT.BDMV': 36}

diskfilefolder_cdoec_type_dict = {'VCD': 1,
                             'SVCD': 2}

container_type_dict = {
    'avi': {'avi'},
    'bdav': {'m2ts', 'mts'},
    'matroska': {'mkv'},
    'mp4': {'mp4'},
    'mpeg_ps': {'mpg', 'mpeg', 'm2p', 'ps', 'vob'},
    'mpeg_ts': {'ts', 'tsv', 'tsa'},
    'qt': {'mov', 'qt'},
    'wm': {'wmv', 'asf', 'wm'},
    'realvideo': {'rm', 'rmvb'}
}

min_film_filsize = 209715200

military_time_regex = r'''^([01]\d|2[0-3]):?([0-5]\d)$'''

dune_supported_images = ['jpg', 'jpeg', 'bmp', 'gif', 'png']

# system file pattern
# pattern.system.files: [.@][a-z]+|bin|initrd|opt|sbin|var|dev|lib|proc|sys|var.defaults|etc|lost.found|root|tmp|etc.defaults|mnt|run|usr|System.Volume.Information

logo_b64 = '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byDwTPP5/KsVQEAAEBAABAQAAQFAQABAQAAQEAAEBAABAUBAAEBAABAQAAQEAAEBQEAAQEAAEBAABAQAAQFAQABAQAAQEAAEBAABAQABAUBAABAQAAQEAAEBAAEBQEAAEBAABAQAAQEAAQFAQAAQEAAEhNdrMBjsrQA8SE1wXlVV3ed53ruGs47H45Akya3dojtPKXgD4ZlWq9U7KwACAoCAACAgAAgIAAICAAICgIAAICAACAgAAgIAAgKAgAAgIAAICAACAgACAoCAACAgAAgIAAICAAICgIAAICAACAgAAgIAAgKAgAAgIAAICAACAgACAoCAACAgAAgIAIQQQmoCjlWWZWYFLklRFNsYo+fSGwgAAgKAgACAgAAgIAAICAACAoCAAICAACAgAAgIAAICgIAAgIAAICAACAgAAgKAgACAgAAgIAAICAACAoCAAICAACAgAAgIAAICAAICgIAAICAACAgAAgIAAgKAgAAgIAAICAACAgACAoCAACAgAAgIAAICAP+QhBAOZgDAGwgAAgKAgAAgIAAgIAAICAACAoCAACAgACAgAAgIAAICgIAAICAAICAACAgAAgKAgAAgIAAgIAAICAACAoCAACAgACAgAAgIAAICgIAAICAAICAACAgAAgKAgAAgIAAgIAAICAACAoCAACAgACAgAAgIAAICgIAAgIAAICAACAgAAgKAgACAgAAgIAAICAACAoCAAICAACAgAAgIAAICgIAAgIAAICAACAgAAgKAgACAgAAgIAAICAACAoCAAICAACAgAAgIAAICgIAAgIAAICAACAgAAgIAAgKAgAAgIAAICACv0l8AAAD//wMAUJxd6hTCiI8AAAAASUVORK5CYII='