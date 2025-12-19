from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable
import requests
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

PROXY_STRING = os.environ.get('WEBSHARE_PROXY', '')

if PROXY_STRING:
    logger.info(f"✅ Proxy configured: {PROXY_STRING[:20]}...")
else:
    logger.warning("⚠️ No proxy configured")

@app.route('/test-proxy', methods=['GET'])
def test_proxy():
    """Test if the proxy is working"""
    if not PROXY_STRING:
        return jsonify({"error": "No proxy configured"}), 500
    
    try:
        parts = PROXY_STRING.split(':')
        proxy_host = parts[0]
        proxy_port = parts[1]
        proxy_user = parts[2]
        proxy_pass = parts[3]
        
        proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        
        # Test the proxy by checking our IP
        response = requests.get(
            'https://api.ipify.org?format=json',
            proxies={'http': proxy_url, 'https': proxy_url},
            timeout=10
        )
        
        return jsonify({
            "proxy_works": True,
            "your_ip_through_proxy": response.json()['ip'],
            "proxy_used": f"{proxy_host}:{proxy_port}"
        })
        
    except Exception as e:
        return jsonify({
            "proxy_works": False,
            "error": str(e)
        }), 500

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    
    if not video_id:
        return jsonify({"error": "video_id parameter required"}), 400
    
    try:
        if PROXY_STRING:
            parts = PROXY_STRING.split(':')
            proxy_host = parts[0]
            proxy_port = parts[1]
            proxy_user = parts[2]
            proxy_pass = parts[3]
            
            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
            logger.info(f"Using proxy: {proxy_host}:{proxy_port}")
            
            session = requests.Session()
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            api = YouTubeTranscriptApi(http_client=session)
        else:
            logger.warning("No proxy - making direct request")
            api = YouTubeTranscriptApi()
        
        logger.info(f"Fetching transcript for video: {video_id}")
        result = api.fetch(video_id)
        transcript_data = result.to_raw_data()
        full_text = " ".join([entry['text'] for entry in transcript_data])
        
        return jsonify({
            "video_id": video_id,
            "language": result.language,
            "is_generated": result.is_generated,
            "full_text": full_text,
            "detailed": transcript_data
        })
        
    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video"}), 404
    except VideoUnavailable:
        return jsonify({"error": "Video not found or unavailable"}), 404
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    proxy_status = "enabled" if PROXY_STRING else "disabled"
    return jsonify({"status": "healthy", "proxy": proxy_status}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
