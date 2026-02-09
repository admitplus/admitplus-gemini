from typing import List, Dict, Any


def build_image_extraction_prompt(image_url: str) -> List[Dict[str, Any]]:
    """
    Build a standard prompt for extracting ALL text, data, charts, and visual info from an image.
    Returns a list of messages formatted for OpenAI-compatible chat/completions API.
    """
    return [
        {
            "role": "system",
            "content": "You are an expert at extracting and describing text and visual content from images. Extract all text, data, and visual information accurately and comprehensively.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please extract and describe all text, data, charts, graphs, and visual information from this image. Be thorough and accurate. If this is a chart or graph, describe the data and trends clearly. If there is text, transcribe it exactly.",
                },
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        },
    ]
