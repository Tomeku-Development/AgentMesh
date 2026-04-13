"""Amazon Bedrock LLM provider."""

from __future__ import annotations

import asyncio
import json
import logging
import time

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Bedrock model IDs for Claude 3
BEDROCK_MODELS = {
    "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "claude-3-5-haiku": "anthropic.claude-3-5-haiku-20241022-v1:0",
}

# Approximate pricing per 1K tokens (as of 2024)
BEDROCK_PRICING = {
    "anthropic.claude-3-sonnet-20240229-v1:0": {"input": 0.003, "output": 0.015},
    "anthropic.claude-3-haiku-20240307-v1:0": {"input": 0.00025, "output": 0.00125},
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {"input": 0.003, "output": 0.015},
    "anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.001, "output": 0.005},
}


class BedrockProvider(LLMProvider):
    """Amazon Bedrock LLM provider using boto3."""

    def __init__(
        self,
        region: str = "us-east-1",
        access_key_id: str = "",
        secret_access_key: str = "",
        model_id: str = "claude-3-haiku",
    ):
        """Initialize Bedrock provider.

        Args:
            region: AWS region (e.g., us-east-1)
            access_key_id: AWS access key ID (empty = use default credential chain)
            secret_access_key: AWS secret access key
            model_id: Model identifier or Bedrock model ID
        """
        self._region = region
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key

        # Resolve model ID
        if model_id in BEDROCK_MODELS:
            self._model_id = BEDROCK_MODELS[model_id]
        else:
            self._model_id = model_id

        self._client = None
        self._pricing = BEDROCK_PRICING.get(
            self._model_id, {"input": 0.003, "output": 0.015}
        )

    def _get_client(self):
        """Get or create Bedrock runtime client (lazy initialization)."""
        if self._client is None:
            import boto3

            if self._access_key_id and self._secret_access_key:
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self._region,
                    aws_access_key_id=self._access_key_id,
                    aws_secret_access_key=self._secret_access_key,
                )
            else:
                # Use default credential chain (IAM roles, env vars, etc.)
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self._region,
                )
        return self._client

    @property
    def name(self) -> str:
        return "bedrock"

    @property
    def model_id(self) -> str:
        return self._model_id

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate completion using Bedrock's Messages API."""
        client = self._get_client()

        # Build Messages API request for Claude
        messages = [{"role": "user", "content": prompt}]

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            request_body["system"] = system_prompt

        # Retry with exponential backoff
        max_retries = 3
        base_delay = 1.0
        last_exception = None

        for attempt in range(max_retries):
            try:
                start_time = time.perf_counter()

                # Run sync call in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.invoke_model(
                        modelId=self._model_id,
                        body=json.dumps(request_body),
                    ),
                )

                latency_ms = (time.perf_counter() - start_time) * 1000

                # Parse response
                response_body = json.loads(response["body"].read())

                # Extract content
                content = ""
                for block in response_body.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")

                # Extract token counts
                input_tokens = response_body.get("usage", {}).get("input_tokens", 0)
                output_tokens = response_body.get("usage", {}).get("output_tokens", 0)

                # Calculate cost estimate
                input_cost = (input_tokens / 1000) * self._pricing["input"]
                output_cost = (output_tokens / 1000) * self._pricing["output"]
                cost_estimate = input_cost + output_cost

                logger.debug(
                    f"Bedrock completion: {input_tokens} in, {output_tokens} out, "
                    f"{latency_ms:.1f}ms, ${cost_estimate:.6f}"
                )

                return LLMResponse(
                    content=content,
                    model=self._model_id,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_estimate=cost_estimate,
                )

            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"Bedrock request failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Bedrock request failed after {max_retries} attempts: {e}")

        raise RuntimeError(f"Bedrock request failed: {last_exception}")
