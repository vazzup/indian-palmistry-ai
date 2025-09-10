"""
OpenAI service for palm reading analysis.
"""

import base64
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from openai import AsyncOpenAI
from fastapi import UploadFile
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
    """Service for OpenAI GPT-4 Vision and Assistants API integration."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Assistant ID no longer needed - using Responses API
    
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
        right_image_path: Optional[str] = None,
        left_file_id: Optional[str] = None,
        right_file_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """DEPRECATED: Use analyze_palm_images_with_responses() instead.
        
        This method uses the older Chat Completions API and is deprecated.
        Use analyze_palm_images_with_responses() which uses the newer Responses API
        for better image handling and consistent formatting.
        
        Analyze palm images using OpenAI GPT-4 Vision.
        
        Args:
            left_image_path: Path to left palm image (legacy, for backward compatibility)
            right_image_path: Path to right palm image (legacy, for backward compatibility)  
            left_file_id: OpenAI file ID for left palm image
            right_file_id: OpenAI file ID for right palm image
            
        Returns:
            Dictionary with summary and full_report
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        # Check if we have either file IDs or paths
        has_left = left_file_id or left_image_path
        has_right = right_file_id or right_image_path
        
        if not has_left and not has_right:
            raise ValueError("At least one palm image is required")
        
        try:
            # Prepare images for analysis
            images = []
            image_descriptions = []
            
            # Handle left palm
            if left_file_id:
                # Use OpenAI file reference
                images.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"file://{left_file_id}",
                        "detail": "high"
                    }
                })
                image_descriptions.append("left palm")
            elif left_image_path:
                # Fallback to base64 encoding for legacy support
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
            
            # Handle right palm
            if right_file_id:
                # Use OpenAI file reference
                images.append({
                    "type": "image_url", 
                    "image_url": {
                        "url": f"file://{right_file_id}",
                        "detail": "high"
                    }
                })
                image_descriptions.append("right palm")
            elif right_image_path:
                # Fallback to base64 encoding for legacy support
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
            
            # Try to parse as JSON, handling markdown code blocks
            try:
                import json
                import re
                
                # Remove markdown code blocks if present
                clean_text = analysis_text.strip()
                if clean_text.startswith('```json'):
                    clean_text = re.sub(r'^```json\s*\n?', '', clean_text)
                if clean_text.endswith('```'):
                    clean_text = re.sub(r'\n?```$', '', clean_text)
                elif clean_text.startswith('```'):
                    # Handle cases where it might just be ``` without json
                    clean_text = re.sub(r'^```\s*\n?', '', clean_text)
                    if clean_text.endswith('```'):
                        clean_text = re.sub(r'\n?```$', '', clean_text)
                
                clean_text = clean_text.strip()
                analysis_data = json.loads(clean_text)
                
                summary = analysis_data.get("summary", "Palm analysis completed.")
                full_report = analysis_data.get("full_report", clean_text)
                
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse JSON response: {e}")
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
    
    async def get_file_url(self, file_id: str) -> str:
        """Get URL for accessing an uploaded OpenAI file.
        
        Args:
            file_id: OpenAI file ID
            
        Returns:
            URL to access the file
        """
        # For OpenAI files, we typically reference them by file_id
        # The actual URL construction depends on how you want to serve them
        return f"openai://file/{file_id}"
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from OpenAI storage.
        
        Args:
            file_id: OpenAI file ID
            
        Returns:
            True if successfully deleted
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            await self.client.files.delete(file_id)
            logger.info(f"Successfully deleted OpenAI file: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting OpenAI file {file_id}: {e}")
            return False
    
    # DEPRECATED: analyze_palm_images_with_assistant removed
    # Replaced with analyze_palm_images_with_responses() using OpenAI Responses API
    
    async def analyze_palm_images_with_responses(
        self,
        left_file_id: Optional[str] = None,
        right_file_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze palm images using OpenAI Responses API.
        
        Args:
            left_file_id: OpenAI file ID for left palm image
            right_file_id: OpenAI file ID for right palm image
            
        Returns:
            Dictionary with analysis results including all JSON fields
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        if not left_file_id and not right_file_id:
            raise ValueError("At least one palm image file ID is required")
        
        try:
            # Prepare content for message
            content_parts = []
            image_descriptions = []
            
            # Add text prompt
            image_description = []
            if left_file_id:
                image_description.append("left palm")
            if right_file_id:
                image_description.append("right palm")
            
            image_desc_text = " and ".join(image_description)
            
            user_message = PALMISTRY_SYSTEM_PROMPT + f"""Please analyze the {image_desc_text} image(s) using traditional Indian palmistry (Hast Rekha Shastra).

Provide your analysis in this exact JSON format:
{{
    "summary": "A brief 2-3 sentence summary suitable for preview",
    "full_report": "A detailed palmistry analysis covering major lines (including love line, health line, career line, etc), mounts, and their meanings. Speak at length. Atleast between 200-250 words",
    "key_features": ["list", "of", "key", "observed", "features"],
    "strengths": ["positive", "traits", "and", "characteristics"],
    "guidance": ["life", "guidance", "based", "on", "palm", "reading"]
}}

For key_features, guidance, and strength, don't send one words. Send full sentences in the list.

Focus on traditional Indian palmistry interpretations and provide meaningful insights."""
            
            content_parts.append({
                "type": "input_text",
                "text": user_message
            })
            
            # Add file inputs
            if left_file_id:
                content_parts.append({
                    "type": "input_image",
                    "file_id": left_file_id
                })
            
            if right_file_id:
                content_parts.append({
                    "type": "input_image", 
                    "file_id": right_file_id
                })
            
            # Create response using Responses API
            response = await self.client.responses.create(
                model="gpt-4.1-mini",
                input=[{
                    "role": "user",
                    "content": content_parts
                }]
            )
            
            # Get the response text
            response_content = response.output_text
            
            # Parse the JSON response
            try:
                import json
                import re
                
                # Clean up response
                clean_text = response_content.strip()
                if clean_text.startswith('```json'):
                    clean_text = re.sub(r'^```json\s*\n?', '', clean_text)
                if clean_text.endswith('```'):
                    clean_text = re.sub(r'\n?```$', '', clean_text)
                elif clean_text.startswith('```'):
                    clean_text = re.sub(r'^```\s*\n?', '', clean_text)
                    if clean_text.endswith('```'):
                        clean_text = re.sub(r'\n?```$', '', clean_text)
                
                clean_text = clean_text.strip()
                analysis_data = json.loads(clean_text)
                
                summary = analysis_data.get("summary", "Palm analysis completed.")
                full_report = analysis_data.get("full_report", clean_text)
                key_features = analysis_data.get("key_features", [])
                strengths = analysis_data.get("strengths", [])
                guidance = analysis_data.get("guidance", [])
                
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                # Fallback
                lines = response_content.split('\n')
                summary = lines[0][:200] + "..." if len(lines[0]) > 200 else lines[0]
                full_report = response_content
                key_features = []
                strengths = []
                guidance = []
            
            # Calculate token usage (approximation for Responses API)
            tokens_used = len(response_content.split()) * 1.3
            
            logger.info(f"Responses API analysis completed. Tokens used (approx): {int(tokens_used)}")
            
            return {
                "summary": summary,
                "full_report": full_report,
                "key_features": key_features,
                "strengths": strengths,
                "guidance": guidance,
                "tokens_used": int(tokens_used),
                "cost": self._calculate_cost(int(tokens_used))
            }
            
        except Exception as e:
            logger.error(f"Error in Responses API palm analysis: {e}")
            raise

    async def generate_conversation_response_with_images(
        self,
        analysis_summary: str,
        analysis_full_report: str,
        key_features: list,
        strengths: list,
        guidance: list,
        left_file_id: Optional[str] = None,
        right_file_id: Optional[str] = None,
        conversation_history: list = None,
        user_question: str = ""
    ) -> Dict[str, Any]:
        """Generate conversation response with palm images using OpenAI Responses API.
        
        This method provides full visual context by including the original palm images
        along with the complete analysis and conversation history.
        
        Args:
            analysis_summary: Summary of the original palm analysis
            analysis_full_report: Detailed palm analysis report
            key_features: List of key observed features from analysis
            strengths: List of positive traits from analysis
            guidance: List of life guidance from analysis
            left_file_id: OpenAI file ID for left palm image
            right_file_id: OpenAI file ID for right palm image
            conversation_history: Previous conversation messages
            user_question: Current user question
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        if not left_file_id and not right_file_id:
            raise ValueError("At least one palm image file ID is required")
        
        if conversation_history is None:
            conversation_history = []
        
        try:
            # Build complete conversation context
            image_description = []
            if left_file_id:
                image_description.append("left palm")
            if right_file_id:
                image_description.append("right palm")
            
            image_desc_text = " and ".join(image_description)
            
            # Construct full context with original analysis
            context_parts = [
                f"{PALMISTRY_SYSTEM_PROMPT}\n",
                "ORIGINAL PALM ANALYSIS:",
                f"Summary: {analysis_summary}",
                f"Full Report: {analysis_full_report}",
                f"Key Features: {', '.join(key_features) if key_features else 'None specified'}",
                f"Strengths: {', '.join(strengths) if strengths else 'None specified'}",
                f"Guidance: {', '.join(guidance) if guidance else 'None specified'}",
                ""
            ]
            
            # Add conversation history if present
            if conversation_history:
                context_parts.append("CONVERSATION HISTORY:")
                for msg in conversation_history:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    context_parts.append(f"{role}: {msg.get('content', '')}")
                context_parts.append("")
            
            # Add current question
            context_parts.extend([
                f"The user is now asking about the {image_desc_text} shown in the images:",
                f"Question: {user_question}",
                "",
                "Please provide a helpful response based on the palm analysis and images. Reference specific visual features you can observe in the palm images when relevant to the question. Use traditional Indian palmistry knowledge and keep your response focused and detailed."
            ])
            
            full_context = "\n".join(context_parts)
            
            # Prepare content parts for OpenAI Responses API
            content_parts = [{
                "type": "input_text",
                "text": full_context
            }]
            
            # Add image file references
            if left_file_id:
                content_parts.append({
                    "type": "input_image",
                    "file_id": left_file_id
                })
            
            if right_file_id:
                content_parts.append({
                    "type": "input_image",
                    "file_id": right_file_id
                })
            
            # Create response using Responses API
            response = await self.client.responses.create(
                model="gpt-4.1-mini",
                input=[{
                    "role": "user",
                    "content": content_parts
                }]
            )
            
            # Get the response text
            response_content = response.output_text
            
            # Calculate tokens and cost (approximate for Responses API)
            input_tokens = len(full_context.split()) * 1.3  # Rough approximation
            output_tokens = len(response_content.split()) * 1.3
            total_tokens = int(input_tokens + output_tokens)
            
            logger.info(f"Generated conversation response with images. Approximate tokens: {total_tokens}")
            
            return {
                "response": response_content,
                "tokens_used": total_tokens,
                "cost": self._calculate_cost(total_tokens)
            }
            
        except Exception as e:
            logger.error(f"Error generating conversation response with images: {e}")
            raise

    async def generate_conversation_response_with_assistant(
        self,
        thread_id: str,
        user_question: str
    ) -> Dict[str, Any]:
        """Generate response for follow-up questions using existing assistant thread.
        
        Args:
            thread_id: OpenAI thread ID from the original analysis
            user_question: User's follow-up question
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        if not self.assistant_id:
            raise ValueError("OpenAI Assistant ID not configured")
        
        try:
            import asyncio
            
            # Add user message to the existing thread
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_question
            )
            
            # Create and run the assistant on the existing thread
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            # Poll for completion
            while run.status in ['queued', 'in_progress']:
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status != 'completed':
                raise Exception(f"Run failed with status: {run.status}")
            
            # Get the latest assistant response
            messages = await self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=1
            )
            
            if not messages.data:
                raise Exception("No response from assistant")
            
            # Get the most recent message (should be assistant's response)
            latest_message = messages.data[0]
            if latest_message.role != 'assistant':
                raise Exception("Expected assistant response but got user message")
            
            response_content = latest_message.content[0].text.value
            
            # Calculate token usage (approximation)
            tokens_used = len(response_content.split()) * 1.3
            
            logger.info(f"Generated assistant conversation response. Thread ID: {thread_id}")
            
            return {
                "response": response_content,
                "tokens_used": int(tokens_used),
                "cost": self._calculate_cost(int(tokens_used))
            }
            
        except Exception as e:
            logger.error(f"Error generating assistant conversation response: {e}")
            raise
