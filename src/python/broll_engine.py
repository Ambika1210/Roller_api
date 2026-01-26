import os
import sys
import json
import argparse
from typing import List, Dict, Tuple
from openai import OpenAI
from config import Config

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

Config.validate()
client = OpenAI(api_key=Config.OPENAI_API_KEY)

class PerceptionLayer:
    """Handles parsing of A-roll and B-roll media using Vision AI."""

    def transcribe_audio(self, video_path: str) -> List[Dict]:
        """Orchestrates the transcription process."""
        print(f"[Perception] Transcribing {video_path}...")
        try:
            audio_path = self._extract_audio(video_path)
            segments = self._call_whisper_api(audio_path)
            self._cleanup_audio(audio_path)
            return segments
        except Exception as e:
            print(f"[Perception] Transcription failed: {e}")
            return []

    def analyze_broll(self, broll_paths: List[str]) -> List[Dict]:
        """Analyzes B-roll clips to generate metadata using Vision AI."""
        print(f"[Perception] Analyzing {len(broll_paths)} B-roll clips with Vision AI...")
        results = []
        for i, path in enumerate(broll_paths):
            try:
                results.append(self._process_single_broll_vision(path, i))
            except Exception as e:
                print(f"[Perception] Failed to analyze {path}: {e}")
                # Fallback to simple filename based
                results.append(self._process_single_broll_fallback(path, i))
        return results

    def _extract_audio(self, video_path: str, output_path: str = "temp_audio.mp3") -> str:
        """Extracts audio from video file using direct ffmpeg."""
        import subprocess
        import imageio_ffmpeg
        
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        cmd = [
            ffmpeg_exe,
            "-y", # Overwrite
            "-i", video_path,
            "-vn", # No video
            "-acodec", "libmp3lame",
            "-q:a", "2",
            output_path
        ]
        
        # Run silently to avoid stdout buffer crushing
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path

    def _call_whisper_api(self, audio_path: str) -> List[Dict]:
        """Calls OpenAI Whisper API."""
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="verbose_json"
            )
        return transcript.segments

    def _cleanup_audio(self, path: str):
        if os.path.exists(path):
            os.remove(path)

    def _process_single_broll_vision(self, path: str, index: int) -> Dict:
        """Processes a single B-roll file using Vision AI."""
        print(f"[Perception] meaningful visual analysis for: {os.path.basename(path)}")
        
        # 1. Extract Frames (Start, Middle, End)
        base64_frames = self._extract_frames(path)
        
        # 2. Get Description from LLM
        description = self._get_visual_description(base64_frames)
        
        return {
            "id": f"broll_{index}",
            "path": path,
            "description": description, 
            "filename": os.path.basename(path)
        }

    def _process_single_broll_fallback(self, path: str, index: int) -> Dict:
        filename = os.path.basename(path)
        return {
            "id": f"broll_{index}",
            "path": path,
            "description": f"Visuals related to {filename} (Analysis Failed)", 
            "filename": filename
        }

    def _extract_frames(self, video_path: str) -> List[str]:
        """Extracts 3 representative frames using ffmpeg directly."""
        import subprocess
        import imageio_ffmpeg
        import base64
        import os
        
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        duration = self._get_duration(video_path)
        
        times = [duration * 0.1, duration * 0.5, duration * 0.9]
        encoded_frames = []
        
        for i, t in enumerate(times):
            temp_img = f"temp_frame_{i}.jpg"
            cmd = [
                ffmpeg_exe,
                "-y",
                "-ss", str(t),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                temp_img
            ]
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.path.exists(temp_img):
                    with open(temp_img, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                        encoded_frames.append(b64)
                    os.remove(temp_img)
            except Exception as e:
                print(f"[Perception] Frame extract failed: {e}")
                
        return encoded_frames

    def _get_duration(self, video_path: str) -> float:
        import subprocess
        import imageio_ffmpeg
        import re
        
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [ffmpeg_exe, "-i", video_path]
        
        # ffmpeg prints info to stderr
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        
        # Parse duration "Duration: 00:00:05.12"
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", result.stderr)
        if match:
            h, m, s = map(float, match.groups())
            return h * 3600 + m * 60 + s
        return 10.0 # Fallback

    def _get_visual_description(self, base64_frames: List[str]) -> str:
        """Sends frames to GPT-4o for analysis."""
        
        # Prepare content with images
        content = [
            {"type": "text", "text": "These are frames from a video clip. Describe the visual content, mood, and potential context in 2-3 sentences. Focus on objects, actions, and lighting."}
        ]
        
        for b64 in base64_frames:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "low"
                }
            })

        response = client.chat.completions.create(
            model="gpt-4o-mini", # Cost effective vision model
            messages=[
                {"role": "user", "content": content}
            ],
            max_tokens=100
        )
        
        return response.choices[0].message.content


class ReasoningLayer:
    """Handles semantic matching using LLM."""

    def match_broll(self, transcript: List[Dict], brolls: List[Dict]) -> Dict:
        """Main entry point for matching logic."""
        print("[Reasoning] Matching B-roll to Transcript...")
        
        transcript_text = self._format_transcript(transcript)
        broll_descriptions = self._format_broll_list(brolls)
        
        print(f"[DEBUG] Transcript (First 500 chars): {transcript_text[:500]}...")
        
        system_prompt, user_prompt = self._construct_prompts(transcript_text, broll_descriptions)
        
        llm_result = self._call_llm(system_prompt, user_prompt)
        
        # Log debug info
        print(f"[DEBUG] System Prompt Length: {len(system_prompt)}")
        print(f"[DEBUG] User Prompt Length: {len(user_prompt)}")
        print(f"[DEBUG] B-Roll Count: {len(brolls)}")

        return llm_result

    def _format_transcript(self, transcript: List[Dict]) -> str:
        # Handle if transcript is an object (TranscriptionSegment) or dict
        def get_val(seg, key):
            return getattr(seg, key, seg.get(key)) if isinstance(seg, dict) else getattr(seg, key)

        return "\n".join([f"[{get_val(seg, 'start'):.2f}-{get_val(seg, 'end'):.2f}] {get_val(seg, 'text')}" for seg in transcript])

    def _format_broll_list(self, brolls: List[Dict]) -> str:
        # Using the rich 'description' field from Vision AI
        return "\n".join([f"ID: {b['id']}\n   Visuals: {b['description']}\n" for b in brolls])

    def _construct_prompts(self, transcript_text: str, broll_descriptions: str) -> Tuple[str, str]:
        """Returns (system_prompt, user_prompt) tuple for better LLM guidance."""
        
        system_prompt = """You are an Expert Video Editor specializing in B-roll insertion.

YOUR GOAL:
Analyze the spoken content (A-roll) and the available visual footage (B-roll) to create a seamless, engaging video. 

MATCHING LOGIC:
1. **Semantic Matching**: Look for deeper connections than just keywords. 
   - Example directly mentioned: Speaker says "I love coffee" -> Match with clip of coffee.
   - Example thematic: Speaker says "The morning rush is crazy" -> Match with clip of traffic or busy streets.
   - Example emotional: Speaker says "I felt so peaceful" -> Match with clip of a calm sunset.

2. **Visual Continuity**: Ensure the selected B-roll actually fits the context described.

CONSTRAINTS:
- Max B-roll duration: 4-5 seconds.
- Min duration: 2 seconds.
- Avoid inserting B-roll when the speaker is likely introducing themselves or doing a direct call-to-action (unless visuals match perfectly).
- **Mandatory**: You MUST act if there are good matches. Do not return empty unless absolutely nothing matches.

JSON OUTPUT FORMAT:
Output ONLY valid JSON.
{
  "insertions": [
    {
      "start_sec": <float>,
      "duration_sec": <float>,
      "broll_id": "<id>",
      "reason": "<Explain WHY this specific visual fits this specific spoken text>",
      "confidence": <float between 0.0 and 1.0>
    }
  ]
}"""

        user_prompt = f"""START PLANNING.

A-ROLL TRANSCRIPT:
{transcript_text}

AVAILABLE B-ROLL FOOTAGE (Analyzed by Vision AI):
{broll_descriptions}

Create the insertion plan JSON."""

        return system_prompt, user_prompt

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Dict:
        try:
            # Updated for OpenAI v1.x with separate system and user prompts
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", # Can upgrade to gpt-4 if needed for better reasoning
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            content = response.choices[0].message.content
            print(f"[DEBUG] Raw LLM Response: {content}")
            
            parsed = self._parse_llm_response(content)
            parsed['_raw_response'] = content 
            return parsed
        except Exception as e:
            print(f"[Reasoning] Matching failed: {e}")
            return {"insertions": [], "_raw_response": str(e)}

    def _parse_llm_response(self, content: str) -> Dict:
        try:
            if "```json" in content:
                clean_content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                clean_content = content.split("```")[1]
            else:
                clean_content = content
            
            return json.loads(clean_content.strip())
        except Exception as e:
             print(f"[Reasoning] JSON parse failed: {e}")
             return {"insertions": []}

class ExecutionLayer:
    """Handles Video Rendering using MoviePy."""

    def render_video(self, a_roll_path: str, b_roll_map: Dict, plan: Dict, output_path: str):
        print(f"[Execution] Rendering video to {output_path}...")
        try:
            from moviepy.editor import VideoFileClip, CompositeVideoClip
            
            a_roll = VideoFileClip(a_roll_path)
            final_clips = [a_roll]
            
            insertions = self._get_sorted_insertions(plan)
            
            for ins in insertions:
                clip = self._prepare_broll_clip(ins, b_roll_map, a_roll.size)
                if clip:
                    final_clips.append(clip)

            self._write_video(final_clips, output_path)
            print("[Execution] Render complete.")
            
        except Exception as e:
            print(f"[Execution] Render failed: {e}")

    def _get_sorted_insertions(self, plan: Dict) -> List[Dict]:
        return sorted(plan.get('insertions', []), key=lambda x: x['start_sec'])

    def _prepare_broll_clip(self, insertion: Dict, b_roll_map: Dict, size: Tuple[int, int]):
        from moviepy.editor import VideoFileClip
        
        b_id = insertion['broll_id']
        if b_id not in b_roll_map:
            return None
        
        b_path = b_roll_map[b_id]['path']
        start_t = insertion['start_sec']
        dur = insertion['duration_sec']
        
        b_clip = VideoFileClip(b_path)
        b_clip = self._adjust_duration(b_clip, dur)
        
        # Overlay settings
        b_clip = b_clip.set_start(start_t).resize(size)
        b_clip = b_clip.crossfadein(0.2).crossfadeout(0.2)
        
        return b_clip

    def _adjust_duration(self, clip, duration: float):
        if clip.duration < duration:
            try:
                return clip.loop(duration=duration)
            except:
                return clip # Fallback
        return clip.subclip(0, duration)

    def _write_video(self, clips: List, output_path: str):
        from moviepy.editor import CompositeVideoClip
        
        final_video = CompositeVideoClip(clips)
        final_video.write_videofile(
            output_path, 
            codec='libx264', 
            audio_codec='aac', 
            verbose=False, 
            logger=None
        )

def main():
    parser = argparse.ArgumentParser(description="Smart B-Roll Inserter Engine")
    parser.add_argument("--a_roll", required=True, help="Path to A-Roll video")
    parser.add_argument("--b_rolls", required=True, nargs='+', help="Paths to B-Roll videos")
    parser.add_argument("--output", default="output.mp4", help="Path to output video")
    parser.add_argument("--render", action="store_true", help="Whether to render final video")
    
    args = parser.parse_args()
    
    perception = PerceptionLayer()
    reasoning = ReasoningLayer()
    execution = ExecutionLayer()
    
    # Internal log buffer
    logs = []
    def log(msg):
        print(msg, flush=True) 
        logs.append(msg)
        sys.stdout.flush() # Force flush

    # Execution Flow
    log(f"[Engine] Processing A-Roll: {os.path.basename(args.a_roll)}")
    transcript = perception.transcribe_audio(args.a_roll)
    transcript_text = reasoning._format_transcript(transcript)
    log(f"[Engine] Transcript Length: {len(transcript_text)} chars")
    log(f"[Engine] Full Transcript:\n{transcript_text}\n") # Added print
    if len(transcript_text) < 100:
        log(f"[Engine] WARNING: Transcript is very short: '{transcript_text}'")

    analyzed_brolls = perception.analyze_broll(args.b_rolls)
    
    b_roll_map = {b['id']: b for b in analyzed_brolls}
    
    # Reasoning
    log("[Engine] Starting B-Roll Matching with gpt-3.5-turbo...")
    
    try:
        plan = reasoning.match_broll(transcript, analyzed_brolls)
    except Exception as e:
        log(f"[Error] Matching crashed: {e}")
        plan = {"insertions": []}

    if not plan.get('insertions'):
        log("[Engine] LLM returned 0 insertions. Returning empty plan.")
    
    # Output to stdout
    print("JSON_PLAN_START")
    print(json.dumps(plan, indent=2))
    print("JSON_PLAN_END")

    if args.render:
        execution.render_video(args.a_roll, b_roll_map, plan, args.output)

if __name__ == '__main__':
    main()