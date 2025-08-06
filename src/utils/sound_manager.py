"""Sound Manager for playing audio notifications.

Provides functionality to play sound effects for various UI events,
particularly error notifications.
"""

import threading
from pathlib import Path

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


class SoundManager:
    """Manages sound playback for UI notifications."""
    
    def __init__(self):
        self.sounds_enabled = True
        self.volume = 0.7
        self.sounds_path = Path(__file__).parent.parent.parent / "assets" / "sounds"
        self._pygame_initialized = False

        # Initialize pygame mixer if available
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self._pygame_initialized = True
            except pygame.error:
                self._pygame_initialized = False

    def play_error_sound(self) -> None:
        """Play error notification sound."""
        if not self.sounds_enabled:
            return

        error_sound_path = self.sounds_path / "error-emotion.mp3"

        if not error_sound_path.exists():
            # Fallback to system beep if file doesn't exist
            self._play_system_beep()
            return

        # Try to play the sound file
        self._play_sound_file(str(error_sound_path))

    def play_warning_sound(self) -> None:
        """Play warning notification sound."""
        if not self.sounds_enabled:
            return

        # For now, use the same error sound for warnings
        # You can add a separate warning sound file later
        self.play_error_sound()

    def play_success_sound(self) -> None:
        """Play success notification sound."""
        if not self.sounds_enabled:
            return

        # For now, just a gentle system sound
        # You can add a separate success sound file later
        if WINSOUND_AVAILABLE:
            threading.Thread(target=lambda: winsound.MessageBeep(winsound.MB_OK), daemon=True).start()

    def _play_sound_file(self, file_path: str) -> None:
        """Play a sound file using available audio libraries."""
        def play_async():
            try:
                if self._pygame_initialized:
                    self._play_with_pygame(file_path)
                elif WINSOUND_AVAILABLE and file_path.endswith('.wav'):
                    self._play_with_winsound(file_path)
                else:
                    self._play_system_beep()
            except Exception:
                # Fallback to system beep if all else fails
                self._play_system_beep()

        # Play sound in a separate thread to avoid blocking UI
        threading.Thread(target=play_async, daemon=True).start()

    def _play_with_pygame(self, file_path: str) -> None:
        """Play sound using pygame."""
        try:
            sound = pygame.mixer.Sound(file_path)
            sound.set_volume(self.volume)
            sound.play()
        except pygame.error:
            raise

    def _play_with_winsound(self, file_path: str) -> None:
        """Play sound using winsound (Windows only, WAV files only)."""
        try:
            winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            raise

    def _play_system_beep(self) -> None:
        """Play system beep as fallback."""
        def beep_async():
            try:
                if WINSOUND_AVAILABLE:
                    winsound.MessageBeep(winsound.MB_ICONERROR)
                else:
                    # Cross-platform fallback
                    print('\a')  # ASCII bell character
            except Exception:
                pass
        
        threading.Thread(target=beep_async, daemon=True).start()

    def set_volume(self, volume: float) -> None:
        """Set playback volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))

    def enable_sounds(self, enabled: bool = True) -> None:
        """Enable or disable sound playback."""
        self.sounds_enabled = enabled

    def is_sounds_enabled(self) -> bool:
        """Check if sounds are enabled."""
        return self.sounds_enabled

    def test_error_sound(self) -> bool:
        """Test if error sound can be played. Returns True if successful."""
        error_sound_path = self.sounds_path / "error-emotion.mp3"
        
        if not error_sound_path.exists():
            return False

        try:
            self.play_error_sound()
            return True
        except Exception:
            return False


# Global sound manager instance
_sound_manager = None


def get_sound_manager() -> SoundManager:
    """Get the global sound manager instance."""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager


def play_error_sound() -> None:
    """Convenience function to play error sound."""
    get_sound_manager().play_error_sound()


def play_warning_sound() -> None:
    """Convenience function to play warning sound."""
    get_sound_manager().play_warning_sound()


def play_success_sound() -> None:
    """Convenience function to play success sound."""
    get_sound_manager().play_success_sound()