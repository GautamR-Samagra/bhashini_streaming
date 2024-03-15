import signal
from asr_client import Dhruva_ASR_SpeechStreamingClient_SocketIO

def display_results(transcript_history, current_transcript):
    print()
    if transcript_history:
        print("Transcript:", transcript_history)
    print("Current:", current_transcript)

if __name__ == "__main__":
    streamer = Dhruva_ASR_SpeechStreamingClient_SocketIO(
        # socket_url="wss://api.dhruva.ai4bharat.org",
        socket_url="wss://dhruva-api.bhashini.gov.in",
        # socket_url="wss://bhashini-dhruva-staging-backend-app-service.azurewebsites.net",
        # api_key="16e16551-7d87-45b2-90ad-a5b91c48e8d6",
        # api_key="4f583212-756a-4f19-b9ef-1e43662600ff",
        api_key="o60Y293maQOLMF8X5Sg1Tw5BoHgMmXuQJjM6ZMJtnV-MVIPS9zzMfZclJgx9aJI1",
        task_sequence=[
            {
                "taskType": "asr",
                "config": {
                    "serviceId": "ai4bharat/whisper-medium-en--gpu--t4",
                    "language": {
                        "sourceLanguage": "en"
                    },
                    "samplingRate": 8000,
                    "audioFormat": "wav",
                    "encoding": None,
                    # "channel": "mono",
                    # "bitsPerSample": "sixteen"
                }
            }
        ],
        response_callback=display_results,
        auto_start=True,
    )
    signal.signal(signal.SIGINT, streamer.force_disconnect)

    try:
        input("(Press Enter to Stop) ")
        streamer.stop()
    except:
        pass
