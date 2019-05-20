from google.cloud.speech import enums, types, SpeechClient
import time, os

from ...aux import printmsg
from .Speech import Speech
from ...elements.WStamp import WStamps
from ...cache.Cache import global_cache

from mutagen.mp3 import MP3

class SpeechGC(Speech):
    """Google Cloud Speech-to-Text."""

    def __init__(self, filename):
        path = 'gs://iiaproj-resources/%s.flac' % filename
        super().__init__(path)
        self.cache = global_cache
        self.cache_key = 'SpeechGC(%s)' % filename
        # get audio length
        mp3path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../audio/%s.mp3' % filename))
        audio = MP3(mp3path)
        self.audio_len = audio.info.length # length in seconds
    
    def process(self):
        """Run the Speech Recogniser and return the result."""
        if self.cache_key in self.cache:
            trans = self.cache[self.cache_key]
        else:
            trans = self.transcribe_gcs(self.path)
            self.cache[self.cache_key] = trans
        wstamps = []
        for x in trans:
            wstamps.extend(x['words'])
        self.result = WStamps(wstamps=wstamps)
        return self.result
    
    def transcribe_gcs(self, gcs_uri):
        """Asynchronously transcribes the audio file specified by the gcs_uri.
        args:
            gcs_uri - URI with format 'gs://<bucket>/<path_to_audio>'
        returns:
            trans - a list of transcribed sections
        """
        printmsg.begin('Initiating Google Cloud Speech operation')
        client = SpeechClient()

        audio = types.RecognitionAudio(uri=gcs_uri)
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
            sample_rate_hertz=44100,
            language_code='en-GB',
            enable_word_time_offsets=True)

        operation = client.long_running_recognize(config, audio)
        printmsg.end()

        printmsg.begin('Waiting for operation to complete [0%%]')
        while not operation.done():
            time.sleep(1)
            printmsg.begin('Waiting for operation to complete [%s%%]' % operation.metadata.progress_percent)
        response = operation.result(timeout=10)
        printmsg.end()

        # Each result is for a consecutive portion of the audio. Iterate through
        # them to get the transcripts for the entire audio file.
        trans = []
        for result in response.results:
            # The first alternative is the most likely one for this portion.
            best = result.alternatives[0]
            get_ts = lambda x: dict(min=x.seconds//60, sec=x.seconds%60, msec=x.nanos//(10**6))
            seg = dict(text=best.transcript, confidence=best.confidence, words=[])
            # loop the words
            for word_info in best.words:
                word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time
                word_obj = dict(word=word, tstamp=get_ts(start_time))
                seg['words'].append(word_obj)
            trans.append(seg)
                
        return trans
    

if __name__ == '__main__':
    speech = SpeechGC('lecture1')
    speech.process()