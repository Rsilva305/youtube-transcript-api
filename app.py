from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable
import requests
import os

app = Flask(__name__)

# Get proxy from environment variable
PROXY_STRING = os.environ.get('WEBSHARE_PROXY', '')

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    
    if not video_id:
        return jsonify({"error": "video_id parameter required"}), 400
    
    try:
        # Set up proxy if provided
        if PROXY_STRING:
            # Format: host:port:username:password
            parts = PROXY_STRING.split(':')
            proxy_host = parts[0]
            proxy_port = parts[1]
            proxy_user = parts[2]
            proxy_pass = parts[3]
            
            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
            
            session = requests.Session()
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            api = YouTubeTranscriptApi(http_client=session)
        else:
            api = YouTubeTranscriptApi()
        
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
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
