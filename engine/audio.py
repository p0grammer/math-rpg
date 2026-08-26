"""
Mathpal — Audio Manager
========================
Advanced retro audio manager providing:
* Synthetic multi-track looping chiptune BGM ("village" and "battle" themes).
* Dedicated BGM channel (Channel 0) with seamless loop playback.
* Dedicated SFX channels (Channels 1-15) for overlapping sound effects that
  never cut off or interrupt the background music.
* Real-time volume controls that immediately apply to active music and SFX.
* Full procedural waveform generation — no external audio assets required!
"""

import os
import pygame
import numpy as np

from config import AUDIO_SFX_VOLUME, AUDIO_BGM_VOLUME, AUDIO_SAMPLE_RATE


class AudioManager:
    """
    Singleton audio manager. Access with ``AudioManager()`` anywhere.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Allocate 16 channels so BGM and many simultaneous SFX never collide
        try:
            pygame.mixer.set_num_channels(16)
        except Exception:
            pass

        self._sfx_cache: dict[str, pygame.mixer.Sound] = {}
        self._bgm_cache: dict[str, pygame.mixer.Sound] = {}
        self._sfx_volume = AUDIO_SFX_VOLUME
        self._bgm_volume = AUDIO_BGM_VOLUME
        self._muted = False
        self._current_bgm_name = None

        # Channel 0 reserved exclusively for BGM loop
        try:
            self._bgm_channel = pygame.mixer.Channel(0)
        except Exception:
            self._bgm_channel = None

        self._generate_default_sounds()
        self._generate_default_bgm()

    # ------------------------------------------------------------------
    # Procedural SFX Generation
    # ------------------------------------------------------------------

    def _generate_default_sounds(self):
        """Create chiptune SFX from raw waveforms."""
        sr = AUDIO_SAMPLE_RATE
        try:
            # UI sounds
            self._sfx_cache["hover"]        = self._make_tone(880, 0.04, sr)
            self._sfx_cache["select"]       = self._make_arpeggio([523, 659, 784], 0.07, sr)
            self._sfx_cache["block_click"]  = self._make_tone(1046, 0.03, sr, wave="pulse")
            self._sfx_cache["toggle"]       = self._make_arpeggio([440, 880], 0.05, sr)

            # Gameplay sounds
            self._sfx_cache["correct"]      = self._make_arpeggio([523, 659, 784, 1047], 0.09, sr)
            self._sfx_cache["wrong"]        = self._make_arpeggio([392, 330, 262], 0.14, sr)
            self._sfx_cache["levelup"]      = self._make_arpeggio([523, 659, 784, 1047, 1319], 0.10, sr)
            self._sfx_cache["damage"]       = self._make_tone(150, 0.20, sr, wave="noise")

            # Battle & kinetic animation sounds
            self._sfx_cache["crack"]        = self._make_tone(180, 0.10, sr, wave="noise")
            self._sfx_cache["bounce"]       = self._make_tone(320, 0.06, sr)
            self._sfx_cache["slide"]        = self._make_arpeggio([300, 400, 500], 0.04, sr)
            self._sfx_cache["tick"]         = self._make_tone(600, 0.03, sr)
            self._sfx_cache["slash"]        = self._make_arpeggio([800, 600, 400], 0.04, sr)
            self._sfx_cache["text_advance"] = self._make_tone(440, 0.02, sr)
            self._sfx_cache["split"]        = self._make_arpeggio([400, 600, 800, 1000], 0.03, sr)
            self._sfx_cache["merge"]        = self._make_arpeggio([600, 750, 900, 1200], 0.05, sr)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Procedural BGM Generation (Village & Battle Themes)
    # ------------------------------------------------------------------

    def _generate_default_bgm(self):
        """Synthesize looping 8-bit chiptune background tracks."""
        sr = AUDIO_SAMPLE_RATE
        try:
            # 1. Calm Village / Menu Theme (C Major / A Minor pentatonic - 100 BPM)
            self._bgm_cache["village"] = self._synthesize_village_theme(sr)

            # 2. Energetic Battle Theme (D Minor harmonic - 144 BPM)
            self._bgm_cache["battle"] = self._synthesize_battle_theme(sr)
        except Exception:
            pass

    def _synthesize_village_theme(self, sr):
        """Synthesize a soothing 90s RPG village/menu loop (4 bars)."""
        bpm = 100
        beat_len = 60.0 / bpm
        total_beats = 16  # 4 bars of 4/4
        duration = total_beats * beat_len
        n_samples = int(sr * duration)
        master = np.zeros(n_samples, dtype=np.float32)

        # Frequencies (Hz)
        C4, D4, E4, F4, G4, A4, B4 = 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88
        C5, D5, E5, G5, A5, C6     = 523.25, 587.33, 659.25, 783.99, 880.00, 1046.50

        # --- Track 1: Gentle Melody (Square wave with soft envelope) ---
        melody = [
            # Bar 1 (C maj)
            (0.0 * beat_len, 1.5 * beat_len, E5),
            (1.5 * beat_len, 0.5 * beat_len, G5),
            (2.0 * beat_len, 2.0 * beat_len, C6),
            # Bar 2 (A min)
            (4.0 * beat_len, 1.5 * beat_len, A5),
            (5.5 * beat_len, 0.5 * beat_len, E5),
            (6.0 * beat_len, 2.0 * beat_len, G5),
            # Bar 3 (F maj)
            (8.0 * beat_len, 1.0 * beat_len, F4),
            (9.0 * beat_len, 1.0 * beat_len, A4),
            (10.0 * beat_len, 2.0 * beat_len, C5),
            # Bar 4 (G maj / turn)
            (12.0 * beat_len, 1.5 * beat_len, D5),
            (13.5 * beat_len, 0.5 * beat_len, E5),
            (14.0 * beat_len, 2.0 * beat_len, D5),
        ]
        for start_t, dur_t, freq in melody:
            idx_start = int(start_t * sr)
            idx_len = int(dur_t * sr)
            if idx_start + idx_len > n_samples:
                idx_len = n_samples - idx_start
            t = np.linspace(0, dur_t, idx_len, endpoint=False)
            # Pulse wave (25% duty cycle) for sweet 8-bit harp/flute sound
            sig = np.where((t * freq) % 1.0 < 0.25, 1.0, -1.0)
            env = np.exp(-1.5 * t / dur_t)
            master[idx_start:idx_start + idx_len] += sig * env * 0.22

        # --- Track 2: Arpeggio accompaniment (16th notes) ---
        chords = [
            [C4, E4, G4, C5],  # C
            [A4 / 2, C4, E4, A4],  # Am
            [F4 / 2, A4 / 2, C4, F4],  # F
            [G4 / 2, B4 / 2, D4, G4],  # G
        ]
        sixteenth = beat_len / 4.0
        for bar in range(4):
            chord = chords[bar]
            for step in range(16):
                t_pos = (bar * 4 + step * 0.25) * beat_len
                idx_start = int(t_pos * sr)
                idx_len = int(sixteenth * sr)
                if idx_start + idx_len > n_samples:
                    idx_len = n_samples - idx_start
                note_freq = chord[step % len(chord)]
                t = np.linspace(0, sixteenth, idx_len, endpoint=False)
                sig = np.sign(np.sin(2 * np.pi * note_freq * t))
                env = np.exp(-6.0 * t / sixteenth)
                master[idx_start:idx_start + idx_len] += sig * env * 0.10

        # --- Track 3: Bassline (Warm square) ---
        bass_notes = [C4 / 2, A4 / 4, F4 / 4, G4 / 4]
        for bar in range(4):
            t_pos = bar * 4 * beat_len
            idx_start = int(t_pos * sr)
            idx_len = int(3.5 * beat_len * sr)
            if idx_start + idx_len > n_samples:
                idx_len = n_samples - idx_start
            t = np.linspace(0, 3.5 * beat_len, idx_len, endpoint=False)
            sig = np.where((t * bass_notes[bar]) % 1.0 < 0.5, 1.0, -1.0)
            env = np.exp(-0.8 * t / (3.5 * beat_len))
            master[idx_start:idx_start + idx_len] += sig * env * 0.18

        return self._numpy_to_sound(master)

    def _synthesize_battle_theme(self, sr):
        """Synthesize an energetic 90s RPG battle theme loop (4 bars, 144 BPM)."""
        bpm = 144
        beat_len = 60.0 / bpm
        total_beats = 16  # 4 bars
        duration = total_beats * beat_len
        n_samples = int(sr * duration)
        master = np.zeros(n_samples, dtype=np.float32)

        # Frequencies (Hz)
        D3, F3, G3, A3, Bb3, C4, Csh4, D4 = 146.83, 174.61, 196.00, 220.00, 233.08, 261.63, 277.18, 293.66
        D5, F5, G5, A5, Bb5, Csh6, D6      = 587.33, 698.46, 783.99, 880.00, 932.33, 1108.73, 1174.66

        # --- Track 1: Fast Driving Lead ---
        lead_pattern = [
            (0.0, 0.5, D5), (0.5, 0.5, F5), (1.0, 1.0, A5), (2.0, 0.5, D6), (2.5, 0.5, Csh6), (3.0, 1.0, A5),
            (4.0, 0.5, Bb5), (4.5, 0.5, G5), (5.0, 1.0, A5), (6.0, 0.5, F5), (6.5, 0.5, G5), (7.0, 1.0, E5 if 'E5' in locals() else 659.25),
            (8.0, 0.5, D5), (8.5, 0.5, F5), (9.0, 0.5, A5), (9.5, 0.5, D6), (10.0, 1.0, Csh6), (11.0, 1.0, A5),
            (12.0, 0.5, Bb5), (12.5, 0.5, A5), (13.0, 0.5, G5), (13.5, 0.5, F5), (14.0, 1.0, E5 if 'E5' in locals() else 659.25), (15.0, 1.0, D5),
        ]
        for start_beat, dur_beat, freq in lead_pattern:
            t_start = start_beat * beat_len
            t_dur = dur_beat * beat_len
            idx_start = int(t_start * sr)
            idx_len = int(t_dur * sr)
            if idx_start + idx_len > n_samples:
                idx_len = n_samples - idx_start
            t = np.linspace(0, t_dur, idx_len, endpoint=False)
            sig = np.sign(np.sin(2 * np.pi * freq * t))
            env = np.exp(-2.0 * t / t_dur)
            master[idx_start:idx_start + idx_len] += sig * env * 0.22

        # --- Track 2: 16th Note Driving Bassline ---
        bass_seq = [
            D3, D3, F3, D3, G3, D3, A3, D3,
            Bb3, Bb3, A3, G3, F3, F3, E4 if 'E4' in locals() else 329.63, Csh4,
            D3, D3, F3, D3, G3, D3, A3, D3,
            G3, G3, F3, F3, E4 if 'E4' in locals() else 329.63, E4 if 'E4' in locals() else 329.63, D3, D3,
        ]
        eighth = beat_len / 2.0
        for i, b_freq in enumerate(bass_seq):
            t_start = i * eighth
            idx_start = int(t_start * sr)
            idx_len = int(eighth * sr)
            if idx_start + idx_len > n_samples:
                idx_len = n_samples - idx_start
            t = np.linspace(0, eighth, idx_len, endpoint=False)
            # Chunky pulse bass
            sig = np.where((t * b_freq) % 1.0 < 0.5, 1.0, -1.0)
            env = np.exp(-4.0 * t / eighth)
            master[idx_start:idx_start + idx_len] += sig * env * 0.22

        # --- Track 3: 8-bit Noise Drum Hits (Kick on 1, 3; Snare on 2, 4) ---
        for beat in range(16):
            t_start = beat * beat_len
            idx_start = int(t_start * sr)
            is_snare = (beat % 2 == 1)
            dur = 0.08 if is_snare else 0.05
            idx_len = int(dur * sr)
            if idx_start + idx_len > n_samples:
                idx_len = n_samples - idx_start
            t = np.linspace(0, dur, idx_len, endpoint=False)
            if is_snare:
                noise = np.random.uniform(-1, 1, idx_len)
                env = np.exp(-25.0 * t)
                master[idx_start:idx_start + idx_len] += noise * env * 0.18
            else:
                # 8-bit pitch-dropping kick
                freq_sweep = np.linspace(160, 40, idx_len)
                kick = np.sin(2 * np.pi * freq_sweep * t)
                env = np.exp(-20.0 * t)
                master[idx_start:idx_start + idx_len] += kick * env * 0.25

        return self._numpy_to_sound(master)

    @staticmethod
    def _numpy_to_sound(mono_array):
        """Convert a floating-point numpy waveform into a stereo pygame.mixer.Sound."""
        # Normalize and prevent clipping
        peak = np.max(np.abs(mono_array))
        if peak > 0:
            mono_array = mono_array / peak * 0.85

        pcm = (mono_array * 32767).astype(np.int16)
        stereo = np.column_stack((pcm, pcm))
        return pygame.sndarray.make_sound(stereo)

    # ------------------------------------------------------------------
    # Waveform Primitives
    # ------------------------------------------------------------------

    @staticmethod
    def _make_tone(freq, duration, sample_rate, wave="square"):
        """Generate a single tone as a Sound object."""
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)

        if wave == "square":
            signal = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave == "pulse":
            signal = np.where((t * freq) % 1.0 < 0.25, 1.0, -1.0)
        elif wave == "noise":
            signal = np.random.uniform(-1, 1, n_samples)
            kernel = np.ones(8) / 8
            signal = np.convolve(signal, kernel, mode="same")
        else:
            signal = np.sin(2 * np.pi * freq * t)

        fade = max(1, int(0.008 * sample_rate))
        envelope = np.ones(n_samples)
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)

        signal = (signal * envelope * 0.30 * 32767).astype(np.int16)
        stereo = np.column_stack((signal, signal))
        return pygame.sndarray.make_sound(stereo)

    @staticmethod
    def _make_arpeggio(freqs, note_duration, sample_rate):
        """Chain multiple square-wave tones into a fast arpeggio."""
        parts = []
        for freq in freqs:
            n = int(sample_rate * note_duration)
            t = np.linspace(0, note_duration, n, endpoint=False)
            sig = np.sign(np.sin(2 * np.pi * freq * t))
            env = np.exp(-4 * t / note_duration)
            parts.append((sig * env * 0.28 * 32767).astype(np.int16))

        combined = np.concatenate(parts)
        stereo = np.column_stack((combined, combined))
        return pygame.sndarray.make_sound(stereo)

    # ------------------------------------------------------------------
    # SFX Playback (Using Channels 1-15)
    # ------------------------------------------------------------------

    def play_sfx(self, name):
        """Play a sound effect on an available non-BGM channel."""
        if self._muted or self._sfx_volume <= 0.001:
            return
        sound = self._sfx_cache.get(name)
        if sound:
            sound.set_volume(self._sfx_volume)
            # Find a free channel among 1..15 to prevent touching Channel 0 (BGM)
            channel = pygame.mixer.find_channel(force=False)
            if channel is not None and channel != self._bgm_channel:
                channel.play(sound)
            else:
                sound.play()

    def load_sfx(self, name, filepath):
        """Load an external audio file into the SFX cache."""
        if os.path.isfile(filepath):
            try:
                self._sfx_cache[name] = pygame.mixer.Sound(filepath)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Background Music (Dedicated Channel 0 Loop)
    # ------------------------------------------------------------------

    def play_bgm(self, track_name):
        """
        Play a looping background music track ("village", "battle").
        Seamlessly keeps playing if already running.
        """
        if self._current_bgm_name == track_name and self._bgm_channel and self._bgm_channel.get_busy():
            return

        self._current_bgm_name = track_name
        if self._muted or self._bgm_volume <= 0.001:
            self.stop_bgm()
            return

        sound = self._bgm_cache.get(track_name)
        if sound and self._bgm_channel:
            sound.set_volume(self._bgm_volume)
            self._bgm_channel.play(sound, loops=-1)

    def stop_bgm(self):
        """Stop current background music."""
        if self._bgm_channel:
            try:
                self._bgm_channel.stop()
            except Exception:
                pass
        self._current_bgm_name = None

    # ------------------------------------------------------------------
    # Volume Controls (Real-Time Synchronous)
    # ------------------------------------------------------------------

    def get_sfx_volume(self):
        return self._sfx_volume

    def set_sfx_volume(self, vol):
        self._sfx_volume = max(0.0, min(1.0, vol))
        for sound in self._sfx_cache.values():
            try:
                sound.set_volume(self._sfx_volume)
            except Exception:
                pass

    def get_bgm_volume(self):
        return self._bgm_volume

    def set_bgm_volume(self, vol):
        self._bgm_volume = max(0.0, min(1.0, vol))
        if self._bgm_channel:
            try:
                self._bgm_channel.set_volume(self._bgm_volume)
            except Exception:
                pass
        # If unmuting / raising from 0 when a track was active
        if self._bgm_volume > 0.01 and self._current_bgm_name and not (self._bgm_channel and self._bgm_channel.get_busy()):
            self.play_bgm(self._current_bgm_name)

    def toggle_mute(self):
        self._muted = not self._muted
        if self._muted:
            if self._bgm_channel:
                self._bgm_channel.stop()
        else:
            if self._current_bgm_name:
                self.play_bgm(self._current_bgm_name)
        return self._muted
