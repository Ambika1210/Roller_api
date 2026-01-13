import os
import sys
import json
import argparse
from typing import List, Dict, Tuple
from openai import OpenAI
from config import Config

Config.validate()
client = OpenAI(api_key=Config.OPENAI_API_KEY)

class PerceptionLayer:
    """Handles parsing of A-roll and B-roll media."""

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
        """Analyzes B-roll clips to generate metadata."""
        print(f"[Perception] Analyzing {len(broll_paths)} B-roll clips...")
        return [self._process_single_broll(path, i) for i, path in enumerate(broll_paths)]

    def _extract_audio(self, video_path: str, output_path: str = "temp_audio.mp3") -> str:
        """Extracts audio from video file."""
        from moviepy.editor import VideoFileClip
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_path, logger=None)
        return output_path

    def _call_whisper_api(self, audio_path: str) -> List[Dict]:
        """Calls OpenAI Whisper API."""
        with open(audio_path, "rb") as audio_file:
            # Updated for OpenAI v1.x
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="verbose_json"
            )
        return transcript.segments

    def _cleanup_audio(self, path: str):
        if os.path.exists(path):
            os.remove(path)

    def _process_single_broll(self, path: str, index: int) -> Dict:
        """Processes a single B-roll file."""
        filename = os.path.basename(path)
        return {
            "id": f"broll_{index}",
            "path": path,
            "description": f"Visuals related to {filename}. General stock footage suitable for illustration.", 
            "filename": filename
        }


class ReasoningLayer:
    """Handles semantic matching using LLM."""

    def match_broll(self, transcript: List[Dict], brolls: List[Dict]) -> Dict:
        """Main entry point for matching logic."""
        print("[Reasoning] Matching B-roll to Transcript...")
        
        transcript_text = self._format_transcript(transcript)
        broll_descriptions = self._format_broll_list(brolls)
        
        print(f"[DEBUG] Transcript (First 500 chars): {transcript_text[:500]}...")
        
        prompt = self._construct_prompt(transcript_text, broll_descriptions)
        
        llm_result = self._call_llm(prompt)
        
        # Log debug info
        print(f"[DEBUG] Prompt Length: {len(prompt)}")
        print(f"[DEBUG] Transcript Preview: {transcript_text[:200]}")
        print(f"[DEBUG] B-Roll Count: {len(brolls)}")

        return llm_result

    def _format_transcript(self, transcript: List[Dict]) -> str:
        # Handle if transcript is an object (TranscriptionSegment) or dict
        def get_val(seg, key):
            return getattr(seg, key, seg.get(key)) if isinstance(seg, dict) else getattr(seg, key)

        return "\n".join([f"[{get_val(seg, 'start'):.2f}-{get_val(seg, 'end'):.2f}] {get_val(seg, 'text')}" for seg in transcript])

    def _format_broll_list(self, brolls: List[Dict]) -> str:
        return "\n".join([f"ID: {b['id']}, Desc: {b['description']}" for b in brolls])

    def _construct_prompt(self, transcript_text: str, broll_descriptions: str) -> str:
        return f"""
You are an Expert Video Editor. Analyze the provided A-roll transcript and B-roll descriptions.

Your Constraints:
1. You MUST insert at least one B-roll if available, regardless of match quality.
2. Match B-roll visually to keywords. If B-roll description is generic, matching it to any relevant segment is allowed.
3. Max B-roll duration: 5 seconds.
4. Minimum gap between two B-rolls: 2 seconds.
5. No restrictions on Intro/Outro for now.
6. Output Format: Strict JSON only.

A-Roll Transcript:
{transcript_text}

Available B-Rolls:
{broll_descriptions}

Return JSON with this structure:
{{
  "insertions": [
    {{
      "start_sec": float,
      "duration_sec": float,
      "broll_id": string,
      "reason": string
    }}
  ]
}}
"""

    def _call_llm(self, prompt: str) -> Dict:
        try:
            # Updated for OpenAI v1.x
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            content = response.choices[0].message.content
            print(f"[DEBUG] Raw LLM Response: {content}")
            
            parsed = self._parse_llm_response(content)
            parsed['_raw_response'] = content # Store raw response for debugging
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
             # Fallback if JSON parsing fails but content might be raw text
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
        print(msg) 
        logs.append(msg)

    # Execution Flow
    log(f"[Engine] Processing A-Roll: {os.path.basename(args.a_roll)}")
    transcript = perception.transcribe_audio(args.a_roll)
    transcript_text = reasoning._format_transcript(transcript)
    log(f"[Engine] Transcript Length: {len(transcript_text)} chars")
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