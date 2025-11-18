
import os
import httpx
from loguru import logger
from .config import settings
URL_CUSTOM_LLM_APILOGY = settings.URL_CUSTOM_LLM
TOKEN_CUSTOM_LLM_APILOGY = settings.TOKEN_CUSTOM_LLM

# Log LLM configuration (without sensitive tokens)
if URL_CUSTOM_LLM_APILOGY:
    logger.info("LLM engine configured with custom endpoint")
else:
    logger.warning("No LLM endpoint configured")

TIMEOUT = 120.0
async def make_async_api_call(url, token, payload):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": token
    }

    logger.debug(f"Making API call to: {url}")

    async with httpx.AsyncClient(timeout=TIMEOUT, verify=False) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.debug("API call successful")
                return response.json()['choices'][0]['message']['content']
            else:
                error_message = response.text
                logger.error(f"API Error {response.status_code}: {error_message}")
                return {"error": f"API call failed with status {response.status_code}"}
        except Exception as e:
            logger.error(f"Exception during API call: {e}")
            return {"error": str(e)}

async def telkomllm_call(prompt, max_tokens, temperature):
    """
    Calls TelkomLLM to select the most suitable table from a list, given a prompt and user question.
    Returns the result as a JSON object (should contain the selected table name and optionally reasoning).
    """
    logger.debug(f"Calling LLM with max_tokens: {max_tokens}, temperature: {temperature}")

    url = URL_CUSTOM_LLM_APILOGY
    token = TOKEN_CUSTOM_LLM_APILOGY
    payload = {
        "model": "telkom-ai-instruct",
        "messages": [
            {
                "role": "system",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }

    result = await make_async_api_call(url, token, payload)
    if isinstance(result, dict) and "error" in result:
        # Fallback to secondary endpoint
        logger.warning("Primary API call failed, attempting fallback")
        result = await make_async_api_call(URL_CUSTOM_LLM_APILOGY, TOKEN_CUSTOM_LLM_APILOGY, payload)

    if isinstance(result, dict) and "error" not in result:
        logger.success("LLM call completed successfully")
    else:
        logger.warning("LLM call returned an error")

    return result