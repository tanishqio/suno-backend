# Audio Files Documentation

## Overview

The hearing screening test uses 9 pre-recorded audio files, each containing a spoken number (1-9) with varying levels of background noise. The noise levels are progressively increased to assess hearing ability across different difficulty levels.

## Audio Clips Table

| # | Filename | Expected Key | Noise Level (dB) | Description | Difficulty |
|---|----------|:-------------:|:----------------:|-------------|:----------:|
| 1 | `number_1_noise_40db.mp3` | 1 | 40 dB SNR | Number "1" spoken clearly with light ambient noise | Easy |
| 2 | `number_2_noise_35db.mp3` | 2 | 35 dB SNR | Number "2" with increased background noise | Easy |
| 3 | `number_3_noise_30db.mp3` | 3 | 30 dB SNR | Number "3" with moderate background noise | Easy |
| 4 | `number_4_noise_25db.mp3` | 4 | 25 dB SNR | Number "4" with moderately increased noise | Medium |
| 5 | `number_5_noise_20db.mp3` | 5 | 20 dB SNR | Number "5" with significant background noise | Medium |
| 6 | `number_6_noise_15db.mp3` | 6 | 15 dB SNR | Number "6" with heavy background noise | Medium |
| 7 | `number_7_noise_10db.mp3` | 7 | 10 dB SNR | Number "7" with very heavy background noise | Hard |
| 8 | `number_8_noise_8db.mp3` | 8 | 8 dB SNR | Number "8" with extreme background noise | Hard |
| 9 | `number_9_noise_5db.mp3` | 9 | 5 dB SNR | Number "9" nearly drowned out by noise | Hard |

## Key Details

### SNR (Signal-to-Noise Ratio)
- **Higher SNR** = More intelligible (easier to hear)
- **Lower SNR** = More challenging
- **40 dB SNR** is nearly noise-free
- **5 dB SNR** is heavily obscured by noise

### Audio Specifications

All audio files should have the following characteristics:

```
Format:         MP3
Sample Rate:    16000 Hz
Bit Rate:       128 kbps
Duration:       ~2-3 seconds per clip
Channels:       Mono
Compression:    MP3 (lossy)
```

### Content

Each file contains:
- A short silence (0.2s)
- A single spoken digit (1-9) in a clear, neutral voice
- A trailing silence (0.2s)

### Noise Profile

The background noise for each clip is:
- Simulated office environment noise (HVAC, ambient chatter, keyboard sounds)
- Consistent frequency spectrum (white noise mixed with pink noise)
- Smooth noise envelope (no sudden spikes or clicks)

## How to Obtain/Create Audio Files

### Option 1: Use Existing Audio Generation Services

Services like **Amazon Polly**, **Google Text-to-Speech**, or **Azure Speech** can generate the base audio. Then:

1. Generate 9 files with text-to-speech for digits 1-9
2. Use **Audacity** or **FFmpeg** to add background noise at varying levels

Example with FFmpeg:

```bash
# Add background noise using a noise file
ffmpeg -i number_1_original.mp3 -i background_noise.mp3 \
  -filter_complex "overlay=0:0" -c:a libmp3lame -q:a 5 \
  number_1_noise_40db.mp3
```

### Option 2: Manually Create with Audacity

1. Open Audacity
2. Generate audio for each number using a TTS plugin or record manually
3. Import background noise track
4. Adjust levels to achieve target SNR
5. Export as MP3

### Option 3: Use Pre-made Test Audio

Clinical hearing test software often provides audio files (e.g., from Interacoustics, GN Resound). Check licensing requirements.

## Hosting Audio Files

### CDN/Cloud Options

1. **AWS S3**
   ```python
   AUDIO_BASE_URL = "https://my-bucket.s3.amazonaws.com/hearing-test/"
   ```

2. **Google Cloud Storage**
   ```python
   AUDIO_BASE_URL = "https://storage.googleapis.com/my-bucket/hearing-test/"
   ```

3. **Azure Blob Storage**
   ```python
   AUDIO_BASE_URL = "https://mystorageaccount.blob.core.windows.net/hearing-test/"
   ```

4. **Cloudflare R2**
   ```python
   AUDIO_BASE_URL = "https://my-domain.r2.cloudflairstorage.com/hearing-test/"
   ```

5. **Self-hosted (Simple)**
   ```python
   # Serve from /public/audio/ in your web server
   AUDIO_BASE_URL = "https://your-domain.com/public/audio/"
   ```

### Public Accessibility

All audio files MUST be:
- ✅ Publicly accessible (no authentication required)
- ✅ Directly downloadable (no redirects)
- ✅ Available 24/7
- ✅ With proper CORS headers (if called from browser)

## Configuration

In `config.py`, update:

```python
AUDIO_BASE_URL = "https://your-cdn.com/hearing-test/"
```

This will be used to construct full URLs like:
```
https://your-cdn.com/hearing-test/number_1_noise_40db.mp3
https://your-cdn.com/hearing-test/number_2_noise_35db.mp3
... etc
```

## Testing Audio Playback

Use curl to test:

```bash
curl -I https://your-cdn.com/hearing-test/number_1_noise_40db.mp3
```

Expected response:
```
HTTP/2 200
Content-Type: audio/mpeg
Content-Length: 45000
```

## Audio Clip Configuration in Code

In `config.py`, each clip is defined:

```python
AUDIO_CLIPS = {
    1: {
        "filename": "number_1_noise_40db.mp3",
        "expected_key": "1",
        "noise_level": "low",
        "description": "Number 1 with low background noise"
    },
    # ... etc for 2-9
}
```

The backend uses these to:
1. Generate full URLs by combining `AUDIO_BASE_URL + filename`
2. Track which clips have been used (avoid repetition within a test)
3. Validate correct answers

## Best Practices

### Creating Audio

- **Recording**: Use a quiet room with good quality microphone
- **Voice**: Consistent speaker, neutral tone, clear pronunciation
- **Noise**: Real-world noise is better than artificial (if possible)
- **Levels**: Use audio editing software to verify SNR values
- **QA**: Test with real phone calls to ensure quality

### Hosting

- Use **HTTPS only** (required for Bolna)
- Use **CDN with caching** (faster delivery)
- Enable **CORS headers** if called from browser:
  ```
  Access-Control-Allow-Origin: *
  ```
- Monitor **bandwidth usage** (audio files are ~45-50KB each)

### Deployment Checklist

- [ ] All 9 audio files uploaded to CDN
- [ ] URLs are publicly accessible
- [ ] HTTPS is enabled
- [ ] CORS headers configured (if needed)
- [ ] `AUDIO_BASE_URL` in `config.py` is correct
- [ ] Audio quality verified with test calls
- [ ] Bandwidth budget confirmed

## Example Audio File Generation Script

Here's a Python script to generate test audio (requires libraries):

```python
# Note: This is a skeleton - requires additional libraries
# pip install pyttsx3 pydub numpy scipy

import pyttsx3
from pydub import AudioSegment
from pydub.generators import WhiteNoise
import numpy as np

def create_audio_with_noise(digit, noise_level_db):
    """Generate a digit audio file with background noise."""
    
    # Generate speech
    engine = pyttsx3.init()
    engine.save_to_file(str(digit), f"temp_{digit}.wav")
    engine.runAndWait()
    
    # Load audio
    speech = AudioSegment.from_wav(f"temp_{digit}.wav")
    
    # Generate noise at specified level
    noise = WhiteNoise().to_audio_segment(duration=len(speech))
    noise = noise - (noise_level_db)  # Reduce noise level
    
    # Mix
    combined = speech.overlay(noise)
    
    # Export
    combined.export(f"number_{digit}_noise_{noise_level_db}db.mp3", format="mp3")

# Generate all 9 files
noise_levels = [40, 35, 30, 25, 20, 15, 10, 8, 5]
for digit, noise_level in enumerate(noise_levels, 1):
    create_audio_with_noise(digit, noise_level)
```

## Troubleshooting

### Audio not playing

- Verify URL is correct and accessible
- Check audio format (must be MP3 or supported format)
- Ensure file is not corrupted (test with local player)
- Check CDN/hosting logs

### Wrong answers on easy clips

- Audio may be too noisy
- Voice clarity might be poor
- SNR levels may need adjustment
- Test with audiologist

### All answers correct (too easy)

- Increase noise levels across the board
- Test is not challenging enough

## References

- [AudioVisual Signal-to-Noise Ratio](https://en.wikipedia.org/wiki/Signal-to-noise_ratio)
- [Pure Tone Audiometry](https://www.audiology.org/)
- [ANSI Standards for Audiometry](https://webstore.ansi.org/)
