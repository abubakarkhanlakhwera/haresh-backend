import base64
import os
from typing import Dict, List
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class ImageAnalyzer:
    """
    Medical report image analyzer using OpenAI Vision API.
    Analyzes uploaded medical reports and provides condition detection and recommendations.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # Using GPT-4 with vision capabilities
        
    async def analyze_report(self, image_data: bytes, content_type: str) -> Dict:
        """
        Analyze a medical report image and extract conditions and recommendations.
        
        Args:
            image_data: Raw image bytes
            content_type: MIME type of the image (e.g., 'image/jpeg')
            
        Returns:
            Dictionary containing analysis, conditions list, and recommendations
        """
        try:
            # Convert image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Create the prompt for medical report analysis
            prompt = """You are a medical report analysis assistant. Analyze this medical report image and provide:

1. A detailed analysis of what you see in the report
2. A list of any medical conditions, abnormalities, or health concerns identified
3. General recommendations and next steps

IMPORTANT DISCLAIMERS:
- This is an AI analysis for informational purposes only
- NOT a substitute for professional medical advice
- Patients should consult with qualified healthcare providers
- Results should be reviewed by medical professionals

Please structure your response in the following format:

ANALYSIS:
[Provide detailed analysis of the report findings]

CONDITIONS:
[List each condition or finding, one per line with a dash prefix, e.g., "- Elevated blood pressure"]

RECOMMENDATIONS:
[Provide general recommendations and emphasize the need to consult healthcare providers]

If the image is not a medical report or is unclear, state that clearly."""

            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert medical report analyzer. You help patients understand their medical reports while emphasizing the importance of professional medical consultation."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.3  # Lower temperature for more consistent medical analysis
            )
            
            # Extract the response content
            full_response = response.choices[0].message.content
            
            # Parse the response into structured format
            parsed_result = self._parse_response(full_response)
            
            return parsed_result
            
        except Exception as e:
            raise Exception(f"Error analyzing image: {str(e)}")
    
    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse the AI response into structured components.
        
        Args:
            response_text: Full text response from the AI
            
        Returns:
            Dictionary with analysis, conditions, and recommendations
        """
        # Initialize result structure
        result = {
            "analysis": "",
            "conditions": [],
            "recommendations": ""
        }
        
        # Split response into sections
        sections = response_text.split("\n")
        current_section = None
        
        analysis_lines = []
        conditions_lines = []
        recommendations_lines = []
        
        for line in sections:
            line_upper = line.strip().upper()
            
            # Detect section headers
            if "ANALYSIS:" in line_upper:
                current_section = "analysis"
                continue
            elif "CONDITIONS:" in line_upper or "CONDITION:" in line_upper or "FINDINGS:" in line_upper:
                current_section = "conditions"
                continue
            elif "RECOMMENDATIONS:" in line_upper or "RECOMMENDATION:" in line_upper:
                current_section = "recommendations"
                continue
            
            # Add content to appropriate section
            if current_section == "analysis" and line.strip():
                analysis_lines.append(line.strip())
            elif current_section == "conditions" and line.strip():
                # Extract condition items (lines starting with -, *, or numbers)
                cleaned_line = line.strip()
                if cleaned_line.startswith(('-', '*', '•')):
                    conditions_lines.append(cleaned_line[1:].strip())
                elif cleaned_line and cleaned_line[0].isdigit() and '.' in cleaned_line:
                    conditions_lines.append(cleaned_line.split('.', 1)[1].strip())
                elif cleaned_line:
                    conditions_lines.append(cleaned_line)
            elif current_section == "recommendations" and line.strip():
                recommendations_lines.append(line.strip())
        
        # Combine lines into result
        result["analysis"] = "\n".join(analysis_lines) if analysis_lines else "Unable to analyze the report clearly."
        result["conditions"] = conditions_lines if conditions_lines else ["No specific conditions identified"]
        result["recommendations"] = "\n".join(recommendations_lines) if recommendations_lines else "Please consult with a healthcare provider to discuss these results."
        
        return result
