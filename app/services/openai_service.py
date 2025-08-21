"""
OpenAI service for palm reading analysis.
"""

import base64
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

PALMISTRY_SYSTEM_PROMPT = """You are an expert in Indian palmistry (Hast Rekha Shastra), a traditional practice of reading palms to provide insights about a person's life, personality, and future. You have deep knowledge of:

- Major lines: Life line, Head line, Heart line, Fate line
- Minor lines: Sun line, Mercury line, Mars line, etc.
- Mounts: Venus, Jupiter, Saturn, Sun, Mercury, Mars, Moon
- Hand shapes, finger characteristics, and their meanings
- Traditional Indian palmistry interpretations and cultural context

When analyzing palm images:
1. Provide both a brief summary (2-3 sentences) and a detailed analysis
2. Focus on positive insights while being honest about challenges
3. Use traditional Indian palmistry terminology and concepts
4. Explain what specific features you observe and their meanings
5. Be respectful of the cultural and spiritual aspects of palmistry
6. If image quality is poor, mention limitations in your analysis

Remember: Palmistry is for guidance and entertainment. Always encourage users to make their own life decisions.
"""

class OpenAIService:
    """Service for OpenAI GPT-4 Vision integration."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64 for OpenAI API.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string or None if error
        """
        try:
            full_path = Path(settings.file_storage_root) / image_path
            with open(full_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None
    
    async def analyze_palm_images(
        self, 
        left_image_path: Optional[str] = None, 
        right_image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze palm images using OpenAI GPT-4 Vision.
        
        Args:
            left_image_path: Path to left palm image
            right_image_path: Path to right palm image
            
        Returns:
            Dictionary with summary and full_report
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        if not left_image_path and not right_image_path:
            raise ValueError("At least one palm image is required")
        
        try:
            # Prepare images for analysis
            images = []
            image_descriptions = []
            
            if left_image_path:
                left_b64 = self._encode_image(left_image_path)
                if left_b64:
                    images.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{left_b64}",
                            "detail": "high"
                        }
                    })
                    image_descriptions.append("left palm")
            
            if right_image_path:
                right_b64 = self._encode_image(right_image_path)
                if right_b64:
                    images.append({
                        "type": "image_url", 
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{right_b64}",
                            "detail": "high"
                        }
                    })
                    image_descriptions.append("right palm")
            
            if not images:
                raise ValueError("Unable to process palm images")
            
            # Construct user prompt
            image_description = " and ".join(image_descriptions)
            user_prompt = f"""Please analyze the {image_description} image(s) using traditional Indian palmistry (Hast Rekha Shastra).

Provide your analysis in this exact JSON format:
{{
    "summary": "A brief 2-3 sentence summary suitable for preview",
    "full_report": "A detailed palmistry analysis covering major lines, mounts, and their meanings",
    "key_features": ["list", "of", "key", "observed", "features"],
    "strengths": ["positive", "traits", "and", "characteristics"],
    "guidance": ["life", "guidance", "based", "on", "palm", "reading"]
}}

Focus on traditional Indian palmistry interpretations and provide meaningful insights."""

            # Prepare messages for GPT-4 Vision
            messages = [
                {
                    "role": "system",
                    "content": PALMISTRY_SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": user_prompt},
                        *images
                    ]
                }
            ]
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini as specified in requirements
                messages=messages,
                max_tokens=1500,
                temperature=0.7,
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text processing
            try:
                import json
                analysis_data = json.loads(analysis_text)
                
                summary = analysis_data.get("summary", "Palm analysis completed.")
                full_report = analysis_data.get("full_report", analysis_text)
                
            except json.JSONDecodeError:
                # Fallback: split the response
                lines = analysis_text.split('\n')
                summary = lines[0][:200] + "..." if len(lines[0]) > 200 else lines[0]
                full_report = analysis_text
            
            # Log token usage
            tokens_used = response.usage.total_tokens
            logger.info(f"OpenAI analysis completed. Tokens used: {tokens_used}")
            
            return {
                "summary": summary,
                "full_report": full_report,
                "tokens_used": tokens_used,
                "cost": self._calculate_cost(tokens_used)
            }
            
        except Exception as e:
            logger.error(f"Error in OpenAI palm analysis: {e}")
            raise
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """Calculate approximate cost based on tokens used.
        
        Args:
            tokens_used: Number of tokens used
            
        Returns:
            Estimated cost in USD
        """
        # GPT-4o-mini pricing (approximate)
        # Input: $0.00015 per 1K tokens, Output: $0.0006 per 1K tokens
        # Assuming 70% input, 30% output for cost estimation
        input_tokens = int(tokens_used * 0.7)
        output_tokens = int(tokens_used * 0.3)
        
        input_cost = (input_tokens / 1000) * 0.00015
        output_cost = (output_tokens / 1000) * 0.0006
        
        return round(input_cost + output_cost, 6)
    
    async def generate_conversation_response(
        self, 
        analysis_summary: str,
        analysis_full_report: str,
        conversation_history: list,
        user_question: str
    ) -> Dict[str, Any]:
        """Generate response for follow-up questions about palm analysis.
        
        Args:
            analysis_summary: Summary of the palm analysis
            analysis_full_report: Full palm analysis report
            conversation_history: Previous conversation messages
            user_question: User's follow-up question
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Construct conversation context
            context_prompt = f"""You are continuing a palmistry consultation. Here is the original palm analysis:

SUMMARY: {analysis_summary}

FULL ANALYSIS: {analysis_full_report}

The user now has a follow-up question. Please provide a helpful response based on the palm analysis and traditional Indian palmistry knowledge. Keep your response focused and relevant to their question."""

            # Build conversation messages
            messages = [
                {"role": "system", "content": PALMISTRY_SYSTEM_PROMPT},
                {"role": "assistant", "content": context_prompt}
            ]
            
            # Add conversation history
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current question
            messages.append({
                "role": "user",
                "content": user_question
            })
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.8,
            )
            
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(f"Generated conversation response. Tokens used: {tokens_used}")
            
            return {
                "response": answer,
                "tokens_used": tokens_used,
                "cost": self._calculate_cost(tokens_used)
            }
            
        except Exception as e:
            logger.error(f"Error generating conversation response: {e}")
            raise
    
    async def analyze_palm_with_custom_prompt(
        self, 
        image_data: bytes, 
        custom_prompt: str
    ) -> Dict[str, Any]:
        """Analyze palm with a custom specialized prompt.
        
        Args:
            image_data: Raw image bytes
            custom_prompt: Custom analysis prompt
            
        Returns:
            Dictionary with analysis results
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Encode image data to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare messages
            messages = [
                {"role": "system", "content": PALMISTRY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": custom_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1200,
                temperature=0.7,
            )
            
            analysis = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(f"Custom palm analysis completed. Tokens used: {tokens_used}")
            
            return {
                "analysis": analysis,
                "tokens_used": tokens_used,
                "cost": self._calculate_cost(tokens_used),
                "confidence": 0.8  # Default confidence for custom analysis
            }
            
        except Exception as e:
            logger.error(f"Error in custom palm analysis: {e}")
            raise
    
    async def generate_response(self, prompt: str) -> Dict[str, Any]:
        """Generate a general response using OpenAI.
        
        Args:
            prompt: The prompt to send to OpenAI
            
        Returns:
            Dictionary with response content
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": PALMISTRY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(f"Generated response. Tokens used: {tokens_used}")
            
            return {
                "content": content,
                "tokens_used": tokens_used,
                "cost": self._calculate_cost(tokens_used)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise