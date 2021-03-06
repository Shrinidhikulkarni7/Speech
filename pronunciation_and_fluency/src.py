import pydub
from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr
from Tkinter import *
import tkSnack
import pickle
from gtts import gTTS
import math
import os
import glob
import time
import xlwt
import soundfile as sf


def toWAV(srcfile):
    """
    Module converts .mp3 files to .wav file
    :param inputfile: path to mp3 file
    :return:
    """
    sound = pydub.AudioSegment.from_file(srcfile)
    sound.export("src.wav", format="wav")
    inputfile = os.path.abspath("src.wav")
    return inputfile


def toSpeech(t):
    """
    Module to convert text to speech
    :param t:text generated by speechToText module(content spoken in the extempore)
    :return: audio file used for comparison against extempore audio to generate pronunciation score
    """
    tts = gTTS(text=t, lang ='en')
    tts.save("hello.wav")


def speechToText(inputfile):
    """
    Module to convert the content spoken in the extempore to text
    :param inputfile: path to the extempore audio file
    result:transcription of speech
    """
    sound1 = AudioSegment.from_file(inputfile, format="wav")
    thresh = sound1.dBFS + 0.5 * sound1.dBFS
    chunks = split_on_silence(sound1, min_silence_len=600, silence_thresh=thresh)
    i = 0
    for i, chunk in enumerate(chunks):
            chunk.export("D:\Speech\pronunciation_and_fluency\sound\chunk{0}.wav".format(i), format="wav")

    str = ""
    r = sr.Recognizer()
    for i in range(0, len(chunks)):
        with sr.WavFile("D:\Speech\pronunciation_and_fluency\sound\chunk{0}.wav".format(i)) as source:
            audio = r.record(source)  # extract audio data from the file
        f = sf.SoundFile("D:\Speech\pronunciation_and_fluency\sound\chunk{0}.wav".format(i))
        seconds = float(format(len(f) / f.samplerate))
        if seconds < 1.5:
            continue
        elif seconds > 15:
            sound2=AudioSegment.from_file("D:\Speech\pronunciation_and_fluency\sound\chunk{0}.wav".format(i), format="wav")
            slices = split_on_silence(sound2, min_silence_len=400, silence_thresh=thresh)
            i = 0
            for j, slice in enumerate(slices):
                slice.export("D:\Speech\pronunciation_and_fluency\sound\slice{0}.wav".format(j), format="wav")
            r = sr.Recognizer()
            for j in range(0, len(slices)):
                with sr.WavFile("D:\Speech\pronunciation_and_fluency\sound\slice{0}.wav".format(j)) as source:
                    audio = r.record(source)  # extract audio data from the file
                f = sf.SoundFile("D:\Speech\pronunciation_and_fluency\sound\slice{0}.wav".format(j))
                seconds = float(format(len(f) / f.samplerate))
                if seconds < 1.5:
                    continue
                try:
                    newstr = r.recognize_google(audio)  # recognize speech using Google Speech Recognition
                    str = str + newstr
                except sr.UnknownValueError: # background noise
                    return 0
                except LookupError:  # speech is unintelligible
                    return -1
                except sr.RequestError:
                    return -2

        else:
            try:
                newstr = r.recognize_google(audio)  # recognize speech using Google Speech Recognition
                str = str + newstr
            except sr.UnknownValueError:  # background noise
                return 0
            except LookupError:  # speech is unintelligible
                return -1
            except sr.RequestError:
                return -2
    toSpeech(str)
    return 1


def toMono(inputfile):
    """
    Module to convert extempore audio from stereo to mono for further processing
    :param inputfile: path to extempore audio file
    :return: audio file converted to mono
    """
    inputfile1 = AudioSegment.from_wav(inputfile)
    inputfile1 = inputfile1.set_channels(1)
    inputfile1.export(inputfile, format="wav")


def findPitch(inputfile):
    """
    Module to generate pitch values for audio files
    :param inputfile: path to extempore file or the sample file generated by the system
    :return: list of pitch values
    """
    root = Tk()
    tkSnack.initializeSnack(root)
    mySound = tkSnack.Sound()
    mySound = tkSnack.Sound(load=inputfile)
    data = mySound.pitch()
    data = list(data)
    return data


def getSegments(pitchvalues):
    """
    Divides the list of pitch values into segments
    :param pitchvalues: List of pitch values
    :return:List of lengths of each segment of pitch values
    """
    segment = []
    lastvalue = 0
    for value in pitchvalues:
        if value > 0:
            if lastvalue == 0 or len(segment) == 0:
                segment.append(0)
            segment[len(segment)-1]=segment[len(segment)-1]+1
        else:
            if lastvalue != 0 or len(segment) == 0:
                segment.append(0)
            segment[len(segment) - 1] = segment[len(segment) - 1] + 1
        lastvalue = value
    return segment


def getFirstX(values):
    """
    To get the first non zero element of a list
    :param values: List whose first non zero value is to be found
    :return: Position of first non zero element
    """
    firstX = 0
    for i in values:
        if i > 0:
            firstX = values.index(i)
            break
    return firstX


def getLastX(values):
    """
    To get the last non zero value in a list
    :param values: List whose last non zero element is to be found
    :return: Position of last non zero value
    """
    lastX = 0
    for i in range(len(values)-1, 0, -1):
        if values[i] > 0:
            lastX=i
            break
    return lastX


def getSegmentSlopes(pitchvalues):
    """
    Module generates a list of slopes.Each element in the list corresponds to the overall slope of a segment of pitchvalues
    :param pitchvalues: List of pitch values
    :return: List of slopes
    """
    slicedslope = []
    pitcharealength = getLastX(pitchvalues)-getFirstX(pitchvalues)
    segmentlengthlist = getSegments(pitchvalues)
    accumsegmentlength = 0
    for segmentlength in segmentlengthlist:
        if segmentlength > 0:
            segmentpoints = []
            for insidesegmentlength in range(0,segmentlength):
                currentX = accumsegmentlength+insidesegmentlength
                currentY = pitchvalues[currentX]
                if currentY != 0:
                    segmentpoints.append([currentX, currentY])
            i = 0
            sumX = 0.0
            sumY = 0.0
            sumX2 = 0.0
            sumXY = 0.0
            d = 0.0
            for i in range(0,len(segmentpoints)):
                sumX += segmentpoints[i][0]
                sumY += segmentpoints[i][1]
                sumX2 += segmentpoints[i][0]*segmentpoints[i][0]
                sumXY += segmentpoints[i][0]*segmentpoints[i][1]
            if len(segmentpoints) > 0:
                d = len(segmentpoints)*sumX2-sumX*sumX
                if d != 0:
                    slope = (len(segmentpoints)*sumXY-sumY*sumX)/d
                    slicedslope.append(slope)
        accumsegmentlength += abs(segmentlength)
    return slicedslope


def removeNaNsegments(userslicedslope, usersegments):
    """
    Module checks for NaN's in the list of slopes and removes any value which is a NaN from both the list of slopes and
    also removes the corresponding segment which has a NaN slope
    :param userslicedslope:List of slopes
    :param usersegments:List of length of segments
    :return:Modified list of slopes amd list of length of segments
    """
    for i in range(len(userslicedslope), 0, -1):
        if math.isnan(user[i]):
            userslicedslope.pop(i)
            usersegments.pop(i)


def removeInsconsistentSegments(slicedslope1, slicedslope2):
    """
    This module is used to remove inconsistent segments when the count of segments of extempore audio does not match the
    count of segments of the audio generated by text to speech module. This is done so that we can compare the segments
    of the two audio files
    :param slicedslope1: List of slopes of each segment of the audio file with greater number of segments
    :param slicedslope2: List of slopes of each segment of the audio file with lesser number of segments
    :return: Modified list of slopes and the difference between the number of segments to be removed and the number of
    segments actually removed
    """
    removecount = len(slicedslope1)-len(slicedslope2)
    indicestoremove = []
    for i in range(0,len(slicedslope2)-1):
        if slicedslope1[i] * slicedslope2[i] < 0:
            if len(indicestoremove) <= removecount:
                indicestoremove.append(i)
    for i in range(len(indicestoremove)-1, 0, -1):
        slicedslope1.pop(indicestoremove[i])
    if len(indicestoremove)-1 < removecount:
        return removecount-len(indicestoremove)+1
    else:
        return 0


def generatePronunciationGrade(user, comp):
    """
    Module scores the extempore based on pronunciation.
    this is done by comparing extempore audio with an audio generated by the text to speech module
    :param user: List of pitch values of the extempore audio
    :param comp: List of pitch values of the audio file generated by the text to speech module
    :return: Pronunciation score out of 10
    """
    segmentslopescore = 0.0
    segmentcounterror = 0.0
    segmentindex = 0
    # split user pitch values into segments
    usersegments = getSegments(user)
    u = float(len(usersegments))
    # split sample(audio generated by program) pitch values into segments
    compsegments = getSegments(comp)
    c = float(len(compsegments))
    # calculate the error in the number of extempore audio segments and the number of segments of sample audio generated by the code
    if len(usersegments) < len(compsegments):
        segmentcounterror = (c-u)/c
    elif len(usersegments) > len(compsegments):
        segmentcounterror = (u-c)/u
    # Find the slope of each segment for both the extempore audio and audio generated by text to speech module
    userslicedslope = getSegmentSlopes(user)
    compslicedslope = getSegmentSlopes(comp)
    count = 0
    removeNaNsegments(userslicedslope, usersegments)
    if len(userslicedslope) > len(compslicedslope):
        count = removeInsconsistentSegments(userslicedslope, compslicedslope)
    elif len(compslicedslope) > len(userslicedslope):
        count = removeInsconsistentSegments(compslicedslope, userslicedslope)
    '''
    Finding the pronunciation score by comparing the slope of each segment of extempore audio with corresponding segment 
    slope of the audio generated by the text to speech module. The error in segment count is also considered for the final
    score. If the both the slopes are either positive or both the slopes are negative then that part of pronunciation is
    considered correct. If no segement scores match or it is not possible to find and any inconsistent segments(in this 
    case a mismatch occurs in number segments, hence we cannot compare the segments)then just the segment count error is
    considered for final score 
    '''
    grade = 0.0
    if count == 0:
        for i in range(0, len(userslicedslope)):
            if userslicedslope[i]*compslicedslope[i] >= 0:
                segmentslopescore += 1
            segmentindex += 1
        if segmentslopescore != 0:
            grade = ((segmentslopescore / segmentindex) * 100 * (1.0 - (segmentcounterror*0.5)))
        else:
            grade = 100 * (1.0 - segmentcounterror)
    else:
        grade = 100*(1.0-segmentcounterror)
    grade /= 10
    print "pronunciation score out of 10=", grade
    return grade


def generateFluencyGrade(user, length):
    """
    Module generates a score for fluency based on the number of pauses(silences and fillers)in speech
    :param user:List of pitch values of extempore audio
    :param length:Length of the list of pitch values
    :return:Fluency Score out of 10
    """
    count = 0
    block = 0
    # check for silences of length greater than 1.5 seconds
    for i in range(0, len(user)):
        if user[i] == 0:
            count += 1
        else:
            count = 0
        if count == 200:
            block += 1
    # To check for fillers
    count = 0
    for i in range(0,len(user)-1):
        if user[i+1] != 0 and user[i] != 0:
            if(user[i+1] <= user[i] and user[i+1] >= user[i]-8) or (user[i+1] >= user[i] and user[i+1] <= user[i]+8):
                count += 1
            else:
                count = 0
            if count == 75:
                block += 1
                count = 0
    length = round(length/100)
    q = length/10
    totalgrade = length/q
    grade = totalgrade-0.25*block
    if grade < 0:
        grade = 0
    print "fluency score out of 10 =", grade
    return grade


i = 1
# creating a new excel workbook and adding a new sheet
book = xlwt.Workbook()
sh = book.add_sheet("Sheet 1")
sh.write(0, 0, "File Name")
sh.write(0, 1, "Score")
# srcpath contains the path to the folder where the audios are stored. All the files with .wav extension will be read
srcpath = #"ADD INPUT PATH HERE"
for srcfile in glob.iglob(srcpath):
    if not os.path.isfile(srcfile):
        continue
    print srcfile
    inputfile = toWAV(srcfile)
    res = speechToText(inputfile)
    if res == 0:
        sh.write(i, 0, srcfile)
        sh.write(i, 1, "Cannot rate file: background noise")
        i += 1
        book.save("results.xls")
        continue
    elif res == -1:
        sh.write(i, 0, srcfile)
        sh.write(i, 1, "Cannot rate file: speech unintelligible")
        i += 1
        book.save("results.xls")
        continue
    elif res == -2:
        sh.write(i, 0, srcfile)
        sh.write(i, 1, "Cannot connect to the server")
        i += 1
        book.save("results.xls")
        continue
    else:
        toMono(inputfile)
        user = findPitch(inputfile)
        # hello.wav is the file generated by the program
        sample = 'D:\Speech\pronunciation_and_fluency\hello.wav'
        comp = findPitch(sample)
        fluencyscore = generateFluencyGrade(user, len(user))
        pronunciationscore = generatePronunciationGrade(user, comp)
        '''
        Weightage of pronunciation is lesser than fluency as according to research fluency out weighs pronunciation when it 
        comes to understandability of speech
        '''
        score = (0.4 * pronunciationscore + 0.6 * fluencyscore) * 10
        # writing score to excel file
        sh.write(i, 0, srcfile)
        sh.write(i, 1, score)
        i += 1
        time.sleep(5)
        book.save("results.xls")
src="D:\Speech\pronunciation_and_fluency\sound\*"
for file in glob.iglob(src):
    os.remove(file)
if os.path.isfile("src.wav"):
    os.remove("src.wav")
if os.path.isfile("hello.wav"):
    os.remove("hello.wav")
