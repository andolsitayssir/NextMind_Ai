"""
OpenRouter API Client for NextMind
Provides unified interface to free OpenRouter models
"""
import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API with free model support"""
    
    MODELS = {
        'reasoning': 'xiaomi/mimo-v2-flash:free',
        'validation': 'nvidia/nemotron-nano-9b-v2:free',
        'fallback': 'mistralai/devstral-2512:free'
    }
    
    def __init__(self, api_key=None):
        """Initialize OpenRouter client"""
        self.api_key = api_key or os.getenv('OPEN_ROUTER_API_KEY', '')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    def generate(self, prompt, model='reasoning', temperature=0.5, response_format=None, max_retries=1):
        """
        Generate text using OpenRouter models
        
        Args:
            prompt: The prompt text
            model: Model type ('reasoning', 'validation', 'fallback')
            temperature: Sampling temperature (0.0-1.0) - lowered to 0.5 for speed
            response_format: 'json' for JSON output, None for text
            max_retries: Number of retry attempts (reduced to 1 for speed)
            
        Returns:
            Generated text or JSON string
        """
        model_name = self.MODELS.get(model, self.MODELS['reasoning'])
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 5000,  # Drastically increased for large batches
            "timeout": 60  # Increased for large generation
        }
        
        if response_format == 'json':
            kwargs["response_format"] = {"type": "json_object"}
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                
                if not response or not hasattr(response, 'choices') or not response.choices:
                    raise Exception(f"Invalid response from OpenRouter: {response}")
                
                return response.choices[0].message.content
            
            except Exception as e:
                logger.error(f"OpenRouter API error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    # Try fallback model on retry
                    if model != 'fallback':
                        kwargs["model"] = self.MODELS['fallback']
                else:
                    raise Exception(f"OpenRouter API failed after {max_retries} attempts: {e}")
        
        return None
    
    def generate_json(self, prompt, model='reasoning', temperature=0.7, max_retries=3):
        """
        Generate JSON response
        
        Returns:
            Parsed JSON dict
        """
        response = self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            response_format='json',
            max_retries=max_retries
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            raise
