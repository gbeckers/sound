Supported Formats
=================

For reading and writing audio data *Sound* depends on the Python library 
*SoundFile*, which in turn depends on the C library *libsndfile*. In 
addition, *Sound* supports reading and writing in Darr format, which is 
a format for scientific numeric data. The latter is recommended for easy 
readability of data outside of the world of audio (such as tools for 
scientific computing) or when very efficient read access to very large files 
(that do not fit in RAM) is required.

Audio Formats and Encodings
---------------------------

The table below is based on *libsndfile*, and additionally indicates the
default encodings for each format as used by *Sound*.

+-----------+------+----+-----+-----+------+-----+-------+------+------+-------+------+-----+-----+-----+-----+------+-----+-----+-----+-----+-----+-----+-------+-----+----+
|           | AIFF | AU | AVR | CAF | FLAC | HTK | IRCAM | MAT4 | MAT5 | MPC2K | NIST | OGG | PAF | PVF | RAW | RF64 | SD2 | SDS | SVX | VOC | W64 | WAV | WAVEX | WVE | XI |
+===========+======+====+=====+=====+======+=====+=======+======+======+=======+======+=====+=====+=====+=====+======+=====+=====+=====+=====+=====+=====+=======+=====+====+
| ALAC_16   |      |    |     | +   |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     |     |     |       |     |    |
| ALAC_20   |      |    |     | +   |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     |     |     |       |     |    |
| ALAC_24   |      |    |     | +   |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     |     |     |       |     |    |
| ALAC_32   |      |    |     | +   |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     |     |     |       |     |    |
| ALAW      | +    | +  |     | +   |      |     | +     |      |      |       | +    |     |     |     | +   | +    |     |     |     | +   | +   | +   | +     | *   |    |
| DOUBLE    | +    | +  |     | +   |      |     |       | +    | +    |       |      |     |     |     | +   | +    |     |     |     |     | +   | +   | +     |     |    |
| DPCM_16   |      |    |     |     |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     |     |     |       |     | *  |
| DPCM_8    |      |    |     |     |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     |     |     |       |     | +  |
| DWVW_12   | +    |    |     |     |      |     |       |      |      |       |      |     |     |     | +   |      |     |     |     |     |     |     |       |     |    |
| DWVW_16   | +    |    |     |     |      |     |       |      |      |       |      |     |     |     | +   |      |     |     |     |     |     |     |       |     |    |
| DWVW_24   | +    |    |     |     |      |     |       |      |      |       |      |     |     |     | +   |      |     |     |     |     |     |     |       |     |    |
| FLOAT     | +    | +  |     | +   |      |     | *     | *    | *    |       |      |     |     |     | *   | +    |     |     |     |     | +   | +   | +     |     |    |
| G721_32   |      | +  |     |     |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     |     | +   |       |     |    |
| G723_24   |      | +  |     |     |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     |     |     |       |     |    |
| GSM610    | +    |    |     |     |      |     |       |      |      |       |      |     |     |     | +   |      |     |     |     |     | +   | +   |       |     |    |
| IMA_ADPCM | +    |    |     |     |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     | +   | +   |       |     |    |
| MS_ADPCM  |      |    |     |     |      |     |       |      |      |       |      |     |     |     |     |      |     |     |     |     | +   | +   |       |     |    |
| PCM_16    | +    | +  | *   | +   | +    | *   | +     | +    | +    | *     | +    |     | +   | +   | +   | +    | +   | +   | *   | *   | +   | +   | +     |     |    |
| PCM_24    | *    | *  |     | *   | *    |     |       |      |      |       | *    |     | *   |     | +   | +    | *   | *   |     |     | *   | *   | *     |     |    |
| PCM_32    | +    | +  |     | +   |      |     | +     | +    | +    |       | +    |     |     | *   | +   | +    | +   |     |     |     | +   | +   | +     |     |    |
| PCM_S8    | +    | +  | +   | +   | +    |     |       |      |      |       | +    |     | +   | +   | +   |      | +   | +   | +   |     |     |     |       |     |    |
| PCM_U8    | +    |    | +   |     |      |     |       |      | +    |       |      |     |     |     | +   | +    |     |     |     | +   | +   | +   | +     |     |    |
| ULAW      | +    | +  |     | +   |      |     | +     |      |      |       | +    |     |     |     | +   | +    |     |     |     | +   | +   | +   | +     |     |    |
| VORBIS    |      |    |     |     |      |     |       |      |      |       |      | *   |     |     |     |      |     |     |     |     |     |     |       |     |    |
| VOX_ADPCM |      |    |     |     |      |     |       |      |      |       |      |     |     |     | +   |      |     |     |     |     |     |     |       |     |    |
+-----------+------+----+-----+-----+------+-----+-------+------+------+-------+------+-----+-----+-----+-----+------+-----+-----+-----+-----+-----+-----+-------+-----+----+

*Format codes*: AIFF: AIFF (Apple/SGI), AU: AU (Sun/NeXT), AVR: AVR (Audio Visual Research), CAF: CAF (Apple Core Audio File), FLAC: FLAC (Free Lossless Audio Codec), HTK: HTK (HMM Tool Kit), IRCAM: SF (Berkeley/IRCAM/CARL), MAT4: MAT4 (GNU Octave 2.0 / Matlab 4.2), MAT5: MAT5 (GNU Octave 2.1 / Matlab 5.0), MPC2K: MPC (Akai MPC 2k), NIST: WAV (NIST Sphere), OGG: OGG (OGG Container format), PAF: PAF (Ensoniq PARIS), PVF: PVF (Portable Voice Format), RAW: RAW (header-less), RF64: RF64 (RIFF 64), SD2: SD2 (Sound Designer II), SDS: SDS (Midi Sample Dump Standard), SVX: IFF (Amiga IFF/SVX8/SV16), VOC: VOC (Creative Labs), W64: W64 (SoundFoundry WAVE 64), WAV: WAV (Microsoft), WAVEX: WAVEX (Microsoft), WVE: WVE (Psion Series 3), XI: XI (FastTracker 2)

*Encoding codes*: ALAC_16: 16 bit ALAC, ALAC_20: 20 bit ALAC, ALAC_24: 24 bit ALAC, ALAC_32: 32 bit ALAC, ALAW: A-Law, DOUBLE: 64 bit float, DPCM_16: 16 bit DPCM, DPCM_8: 8 bit DPCM, DWVW_12: 12 bit DWVW, DWVW_16: 16 bit DWVW, DWVW_24: 24 bit DWVW, FLOAT: 32 bit float, G721_32: 32kbs G721 ADPCM, G723_24: 24kbs G723 ADPCM, GSM610: GSM 6.10, IMA_ADPCM: IMA ADPCM, MS_ADPCM: Microsoft ADPCM, PCM_16: Signed 16 bit PCM, PCM_24: Signed 24 bit PCM, PCM_32: Signed 32 bit PCM, PCM_S8: Signed 8 bit PCM, PCM_U8: Unsigned 8 bit PCM, ULAW: U-Law, VORBIS: Vorbis, VOX_ADPCM: VOX ADPCM

Darr encodings
--------------

Darr supports any numeric Numpy dtype. Generally I would recommend 'float32'.
For audio compatibility, 'int16', 'int32' and 'int64' would make sense for
direct compatibility with PCM encodings, while 'float32'  and 'float64' would
make sense for compatibility with FLOAT and DOUBLE encodings.