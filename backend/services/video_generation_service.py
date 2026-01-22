"""
Video Generation Service
Service for converting text modules into narrated videos
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import os
import subprocess
import tempfile

from config import settings

logger = logging.getLogger(__name__)

# Try to import TTS libraries
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS is not installed. Install with: pip install gtts")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 is not installed. Install with: pip install pyttsx3")


class VideoGenerationService:
    """Service for generating narrated videos from text"""
    
    def __init__(self):
        """Initialize video generation service"""
        self.media_root = Path(settings.MEDIA_ROOT)
        self.videos_dir = self.media_root / "videos"
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for ffmpeg (required for video creation)
        self.ffmpeg_available = self._check_ffmpeg()
        if not self.ffmpeg_available:
            logger.warning("ffmpeg not found. Video generation will be limited.")
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def generate_video_from_text(
        self,
        text: str,
        title: str,
        formation_id: int,
        module_id: int,
        language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Generate a narrated video from text content
        
        Args:
            text: Text content to convert to video
            title: Video title
            formation_id: Formation ID
            module_id: Module ID
            language: Language code (fr, en, etc.)
            
        Returns:
            Dictionary with video_url and duration
        """
        try:
            # Step 1: Generate audio narration
            audio_path = await self._generate_audio(text, title, formation_id, module_id, language)
            
            # Step 2: Create video with slides (text overlay)
            video_path = await self._create_video_with_slides(
                text, title, audio_path, formation_id, module_id
            )
            
            # Step 3: Calculate duration
            duration = self._get_video_duration(video_path)
            
            # Generate URL
            video_filename = f"formation_{formation_id}_module_{module_id}.mp4"
            video_url = f"{settings.MEDIA_URL}videos/{video_filename}"
            
            # Move to final location
            final_path = self.videos_dir / video_filename
            if os.path.exists(video_path):
                import shutil
                shutil.move(video_path, final_path)
            
            return {
                "video_url": video_url,
                "duration": duration,
                "file_path": str(final_path)
            }
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            # Return placeholder URL if generation fails
            return {
                "video_url": None,
                "duration": 0,
                "error": str(e)
            }
    
    async def _generate_audio(
        self,
        text: str,
        title: str,
        formation_id: int,
        module_id: int,
        language: str
    ) -> str:
        """Generate audio narration from text"""
        # Clean and prepare text
        clean_text = self._clean_text_for_speech(text)
        
        # Limit text length (gTTS has limits)
        max_length = 5000
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "..."
        
        # Create temp directory for audio
        temp_dir = Path(tempfile.gettempdir()) / "video_gen"
        temp_dir.mkdir(exist_ok=True)
        audio_path = temp_dir / f"audio_{formation_id}_{module_id}.mp3"
        
        # Use gTTS (Google Text-to-Speech) - free, no API key needed
        if GTTS_AVAILABLE:
            try:
                tts = gTTS(text=clean_text, lang=language, slow=False)
                tts.save(str(audio_path))
                logger.info(f"Generated audio using gTTS: {audio_path}")
                return str(audio_path)
            except Exception as e:
                logger.warning(f"gTTS failed: {e}, trying pyttsx3")
        
        # Fallback to pyttsx3 (offline, but lower quality)
        if PYTTSX3_AVAILABLE:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)  # Speed
                engine.setProperty('volume', 0.9)  # Volume
                
                # Save to file
                engine.save_to_file(clean_text, str(audio_path))
                engine.runAndWait()
                
                if os.path.exists(audio_path):
                    logger.info(f"Generated audio using pyttsx3: {audio_path}")
                    return str(audio_path)
            except Exception as e:
                logger.error(f"pyttsx3 failed: {e}")
        
        raise RuntimeError("No TTS engine available. Install gtts or pyttsx3")
    
    async def _create_video_with_slides(
        self,
        text: str,
        title: str,
        audio_path: str,
        formation_id: int,
        module_id: int
    ) -> str:
        """Create video with text slides and audio"""
        if not self.ffmpeg_available:
            # Without ffmpeg, we can't create videos
            # Return audio path as placeholder
            logger.warning("ffmpeg not available, returning audio only")
            return audio_path
        
        # Split text into slides (chunks for display)
        slides = self._split_text_into_slides(text, max_slides=10)
        
        # Create temp directory
        temp_dir = Path(tempfile.gettempdir()) / "video_gen"
        temp_dir.mkdir(exist_ok=True)
        video_path = temp_dir / f"video_{formation_id}_{module_id}.mp4"
        
        # Create video using ffmpeg
        # Simple approach: Create a video with title slide + content slides
        try:
            # For now, create a simple video with static background and text overlay
            # In production, you might want to use more sophisticated tools like moviepy
            
            # Create a simple video: black background with text
            duration = self._get_audio_duration(audio_path)
            
            # Use ffmpeg to create video with text overlay
            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"color=c=black:s=1280x720:d={duration}",
                "-i", audio_path,
                "-vf", f"drawtext=text='{title}':fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:fontcolor=white",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "-y",
                str(video_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            logger.info(f"Created video: {video_path}")
            return str(video_path)
            
        except Exception as e:
            logger.error(f"Error creating video with ffmpeg: {e}")
            # Return audio path as fallback
            return audio_path
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that don't read well
        text = text.replace('\n', '. ')
        text = text.replace('\t', ' ')
        
        return text.strip()
    
    def _split_text_into_slides(self, text: str, max_slides: int = 10) -> list:
        """Split text into slides for video display"""
        # Simple split by sentences
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Group sentences into slides
        sentences_per_slide = max(1, len(sentences) // max_slides)
        slides = []
        
        for i in range(0, len(sentences), sentences_per_slide):
            slide_text = '. '.join(sentences[i:i + sentences_per_slide])
            if slide_text.strip():
                slides.append(slide_text.strip())
        
        return slides[:max_slides]
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        if not self.ffmpeg_available:
            # Estimate: ~150 words per minute
            return 60.0
        
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 60.0  # Default 1 minute
    
    def _get_video_duration(self, video_path: str) -> int:
        """Get duration of video file in seconds"""
        if not os.path.exists(video_path):
            return 0
        
        if not self.ffmpeg_available:
            return 0
        
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True,
                text=True,
                check=True
            )
            return int(float(result.stdout.strip()))
        except Exception:
            return 0


# Singleton instance
video_generation_service = VideoGenerationService()

