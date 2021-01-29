from __future__ import unicode_literals

encodings = {
    'ABC': 'cp1258',
    'ALT': 'cp866',
    'BIG5': 'big5',
    'EUC_CN': 'euccn',
    'EUC_JIS_2004': 'euc_jis_2004',
    'EUC_JP': 'euc_jp',
    'EUC_KR': 'euc_kr',
    'GB18030': 'gb18030',
    'GBK': 'gbk',
    'ISO_8859_1': 'iso8859_1',
    'ISO_8859_2': 'iso8859_2',
    'ISO_8859_3': 'iso8859_3',
    'ISO_8859_5': 'iso8859_5',
    'ISO_8859_6': 'iso8859_6',
    'ISO_8859_7': 'iso8859_7',
    'ISO_8859_8': 'iso8859_8',
    'ISO_8859_9': 'iso8859_9',
    'ISO_8859_10': 'iso8859_10',
    'ISO_8859_13': 'iso8859_13',
    'ISO_8859_14': 'iso8859_14',
    'ISO_8859_15': 'iso8859_15',
    'ISO_8859_16': 'iso8859_16',
    'JOHAB': 'johab',
    'KOI8': 'koi8_r',
    'KOI8R': 'koi8_r',
    'KOI8U': 'koi8_u',
    'LATIN1': 'iso8859_1',
    'LATIN2': 'iso8859_2',
    'LATIN3': 'iso8859_3',
    'LATIN4': 'iso8859_4',
    'LATIN5': 'iso8859_9',
    'LATIN6': 'iso8859_10',
    'LATIN7': 'iso8859_13',
    'LATIN8': 'iso8859_14',
    'LATIN9': 'iso8859_15',
    'LATIN10': 'iso8859_16',
    'Mskanji': 'cp932',
    'ShiftJIS': 'cp932',
    'SHIFT_JIS_2004': 'shift_jis_2004',
    'SJIS': 'cp932',
    'SQL_ASCII': 'ascii',   # XXX this is wrong: SQL_ASCII means "no
                            # encoding" we should fix the unicode
                            # typecaster to return a str or bytes in Py3
    'TCVN': 'cp1258',
    'TCVN5712': 'cp1258',
    'UHC': 'cp949',
    'UNICODE': 'utf_8',
    'UTF8': 'utf_8',
    'VSCII': 'cp1258',
    'WIN': 'cp1251',
    'WIN866': 'cp866',
    'WIN874': 'cp874',
    'WIN932': 'cp932',
    'WIN936': 'gbk',
    'WIN949': 'cp949',
    'WIN950': 'cp950',
    'WIN1250': 'cp1250',
    'WIN1251': 'cp1251',
    'WIN1252': 'cp1252',
    'WIN1253': 'cp1253',
    'WIN1254': 'cp1254',
    'WIN1255': 'cp1255',
    'WIN1256': 'cp1256',
    'WIN1257': 'cp1257',
    'WIN1258': 'cp1258',
    'Windows932': 'cp932',
    'Windows936': 'gbk',
    'Windows949': 'cp949',
    'Windows950': 'cp950',

    # these are missing from Python:
    # 'EUC_TW': ???
    # 'MULE_INTERNAL': ???
}

def normalize(name):
    """Normalize the name of an encoding."""
    return name.replace('_', '').replace('-', '').upper()

# Include a normalized version of the encodings above
# (all uppercase, no - or _)
for k, v in list(encodings.items()):
    encodings[normalize(k)] = v

del k, v

