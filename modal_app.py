import modal

MODEL_NAME = "large-v3"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "faster-whisper==1.0.3",
        "ctranslate2==4.4.0",
    )
)

app = modal.App("voice-to-text-whisper", image=image)

model_cache = modal.Volume.from_name("faster-whisper-cache", create_if_missing=True)
CACHE_DIR = "/cache"


@app.cls(
    gpu="A10G",
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
            )
            text = "".join(seg.text for seg in segments).strip()
        finally:
            os.unlink(path)
        return {"text": text, "language": info.language}
