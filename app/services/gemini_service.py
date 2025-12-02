import os
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


def get_gemini_client():
    """Initialize Gemini client"""
    try:
        api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            error_msg = "GEMINI_API_KEY not found in environment variables or settings"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash (can be changed to gemini-2.0-flash-exp or other models)
        model_name = os.getenv('GEMINI_MODEL') or getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
        logger.debug(f"Initializing Gemini model: {model_name}")
        return genai.GenerativeModel(model_name)
    
    except Exception as e:
        logger.error(f"Error initializing Gemini client: {str(e)}", exc_info=True)
        raise


def generate_prompt_suggestion(template: str, data_fields: list) -> str:
    """
    Sử dụng Gemini để suggest prompt tốt hơn dựa trên template và data fields
    
    Args:
        template: Prompt template hiện tại với {{field}} placeholders
        data_fields: Danh sách các field names từ CSV/Excel
    
    Returns:
        Enhanced prompt suggestion từ Gemini
    
    Raises:
        ValueError: Nếu template hoặc data_fields rỗng
        Exception: Nếu có lỗi khi gọi Gemini API
    """
    if not template or not template.strip():
        error_msg = "Template cannot be empty"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not data_fields or len(data_fields) == 0:
        error_msg = "Data fields list cannot be empty"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        logger.info(f"Generating prompt suggestion with {len(data_fields)} fields")
        model = get_gemini_client()
        
        fields_description = ", ".join([f"{{{{{field}}}}}" for field in data_fields])
        
        prompt = f"""Bạn là một chuyên gia viết prompt cho video generation.

Template prompt hiện tại:
{template}

Các trường dữ liệu có sẵn:
{fields_description}

Hãy cải thiện prompt này để:
1. Sử dụng tất cả các trường dữ liệu một cách tự nhiên và phù hợp
2. Tạo prompt chi tiết, mô tả rõ ràng cho video generation
3. Giữ nguyên format {{field}} placeholders
4. Làm cho prompt hấp dẫn và dễ hiểu hơn

Chỉ trả về prompt đã được cải thiện, không thêm giải thích hay comment."""

        response = model.generate_content(prompt)
        
        if not response or not response.text:
            error_msg = "Empty response from Gemini API"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        suggested_prompt = response.text.strip()
        logger.info(f"Successfully generated prompt suggestion (length: {len(suggested_prompt)})")
        return suggested_prompt
    
    except ValueError:
        raise
    except Exception as e:
        error_msg = f"Error calling Gemini API: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg) from e


def enhance_prompt(template: str, data_fields: list, context: str = "") -> str:
    """
    Enhance prompt với context bổ sung
    
    Args:
        template: Prompt template hiện tại
        data_fields: Danh sách các field names
        context: Context bổ sung (optional)
    
    Returns:
        Enhanced prompt
    
    Raises:
        ValueError: Nếu template hoặc data_fields rỗng
        Exception: Nếu có lỗi khi gọi Gemini API
    """
    if not template or not template.strip():
        error_msg = "Template cannot be empty"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not data_fields or len(data_fields) == 0:
        error_msg = "Data fields list cannot be empty"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        logger.info(f"Enhancing prompt with {len(data_fields)} fields, context: {bool(context)}")
        model = get_gemini_client()
        
        fields_description = ", ".join([f"{{{{{field}}}}}" for field in data_fields])
        
        prompt = f"""Cải thiện prompt video generation sau đây:

Template:
{template}

Các trường dữ liệu: {fields_description}
{f'Context bổ sung: {context}' if context else ''}

Hãy tạo một prompt chi tiết, hấp dẫn cho video generation, sử dụng tất cả các trường dữ liệu một cách tự nhiên.
Giữ nguyên format {{field}} placeholders.
Chỉ trả về prompt đã cải thiện."""

        response = model.generate_content(prompt)
        
        if not response or not response.text:
            error_msg = "Empty response from Gemini API"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        enhanced_prompt = response.text.strip()
        logger.info(f"Successfully enhanced prompt (length: {len(enhanced_prompt)})")
        return enhanced_prompt
    
    except ValueError:
        raise
    except Exception as e:
        error_msg = f"Error enhancing prompt with Gemini: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg) from e

