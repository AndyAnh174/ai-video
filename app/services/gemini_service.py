import os
import google.generativeai as genai
from django.conf import settings


def get_gemini_client():
    """Initialize Gemini client"""
    api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables or settings")
    
    genai.configure(api_key=api_key)
    # Using gemini-1.5-flash (can be changed to gemini-2.0-flash-exp or other models)
    model_name = os.getenv('GEMINI_MODEL') or getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
    return genai.GenerativeModel(model_name)


def generate_prompt_suggestion(template: str, data_fields: list) -> str:
    """
    Sử dụng Gemini để suggest prompt tốt hơn dựa trên template và data fields
    
    Args:
        template: Prompt template hiện tại với {{field}} placeholders
        data_fields: Danh sách các field names từ CSV/Excel
    
    Returns:
        Enhanced prompt suggestion từ Gemini
    """
    try:
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
        return response.text.strip()
    
    except Exception as e:
        raise Exception(f"Error calling Gemini API: {str(e)}")


def enhance_prompt(template: str, data_fields: list, context: str = "") -> str:
    """
    Enhance prompt với context bổ sung
    
    Args:
        template: Prompt template hiện tại
        data_fields: Danh sách các field names
        context: Context bổ sung (optional)
    
    Returns:
        Enhanced prompt
    """
    try:
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
        return response.text.strip()
    
    except Exception as e:
        raise Exception(f"Error enhancing prompt with Gemini: {str(e)}")

