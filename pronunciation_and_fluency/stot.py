# NOTE: this requires PyAudio because it uses the Microphone class
from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr
import math

sound1 = AudioSegment.from_file("C:\Users\shriya.magadal\Downloads\mp3\s16.wav", format="wav")
thresh=sound1.dBFS+0.5*sound1.dBFS
chunks=split_on_silence(sound1,min_silence_len=900,silence_thresh=thresh)
i=0
print thresh
for i,chunk in enumerate(chunks):

    print "splitting", i

    chunk.export("D:\SpeechEval\pronunciation_and_fluency\sound\chunk{0}.wav".format(i),format="wav")

str=""
r = sr.Recognizer()
for i in range(0,len(chunks)):
    with sr.WavFile("D:\SpeechEval\pronunciation_and_fluency\sound\chunk{0}.wav".format(i)) as source:              # use "test.wav" as the audio source
       audio = r.record(source)                        # extract audio data from the file
    retry=0
    while retry<5:
        try:
            newstr= r.recognize_google(audio)   # recognize speech using Google Speech Recognition
            #print newstr
            str=str+newstr
        except LookupError:                            # speech is unintelligible
            print("Could not understand audio")
        except sr.RequestError:
            print retry
            retry += 1


print str
