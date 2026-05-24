import modal

MODEL_NAME = "large-v3"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "faster-whisper==1.1.1",
        "ctranslate2==4.5.0",
        "nvidia-cudnn-cu12==9.1.0.70",
        "nvidia-cublas-cu12",
        "requests",
    )
    .env(
        {
            "LD_LIBRARY_PATH": "/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib:/usr/local/lib/python3.11/site-packages/nvidia/cublas/lib"
        }
    )
)

app = modal.App("voice-to-text-whisper", image=image)

model_cache = modal.Volume.from_name("faster-whisper-cache", create_if_missing=True)
CACHE_DIR = "/cache"


@app.cls(
    gpu="T4",
    scaledown_window=300,
    timeout=600,
    volumes={CACHE_DIR: model_cache},
)
class Whisper:
    @modal.enter()
    def load(self):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(
            MODEL_NAME,
            device="cuda",
            compute_type="float16",
            download_root=CACHE_DIR,
        )

    @modal.method()
    def transcribe(self, audio_bytes: bytes) -> dict:
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            path = f.name
        try:
            segments, info = self.model.transcribe(
                path,
                beam_size=5,
                vad_filter=True,
                initial_prompt="Hello, welcome. This is a transcript with proper punctuation, including commas, periods, and question marks. Isn't it nice?",
            )
            text = "".join(seg.text for seg in segments).strip()
        finally:
            os.unlink(path)
        return {"text": text, "language": info.language}
