"""
Voice Control - Push-to-talk voice commands with whisper-cpp
"""

import sys
import os
import threading
import time
import json
import subprocess
import tempfile

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Add paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="VOICE"):
        print(f"[{category}] {msg}")

try:
    from core.event_bus import publish_event
    from core.config_manager import get_module_config
except ImportError:
    def publish_event(event_type, sender, data=None):
        log(f"Event: {event_type} - {data}", "VOICE")
    def get_module_config(module_id):
        return {}

class VoiceListener:
    """Voice command listener using whisper-cpp"""
    
    def __init__(self):
        self.running = False
        self.listening = False
        self.hotkey = "f9"  # Default push-to-talk key
        self.config = get_module_config("voice_control")
        self.hotkey = self.config.get("hotkey", "f9")
        self.enabled = self.config.get("enabled", True)
        
        # Whisper model path
        self.whisper_path = self.config.get("whisper_path", "whisper-cpp")
        self.model_path = self.config.get("model_path", "models/ggml-small.bin")
        
        # Command mappings
        self.command_map = {
            "start rag api": "start_academic_rag",
            "stop rag api": "stop_academic_rag",
            "start api": "start_academic_rag",
            "stop api": "stop_academic_rag",
            "index documents": "index_documents",
            "reindex": "index_documents",
            "health check": "health_check",
            "open logs": "open_logs",
            "stop all": "stop_all_modules",
            "start all": "start_all_modules"
        }
        
        self.audio_thread = None
        self.hotkey_thread = None
    
    def find_whisper_cpp(self):
        """Find whisper-cpp binary"""
        # Check common locations
        possible_paths = [
            os.path.join(BASE_DIR, "whisper-cpp", "main"),
            os.path.join(BASE_DIR, "whisper-cpp", "main.exe"),
            "whisper-cpp",
            "whisper-cpp.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or self._command_exists(path):
                return path
        
        log("whisper-cpp not found, voice control will use fallback", "VOICE", level="WARNING")
        return None
    
    def _command_exists(self, cmd):
        """Check if command exists in PATH"""
        try:
            result = subprocess.run(
                ["where" if os.name == "nt" else "which", cmd.split()[0]],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False
    
    def record_audio(self, duration=3):
        """Record audio using pyaudio"""
        try:
            import pyaudio
            import wave
            
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            frames = []
            log("Recording audio...", "VOICE")
            
            for _ in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save to temp file
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_wav.close()
            
            wf = wave.open(temp_wav.name, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            return temp_wav.name
            
        except ImportError:
            log("pyaudio not installed, voice recording disabled", "VOICE", level="WARNING")
            return None
        except Exception as e:
            log(f"Error recording audio: {e}", "VOICE", level="ERROR")
            return None
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio using whisper-cpp"""
        whisper_cmd = self.find_whisper_cpp()
        
        if not whisper_cmd:
            # Fallback: return mock transcription for testing
            log("Using fallback transcription (mock)", "VOICE", level="WARNING")
            return "test command"
        
        try:
            # Run whisper-cpp
            cmd = [
                whisper_cmd,
                "-m", self.model_path,
                "-f", audio_file,
                "--no-timestamps",
                "--output-txt"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(whisper_cmd) if os.path.dirname(whisper_cmd) else None
            )
            
            if result.returncode == 0:
                # Read transcription from .txt file
                txt_file = audio_file.replace('.wav', '.txt')
                if os.path.exists(txt_file):
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        transcript = f.read().strip()
                    os.remove(txt_file)
                    return transcript
                else:
                    # Try stdout
                    return result.stdout.strip()
            else:
                log(f"whisper-cpp error: {result.stderr}", "VOICE", level="ERROR")
                return None
                
        except Exception as e:
            log(f"Error transcribing audio: {e}", "VOICE", level="ERROR")
            return None
        finally:
            # Cleanup temp file
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except:
                pass
    
    def process_command(self, text):
        """Process voice command text"""
        text_lower = text.lower().strip()
        
        log(f"Processing voice command: '{text_lower}'", "VOICE")
        
        # Store command in memory
        try:
            from core.memory_manager import get_memory_manager
            memory = get_memory_manager()
            timestamp = int(time.time())
            memory.remember(
                "julian",
                f"voice_command_{timestamp}",
                text_lower,
                category="voice_commands",
                confidence=0.9
            )
        except:
            pass
        
        # Find matching command
        matched = False
        for cmd_text, action in self.command_map.items():
            if cmd_text in text_lower:
                log(f"Matched command: {cmd_text} -> {action}", "VOICE")
                matched = True
                
                # Publish event
                publish_event(
                    "voice.command",
                    "voice_control",
                    {
                        "command": cmd_text,
                        "action": action,
                        "raw_text": text_lower
                    }
                )
                
                return action
        
        if not matched:
            log(f"No command matched for: '{text_lower}'", "VOICE", level="WARNING")
            # Log unknown command for training
            try:
                unknown_log_path = os.path.join(BASE_DIR, "modules", "voice_control", "config", "unknown_commands.log")
                with open(unknown_log_path, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: {text_lower}\n")
            except:
                pass
        
        return None
    
    def hotkey_monitor(self):
        """Monitor hotkey for push-to-talk"""
        try:
            import keyboard
            
            log(f"Voice control hotkey: {self.hotkey.upper()}", "VOICE")
            
            while self.running:
                try:
                    # Wait for hotkey press
                    keyboard.wait(self.hotkey)
                    
                    if not self.enabled:
                        continue
                    
                    if self.listening:
                        # Release - stop recording
                        self.listening = False
                        log("Stopped listening", "VOICE")
                    else:
                        # Press - start recording
                        self.listening = True
                        log("Started listening (push-to-talk)", "VOICE")
                        
                        # Record audio
                        audio_file = self.record_audio(duration=3)
                        if audio_file:
                            # Transcribe
                            transcript = self.transcribe_audio(audio_file)
                            if transcript:
                                # Process command
                                self.process_command(transcript)
                            
                            self.listening = False
                            time.sleep(0.5)  # Debounce
                            
                except keyboard.HookException:
                    # Hotkey not available
                    log(f"Hotkey {self.hotkey} not available", "VOICE", level="WARNING")
                    time.sleep(1)
                    break
                except Exception as e:
                    log(f"Error in hotkey monitor: {e}", "VOICE", level="ERROR")
                    time.sleep(1)
                    
        except ImportError:
            log("keyboard module not installed, hotkey monitoring disabled", "VOICE", level="WARNING")
        except Exception as e:
            log(f"Error starting hotkey monitor: {e}", "VOICE", level="ERROR")
    
    def start(self):
        """Start voice listener"""
        if self.running:
            return
        
        self.running = True
        
        if not self.enabled:
            log("Voice control is disabled", "VOICE")
            return
        
        # Start hotkey monitor thread
        self.hotkey_thread = threading.Thread(target=self.hotkey_monitor, daemon=True)
        self.hotkey_thread.start()
        
        log("Voice control started", "VOICE")
    
    def stop(self):
        """Stop voice listener"""
        self.running = False
        self.listening = False
        log("Voice control stopped", "VOICE")

def main():
    """Main entry point for voice listener"""
    listener = VoiceListener()
    
    try:
        listener.start()
        
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()

if __name__ == "__main__":
    main()

