"""
Face Recognition Service - Using DeepFace for face detection and verification
"""

import json
import logging
import numpy as np
from typing import Optional, List, Tuple
from pathlib import Path
import io
import os
import tempfile
from PIL import Image
import base64

# Initialize logger first
logger = logging.getLogger(__name__)

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    logger.info("DeepFace library loaded successfully")
except ImportError as e:
    DEEPFACE_AVAILABLE = False
    logger.warning(f"DeepFace not available: {e}. Install with: pip install deepface")
except Exception as e:
    DEEPFACE_AVAILABLE = False
    logger.error(f"Error loading DeepFace: {e}", exc_info=True)


# Distance threshold for face verification (adjust based on your needs)
# Note: For VGG-Face with 4096 dimensions, the threshold may need to be higher
FACE_VERIFICATION_THRESHOLD = 0.6  # Lower = stricter (0.3-0.6 typical range for 128-dim, 0.6-0.8 for 4096-dim)


def extract_face_embedding(image_data: bytes) -> Optional[List[float]]:
    """
    Extract face embedding from image data.
    
    Args:
        image_data: Image bytes (JPEG, PNG, etc.)
    
    Returns:
        List of 128 floats (embedding) or None if no face detected or multiple faces
    """
    if not DEEPFACE_AVAILABLE:
        raise ImportError("DeepFace library is not installed. Install with: pip install deepface")
    
    if not image_data:
        raise ValueError("Empty image data provided")
    
    try:
        # Load image from bytes
        try:
            image = Image.open(io.BytesIO(image_data))
            if image is None:
                raise ValueError("Could not open image from bytes")
        except Exception as e:
            raise ValueError(f"Invalid image format: {e}")
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Verify image has valid dimensions
        if image.size[0] == 0 or image.size[1] == 0:
            raise ValueError("Image has invalid dimensions")
        
        # DeepFace expects a file path or numpy array
        # Convert PIL image to numpy array first (fallback method)
        img_array = np.array(image)
        
        if img_array is None or img_array.size == 0:
            raise ValueError("Could not convert image to numpy array")
        
        logger.debug(f"Image array shape: {img_array.shape}, dtype: {img_array.dtype}")
        
        # Extract embedding using DeepFace
        # Try with numpy array first, if that fails, use temporary file
        embedding_obj = None
        temp_file_path = None
        
        try:
            # Method 1: Try with temporary file (more reliable with DeepFace)
            try:
                # Save to temporary file first (DeepFace works better with file paths)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    image.save(tmp_file.name, format='JPEG', quality=95)
                    temp_file_path = tmp_file.name
                
                logger.debug(f"Calling DeepFace.represent with temporary file: {temp_file_path}")
                embedding_obj = DeepFace.represent(
                    img_path=temp_file_path,
                    model_name="VGG-Face",
                    enforce_detection=True,
                    detector_backend="opencv"
                )
                logger.debug(f"DeepFace.represent (file) returned {len(embedding_obj) if embedding_obj else 0} results")
            except (AttributeError, TypeError, ValueError) as e:
                # If file method fails, try with numpy array as fallback
                logger.debug(f"File method failed: {e}, trying numpy array method")
                
                # Try with numpy array
                embedding_obj = DeepFace.represent(
                    img_path=img_array,
                    model_name="VGG-Face",
                    enforce_detection=True,
                    detector_backend="opencv"
                )
                logger.debug(f"DeepFace.represent (numpy) returned {len(embedding_obj) if embedding_obj else 0} results")
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
        
        # DeepFace.represent returns a list with one dict containing 'embedding'
        if embedding_obj and len(embedding_obj) > 0:
            embedding = embedding_obj[0].get('embedding')
            if embedding is None:
                raise ValueError("No embedding found in DeepFace result")
            
            # Check if multiple faces were detected (should only have 1)
            if len(embedding_obj) > 1:
                logger.warning(f"Multiple faces detected ({len(embedding_obj)}). Using first.")
            
            # Convert to list if it's a numpy array, otherwise it's already a list
            if isinstance(embedding, np.ndarray):
                return embedding.tolist()
            elif isinstance(embedding, list):
                return embedding
            else:
                # Convert other types to list
                try:
                    return list(embedding)
                except Exception as e:
                    raise ValueError(f"Could not convert embedding to list: {e}")
        else:
            return None
                
    except ValueError as e:
        # DeepFace raises ValueError if no face detected or detection fails
        error_msg = str(e).lower() if e else ""
        if "could not detect a face" in error_msg or "face could not be detected" in error_msg:
            raise ValueError("No face detected in the image. Please ensure your face is clearly visible.")
        elif "multiple faces detected" in error_msg or "more than one face" in error_msg:
            raise ValueError("Multiple faces detected. Please ensure only one face is visible.")
        else:
            raise ValueError(f"Face detection failed: {e}")
    except (AttributeError, TypeError) as e:
        # Handle attribute/type errors like 'NoneType' object has no attribute 'split'
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"DeepFace processing error ({type(e).__name__}): {error_msg}", exc_info=True)
        
        # Check for specific error patterns
        error_lower = error_msg.lower()
        if "'nonetype' object has no attribute 'split'" in error_lower:
            raise ValueError("Image format error. The image may be corrupted or in an unsupported format. Please try with a different image (JPEG or PNG recommended).")
        elif "module 'cv2' has no attribute 'imread'" in error_lower or ("cv2" in error_lower and "imread" in error_lower):
            logger.error("OpenCV installation issue detected. cv2.imread not available.")
            raise ValueError("OpenCV installation issue. Please contact support or try reinstalling the application.")
        elif "'nonetype'" in error_lower or "none" in error_lower:
            raise ValueError("Image processing error. Please ensure the image is valid, not corrupted, and contains a clearly visible face.")
        else:
            raise ValueError(f"Image processing error: {error_msg}. Please try with a different image.")
    except Exception as e:
        # Catch any other DeepFace errors
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"DeepFace unexpected error: {error_msg}", exc_info=True)
        raise ValueError(f"Face recognition error: {error_msg}. Please ensure the image is valid and contains a face.")
    
    except ValueError:
        # Re-raise ValueError as-is (already user-friendly)
        raise
    except Exception as e:
        logger.error(f"Error extracting face embedding: {e}", exc_info=True)
        raise ValueError(f"Failed to process image: {e}")


def verify_face(known_embedding_json: str, image_data: bytes) -> Tuple[bool, float]:
    """
    Verify if the face in the image matches the known embedding.
    
    Args:
        known_embedding_json: JSON string of the stored face embedding (list of floats)
        image_data: Image bytes to verify
    
    Returns:
        Tuple of (is_match: bool, distance: float)
        - is_match: True if distance < threshold
        - distance: Cosine distance (lower = more similar)
    """
    if not DEEPFACE_AVAILABLE:
        raise ImportError("DeepFace library is not installed")
    
    try:
        # Parse stored embedding
        known_embedding = json.loads(known_embedding_json)
        if not isinstance(known_embedding, list):
            raise ValueError("Invalid embedding format")
        
        # Extract embedding from new image
        try:
            new_embedding = extract_face_embedding(image_data)
            if new_embedding is None:
                logger.warning("extract_face_embedding returned None - no face detected or extraction failed")
                raise ValueError("No face detected in the image. Please ensure your face is clearly visible.")
        except ValueError as e:
            # extract_face_embedding raised ValueError (e.g., no face detected)
            # Re-raise it so the caller can handle it properly
            logger.warning(f"Face extraction failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting face embedding: {e}", exc_info=True)
            raise ValueError(f"Failed to extract face from image: {e}")
        
        # Calculate cosine distance
        known_vec = np.array(known_embedding)
        new_vec = np.array(new_embedding)
        
        # Normalize vectors
        known_norm = known_vec / (np.linalg.norm(known_vec) + 1e-8)
        new_norm = new_vec / (np.linalg.norm(new_vec) + 1e-8)
        
        # Cosine distance = 1 - cosine similarity
        cosine_similarity = np.dot(known_norm, new_norm)
        distance = 1.0 - cosine_similarity
        
        # Log the distance for debugging
        logger.info(f"Face verification: distance={distance:.4f}, threshold={FACE_VERIFICATION_THRESHOLD}, similarity={cosine_similarity:.4f}")
        
        # Check if match (lower distance = more similar)
        is_match = distance < FACE_VERIFICATION_THRESHOLD
        
        return is_match, float(distance)
    
    except Exception as e:
        print(f"Error verifying face: {e}")
        return False, float('inf')


def embedding_to_json(embedding: List[float]) -> str:
    """Convert embedding list to JSON string for storage"""
    return json.dumps(embedding)


def json_to_embedding(embedding_json: str) -> Optional[List[float]]:
    """Parse JSON string back to embedding list"""
    try:
        return json.loads(embedding_json)
    except (json.JSONDecodeError, TypeError):
        return None

