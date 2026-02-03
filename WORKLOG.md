# Project Worklog

## Feature: Visual & Language Enhancements

**Date**: 2026-02-03
**Branch**: `feature/visual-lang-enhance`
**Status**: Completed

### 1. Visual Quality Improvements
**Issue**: Generated lips looked "edited" or "cut-out" with hard edges.
**Change**: Implemented **Mask Feathering** (Alpha Blending) in `services/visual/Wav2Lip/inference.py`.
- **Logic**: Instead of a hard paste (`f[y1:y2] = p`), we now generate a transparency mask for the lip region.
- **Feathering**: The mask is blurred using `cv2.GaussianBlur` (Kernel: 51x51).
- **Blending**: The new lips are alpha-blended with the original face frame, ensuring smooth transitions at the chin and cheeks.

### 2. Audio Quality & Language Support
**Issue**: 
1. `XTTS v2` model does not support Telugu (`te`) language. error: `Language te is not supported`.
2. Voice sounded robotic/rushed with `speed=1.1`.
3. Mixed language text ("Hello, Durga...") was failing logic detection.

**Changes**:
- **Telugu Support via "Hindi Hack"**:
    - **Logic**: Since XTTS supports Hindi (`hi`) and phonetic structures are similar, we now:
        1. Detect Romanized Telugu.
        2. Transliterate it to **Devanagari** script (Hindi script) using `indic-transliteration`.
        3. Pass it to XTTS with `language="hi"`.
    - **Result**: The model reads the "Hindi" characters but produces correct Telugu pronunciation and Indian accent.
- **Language Auto-Detection**:
    - Expanded `TELUGU_KEYWORDS` in `services/audio/worker.py` to include colloquial words (`nuv`, `na`, `modda`, `koni`, etc.) to catch "Tanglish" (Telugu-English mixed) text.
- **TTS Tuning**:
    - Reverted `speed` to `1.0` to fix slurred words.
    - Kept `split_sentences=False` to prevent robotic pauses between sentences.
    - Set `temperature=0.75` for natural inflection.
