# Streaming Client Example

The list of all supported languages and corresponding serviceId's are available here:  
https://docs.google.com/spreadsheets/d/1QPBXdm67T7B8Q07mKzLpvo7TWLScsRixCxDOGnsPGyQ/

## Prerequisites

1. Python 3.7+
2. `pip install -r requirements.txt`

## Automatic Speech Recognition

In `asr_recorder.py`, set the variables:
- `api_key`
- `serviceId`
- `sourceLanguage`

Then run `python asr_recorder.py`, and once it says "_START SPEAKING_", you can talk through your microphone.
It should be see the live stream output printed on the terminal as you speak.
