from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable

app = Flask(__name__)

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    
    if not video_id:
        return jsonify({"error": "video_id parameter required"}), 400
    
    try:
        # Use the new API syntax
        api = YouTubeTranscriptApi()
        result = api.fetch(video_id)
        
        # Convert to raw data format (list of dicts)
        transcript_data = result.to_raw_data()
        
        # Also create a simple full text version
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
