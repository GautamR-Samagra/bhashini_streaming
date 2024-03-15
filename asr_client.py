import socketio
import pyaudio

class Dhruva_ASR_SpeechStreamingClient_SocketIO:
    def __init__(
        self,
        socket_url: str,
        api_key: str,
        task_sequence: list,
        response_callback,
        auto_start: bool = False,
    ) -> None:

        # Default ASR settings
        self.input_audio__streaming_rate = 3200
        self.input_audio__sampling_rate = task_sequence[0]["config"]["samplingRate"]

        self.input_audio__bytes_per_sample = 2 # Do not change
        self.input_audio__num_channels = 1 # Do not change

        self.response_frequency_in_secs = 2.0
        self.transcript_history = ""

        # Parameters
        assert len(task_sequence) == 1, "Only ASR task allowed in sequence"
        self.task_sequence = task_sequence
        self.response_callback = response_callback

        # states
        self.audio_stream = None
        self.is_speaking = False
        self.is_stream_inactive = True

        self.socket_client = self._get_client(
            on_ready=self.start_transcribing_from_mic if auto_start else None
        )

        self.socket_client.connect(
            url=socket_url,
            transports=["websocket", "polling"],
            socketio_path="/socket.io",
            auth={
                "authorization": api_key
            }
        )

    def _get_client(self, on_ready=None) -> socketio.Client:
        sio = socketio.Client(reconnection_attempts=5)

        @sio.event
        def connect():
            print("Socket connected with ID:", sio.get_sid())
            streaming_config = {
                "responseFrequencyInSecs": self.response_frequency_in_secs,
            }
            sio.emit("start", data=(self.task_sequence, streaming_config))
        
        @sio.event
        def connect_error(data):
            print("The connection failed!")
        
        @sio.on('ready')
        def ready():
            self.is_stream_inactive = False
            print("Server ready to receive data from client")
            if on_ready:
                on_ready()
        
        @sio.on('response')
        def response(response, streaming_status):
            print(response)
            print()
            
            if streaming_status["isIntermediateResult"]:
                current_transcript = response["pipelineResponse"][0]["output"][0]["source"]
                self.response_callback(self.transcript_history, current_transcript)
                print("transcript printing")
            else:
                current_transcript = '. '.join(chunk["source"] for chunk in response["pipelineResponse"][0]["output"] if chunk["source"].strip())
                self.response_callback(self.transcript_history, current_transcript)
                print("transcript printing 1")
                if current_transcript.strip():
                    self.transcript_history += current_transcript + '. '
                    print("transcript printing 2")
        
        @sio.on('abort')
        def abort(message):
            print("Connection aborted with message:")
            print(message)

        @sio.on('terminate')
        def terminate():
            sio.disconnect()
            if self.audio_stream:
                # Probably server-side terminated first
                self.audio_stream.stop_stream()
                self.audio_stream = None

        @sio.event
        def disconnect():
            if not self.is_stream_inactive:
                print("Force-disconnected by server, press Enter to stop client.")
            else:
                print("Stream disconnected!")

        return sio

    def stop(self) -> None:
        print("Stopping...")
        if self.audio_stream:
            self.audio_stream.stop_stream()
        else:
            # Likely that already somehow force-stopped
            return

        self.is_speaking = False
        self._transmit_end_of_stream()

        # Wait till stream is disconnected
        self.socket_client.wait()

    def force_disconnect(self, sig=None, frame=None) -> None:
        self.socket_client.disconnect()
    
    def _create_audio_stream(self) -> pyaudio.Stream:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(self.input_audio__bytes_per_sample),
            channels=self.input_audio__num_channels,
            rate=self.input_audio__sampling_rate,
            input=True,
            output=False,
            frames_per_buffer=self.input_audio__streaming_rate,
            stream_callback=self.recorder_callback,
        )
        return stream
    
    def start_transcribing_from_mic(self) -> None:
        self.is_speaking = True
        self.audio_stream = self._create_audio_stream()
        print("START SPEAKING NOW!!!")
    
    def recorder_callback(self, in_data, frame_count, time_info, status_flags) -> tuple:
        if self.is_speaking:
            # print("is speaking now")
            # print(in_data)
            input_data = {
                "audio": [{
                    "audioContent": in_data
                }]
            }
            clear_server_state = not self.is_speaking
            streaming_config = {}
            self.socket_client.emit("data", data=(input_data, streaming_config, clear_server_state, self.is_stream_inactive))
        return (None, pyaudio.paContinue)
    
    def _transmit_end_of_stream(self) -> None:
        # Convey that speaking has stopped
        clear_server_state = not self.is_speaking
        self.socket_client.emit("data", (None, None, clear_server_state, self.is_stream_inactive))
        # Convey that we can close the stream safely
        self.is_stream_inactive = True
        self.socket_client.emit("data", (None, None, clear_server_state, self.is_stream_inactive))
