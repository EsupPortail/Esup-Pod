from django.conf import settings

import collections
import contextlib
import wave
import webrtcvad


VAD_AGRESSIVITY = getattr(settings, "VAD_AGRESSIVITY", 1)
SAMPLE_WINDOW = getattr(settings, "SAMPLE_WINDOW", 20)
SAMPLE_OVERLAP = getattr(settings, "SAMPLE_OVERLAP", 300)
THRESHOLD_VOICED = getattr(settings, "THRESHOLD_VOICED", 90) / 100
THRESHOLD_UNVOICED = getattr(settings, "THRESHOLD_UNVOICED", 90) / 100


class VoiceActivityDetector(object):
    class Frame(object):
        def __init__(self, bytes, timestamp, duration):
            self.bytes = bytes
            self.timestamp = timestamp
            self.end = timestamp + duration
            self.duration = duration

    def __init__(self, wave_input_filename):
        self.read_wave(wave_input_filename)

    def read_wave(self, path):
        with contextlib.closing(wave.open(path, "rb")) as wf:
            self.sample_rate = wf.getframerate()
            frames = wf.getnframes()
            self.pcm_data = wf.readframes(frames)

    def frame_generator(self, frame_duration_ms, audio, sample_rate):
        n = int(sample_rate * (frame_duration_ms / 1000) * 2)
        offset = 0
        timestamp = 0
        duration = int(sample_rate * (frame_duration_ms / 1000))
        while offset + n < len(audio):
            yield VoiceActivityDetector.Frame(
                audio[offset : offset + n], timestamp, duration
            )
            timestamp += duration
            offset += n

    def vad_collector(
        self, sample_rate, frame_duration_ms, padding_duration_ms, vad, frames
    ):
        num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False
        voiced_frames = []
        for frame in frames:
            is_speech = vad.is_speech(frame.bytes, sample_rate)
            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > THRESHOLD_VOICED * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        voiced_frames.append(f)
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > THRESHOLD_UNVOICED * ring_buffer.maxlen:
                    triggered = False
                    yield (
                        voiced_frames[0].timestamp,
                        voiced_frames[-1].end,
                        b"".join([f.bytes for f in voiced_frames]),
                        sample_rate,
                    )
                    ring_buffer.clear()
                    voiced_frames = []
        if voiced_frames:
            yield (
                voiced_frames[0].timestamp,
                voiced_frames[-1].end,
                b"".join([f.bytes for f in voiced_frames]),
                sample_rate,
            )

    def vad_segment_generator(self):
        vad = webrtcvad.Vad(int(VAD_AGRESSIVITY))
        frames = self.frame_generator(SAMPLE_WINDOW, self.pcm_data, self.sample_rate)
        frames = list(frames)
        segments = self.vad_collector(
            self.sample_rate, SAMPLE_WINDOW, SAMPLE_OVERLAP, vad, frames
        )
        return segments, self.sample_rate
