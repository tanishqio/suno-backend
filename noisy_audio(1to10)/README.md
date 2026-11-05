# Digit_Spoken_Hindi_IndianEnglish

## Description
This data-set consists of around 3700 spoken digits from 1 - 10, both in Hindi and Indian English, in .wav file format. The spoken data for each digit is saved in three folders namely 'Female' (spoken by females), 'Male' (spoken by males) and 'Unspecified' (contains digits spoken by both females and males). 

The data was collected as a part of the coursework on the following:
**BITS F-312 Neural Networks**, Department of Computer Science, Birla Insititue of Technology and Science, K.K. Birla Goa Campus, Goa, India 403 726

## Nomenclature
Each data file is named as follows : 
* {id}\_{digit}\_{language}\_{gender} --- if gender is specified
* {id}\_{digit}\_{language}\_{unspecified} --- if gender is not specified

## Credits:
BITS F312 Class of Semester-I, AY 2020-21
(please follow this link for names of all contributors)

All data was collected with due consent of all contributors to the project on the condition of anonyminity. Gender information is provided in some cases, with due consent of the contributors. However, where gender information was not provided, the data is kept in the subfolder 'unspecified'.

## APIs included
* getSpectrogram(pathTofile) - Finds the spectrogram of the sound file.
* removeSilence(path_to_file, silence_threshold = -35.0, iter_size=10) - Removes silence present in the beginning & end from audio clips 
* removeNoise(path_to_file) - Removes background noise in the audio clip
* fix_wave(path_in, path_out) - repairs corrupt wav files.

## Libraries for reading .wav files in Python
###### Pydub:
  from pydub import AudioSegment
  
  wav_file = AudioSegment.from_file(file = pathToFile, format = "wav")  
###### Wave:
  import wave
  
  wavefile = wave.open(pathToFile, 'r')
###### Scipy:
  from scipy.io import wavfile
  
  wavfile.read(pathTofile)
###### Librosa:
  import librosa
  
  x,_ = librosa.load(pathTofile, sr=16000)
###### Audioread:
  import audioread
  
  audioread.ffdec.FFmpegAudioFile(p)

## Useful links to work on Speech Recognition


