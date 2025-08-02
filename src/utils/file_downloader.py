#!/usr/bin/env python3
"""
File download utility
Handles downloading files from URLs with size limits and error handling
"""

import requests
from typing import Optional

class FileDownloader:
    """Handles file downloads with validation and error handling"""
    
    def __init__(self, max_size_bytes: int = 200 * 1024 * 1024):
        """Initialize downloader with size limit"""
        self.max_size_bytes = max_size_bytes
    
    def download_file(self, url: str, output_filename: str, api_key: Optional[str] = None) -> bool:
        """
        Download a file from a given URL with size limit and optional API key.
        Implements robust error handling and validation.

        Args:
            url (str): The URL of the file to download.
            output_filename (str): The name of the file to save the download as.
            api_key (str, optional): API key to be used as a bearer token.

        Returns:
            bool: True if download was successful, False otherwise.
        """
        try:
            # Validate inputs
            if not url or not url.strip():
                print("Error: URL is empty or invalid")
                return False
            
            if self.max_size_bytes <= 0:
                print("Error: Invalid max_size_bytes")
                return False
            
            # Prepare headers
            headers = {'User-Agent': 'ivrit-ai-transcription/1.0'}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            # Send a GET request with timeout
            response = requests.get(url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()

            # Get the file size if possible
            content_length = response.headers.get('Content-Length')
            if content_length:
                file_size = int(content_length)
                if file_size > self.max_size_bytes:
                    print(f"Error: File size ({file_size:,} bytes) exceeds limit ({self.max_size_bytes:,} bytes)")
                    return False

            # Download and write the file with progress tracking
            downloaded_size = 0
            chunk_size = 8192
            
            with open(output_filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        downloaded_size += len(chunk)
                        if downloaded_size > self.max_size_bytes:
                            print(f"Error: Download size limit exceeded ({self.max_size_bytes:,} bytes)")
                            return False
                        file.write(chunk)

            print(f"✅ File downloaded successfully: {output_filename} ({downloaded_size:,} bytes)")
            return True

        except requests.exceptions.Timeout:
            print(f"Error: Download timeout for {url}")
            return False
        except requests.exceptions.HTTPError as e:
            print(f"Error: HTTP {e.response.status_code} for {url}")
            return False
        except requests.exceptions.ConnectionError:
            print(f"Error: Connection failed for {url}")
            return False
        except requests.RequestException as e:
            print(f"Error downloading file: {e}")
            return False
        except (IOError, OSError) as e:
            print(f"Error writing file {output_filename}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during download: {e}")
            return False 