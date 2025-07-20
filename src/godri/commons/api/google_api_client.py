"""Base Google API client with async aiohttp and retry logic."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import aiohttp
import aiofiles
from pathlib import Path
import mimetypes


class GoogleApiClient:
    """Base async Google API client with retry logic."""

    def __init__(self, credentials):
        self.credentials = credentials
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.base_url = "https://www.googleapis.com"
        self.max_retries = 3
        self.retry_delay = 1.0

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self):
        """Initialize the aiohttp session."""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
            self.logger.info("Google API client initialized")

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("Google API client closed")

    async def refresh_credentials(self):
        """Refresh OAuth2 credentials if needed."""
        if hasattr(self.credentials, "expired") and self.credentials.expired:
            if hasattr(self.credentials, "refresh"):
                self.credentials.refresh()
                self.logger.info("Credentials refreshed")

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json",
        }

    async def make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Make an async HTTP request with retry logic."""
        if not self.session:
            await self.initialize()

        await self.refresh_credentials()
        headers = self.get_headers()

        # Merge additional headers if provided
        if additional_headers:
            headers.update(additional_headers)

        if files:
            # For file uploads, don't set Content-Type header (let aiohttp handle it)
            headers.pop("Content-Type", None)

        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=data if not files else None,
                data=files if files else None,
                headers=headers,
            ) as response:
                if response.status == 401:
                    # Unauthorized - refresh credentials and retry
                    if retry_count < self.max_retries:
                        self.logger.warning("401 Unauthorized, refreshing credentials and retrying")
                        await self.refresh_credentials()
                        await asyncio.sleep(self.retry_delay)
                        return await self.make_request(
                            method, url, params, data, files, additional_headers, retry_count + 1
                        )
                    else:
                        raise aiohttp.ClientResponseError(
                            response.request_info, response.history, status=response.status
                        )

                elif response.status == 429:
                    # Rate limited - retry with exponential backoff
                    if retry_count < self.max_retries:
                        delay = self.retry_delay * (2**retry_count)
                        self.logger.warning(f"Rate limited, retrying in {delay}s")
                        await asyncio.sleep(delay)
                        return await self.make_request(
                            method, url, params, data, files, additional_headers, retry_count + 1
                        )
                    else:
                        raise aiohttp.ClientResponseError(
                            response.request_info, response.history, status=response.status
                        )

                elif response.status >= 500:
                    # Server error - retry with exponential backoff
                    if retry_count < self.max_retries:
                        delay = self.retry_delay * (2**retry_count)
                        self.logger.warning(f"Server error {response.status}, retrying in {delay}s")
                        await asyncio.sleep(delay)
                        return await self.make_request(
                            method, url, params, data, files, additional_headers, retry_count + 1
                        )
                    else:
                        raise aiohttp.ClientResponseError(
                            response.request_info, response.history, status=response.status
                        )

                response.raise_for_status()

                # Handle different content types
                content_type = response.headers.get("content-type", "").lower()
                if "application/json" in content_type:
                    return await response.json()
                elif content_type.startswith("text/"):
                    text_content = await response.text()
                    return {"content": text_content}
                else:
                    # Binary content
                    content = await response.read()
                    return {"content": content, "content_type": content_type}

        except aiohttp.ClientError as e:
            if retry_count < self.max_retries:
                delay = self.retry_delay * (2**retry_count)
                self.logger.warning(f"Client error {e}, retrying in {delay}s")
                await asyncio.sleep(delay)
                return await self.make_request(method, url, params, data, files, retry_count + 1)
            else:
                self.logger.error(f"Request failed after {self.max_retries} retries: {e}")
                raise

    async def upload_file(
        self,
        url: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 256 * 1024,  # 256KB chunks
    ) -> Dict[str, Any]:
        """Upload a file with resumable upload support."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file info
        file_size = file_path.stat().st_size
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

        # Prepare metadata
        upload_metadata = metadata or {}
        upload_metadata.update(
            {
                "name": file_path.name,
                "mimeType": mime_type,
            }
        )

        # For small files, use simple upload
        if file_size <= chunk_size:
            return await self._simple_upload(url, file_path, upload_metadata, mime_type)
        else:
            return await self._resumable_upload(url, file_path, upload_metadata, mime_type, chunk_size)

    async def _simple_upload(
        self, url: str, file_path: Path, metadata: Dict[str, Any], mime_type: str
    ) -> Dict[str, Any]:
        """Simple file upload for small files."""
        if not self.session:
            await self.initialize()

        await self.refresh_credentials()
        headers = {"Authorization": f"Bearer {self.credentials.token}"}

        data = aiohttp.FormData()
        data.add_field("metadata", json.dumps(metadata), content_type="application/json")

        async with aiofiles.open(file_path, "rb") as f:
            file_content = await f.read()
            data.add_field("file", file_content, filename=file_path.name, content_type=mime_type)

        return await self.make_request("POST", url, files=data)

    async def _resumable_upload(
        self, url: str, file_path: Path, metadata: Dict[str, Any], mime_type: str, chunk_size: int
    ) -> Dict[str, Any]:
        """Resumable file upload for large files."""
        # Initiate resumable upload
        init_url = f"{url}?uploadType=resumable"
        init_response = await self.make_request("POST", init_url, data=metadata)

        # Get upload URL from Location header
        upload_url = init_response.get("location")
        if not upload_url:
            raise ValueError("Failed to initiate resumable upload")

        # Upload file in chunks
        file_size = file_path.stat().st_size
        uploaded = 0

        async with aiofiles.open(file_path, "rb") as f:
            while uploaded < file_size:
                chunk_end = min(uploaded + chunk_size, file_size) - 1
                chunk_data = await f.read(chunk_size)

                headers = {
                    "Authorization": f"Bearer {self.credentials.token}",
                    "Content-Range": f"bytes {uploaded}-{chunk_end}/{file_size}",
                    "Content-Type": mime_type,
                }

                async with self.session.put(upload_url, data=chunk_data, headers=headers) as response:
                    if response.status == 308:
                        # Continue uploading
                        range_header = response.headers.get("Range", "")
                        if range_header:
                            uploaded = int(range_header.split("-")[1]) + 1
                        else:
                            uploaded += len(chunk_data)
                    elif response.status in (200, 201):
                        # Upload complete
                        return await response.json()
                    else:
                        response.raise_for_status()

        raise RuntimeError("Upload completed but no final response received")

    async def download_file(self, url: str, output_path: str, chunk_size: int = 8192) -> str:
        """Download a file from Google APIs."""
        if not self.session:
            await self.initialize()

        await self.refresh_credentials()
        headers = {"Authorization": f"Bearer {self.credentials.token}"}

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with self.session.get(url, headers=headers) as response:
            response.raise_for_status()

            async with aiofiles.open(output_path, "wb") as f:
                async for chunk in response.content.iter_chunked(chunk_size):
                    await f.write(chunk)

        self.logger.info(f"File downloaded successfully to: {output_path}")
        return str(output_path)

    async def batch_request(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple requests concurrently with proper rate limiting."""
        # Implement semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

        async def execute_request(request_data):
            async with semaphore:
                return await self.make_request(**request_data)

        # Execute all requests concurrently
        tasks = [execute_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error dictionaries
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)

        return processed_results
