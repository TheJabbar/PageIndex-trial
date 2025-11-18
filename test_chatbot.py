import asyncio
import aiohttp
import os
from pathlib import Path

# Test script for the FastAPI chatbot
async def test_chatbot():
    base_url = "http://localhost:8000"
    
    # First, test the root endpoint
    async with aiohttp.ClientSession() as session:
        print("Testing root endpoint...")
        async with session.get(f"{base_url}/") as response:
            print(f"Root endpoint status: {response.status}")
            print(f"Root endpoint response: {await response.json()}")
        
        print("\nTesting PDF upload endpoint...")
        # Upload the sample PDF file
        sample_pdf_path = Path("laporan-perekonomian-indonesia-2024.pdf")
        if sample_pdf_path.exists():
            with open(sample_pdf_path, 'rb') as pdf_file:
                data = aiohttp.FormData()
                data.add_field('file', pdf_file, filename=sample_pdf_path.name, content_type='application/pdf')
                
                async with session.post(f"{base_url}/upload", data=data) as upload_response:
                    if upload_response.status == 200:
                        upload_result = await upload_response.json()
                        print(f"Upload successful: {upload_result}")
                        pdf_id = upload_result['pdf_id']
                        
                        print(f"\nTesting chat endpoint with PDF ID: {pdf_id}")
                        # Test the chat endpoint
                        chat_payload = {
                            "message": "What is this document about?",
                            "pdf_id": pdf_id
                        }
                        
                        async with session.post(f"{base_url}/chat", json=chat_payload) as chat_response:
                            if chat_response.status == 200:
                                chat_result = await chat_response.json()
                                print(f"Chat response: {chat_result}")
                            else:
                                print(f"Chat endpoint error: {chat_response.status} - {await chat_response.text()}")
                    else:
                        print(f"Upload failed: {upload_response.status} - {await upload_response.text()}")
        else:
            print(f"Sample PDF file not found: {sample_pdf_path}")
            
        print("\nTest completed.")

if __name__ == "__main__":
    print("Starting tests for the FastAPI chatbot...")
    asyncio.run(test_chatbot())