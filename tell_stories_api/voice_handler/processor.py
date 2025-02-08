from pathlib import Path
import torch
import torchaudio
import soundfile as sf
from .models import VoiceRequest, ProgressData
from .utils import generate_audio, generate_audio_instruct, get_audio_duration, load_va_database
from tell_stories_api.logs import logger
import json
import subprocess
from datetime import datetime
from tqdm import tqdm

class VoiceProcessor:
    def process_cast_file(self, process_dir: Path) -> dict:
        with open(process_dir / "cast.json", encoding='utf-8') as f:
            va_match = json.load(f)
        
        cast_dict = {c["character"]: c for c in va_match}
        return self.update_cast_with_va_info(cast_dict)

    def update_cast_with_va_info(self, cast_dict: dict) -> dict:
        try:
            va_db = load_va_database()
        except Exception as e:
            logger.error(f"Failed to load VA database: {e}")
            return cast_dict
        
        va_lookup = {va['va_name']: va for va in va_db}
        
        for character, cast_info in cast_dict.items():
            va_name = cast_info.get('va_name')
            if va_name and va_name in va_lookup:
                va_info = va_lookup[va_name]
                cast_info['prompt_text'] = va_info['prompt_text']
                cast_info['prompt_wav'] = va_info['prompt_wav']
            else:
                logger.warning(f"VA info not found for character {character} with va_name {va_name}")
        
        return cast_dict

    def process_voice_generation(self, request: VoiceRequest, process_dir: Path):
        progress_file = process_dir / "voice_progress.json"
        try:
            # Initialize progress data
            progress_data = ProgressData(
                total_lines=0,
                processed_lines=0,
                success_count=0,
                failed_count=0,
                narrator_success_count=0,
                narrator_failed_count=0,
                status="processing"
            )
            
            # Load required files
            cast_file = process_dir / "voice_cast.json"
            if not cast_file.exists():
                raise Exception("Voice casting not performed. Please run voice_casting first.")
                
            with open(cast_file, encoding='utf-8') as f:
                cast_dict = json.load(f)
                
            with open(process_dir / "lines.json", encoding='utf-8') as f:
                lines_data = json.load(f)
            progress_data.total_lines = len(lines_data["lines"])
            

            # Save initial progress
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data.model_dump(), f)

            # Setup output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output") / timestamp
            output_dir.mkdir(parents=True, exist_ok=True)
            progress_data.output_path = str(output_dir)
            
            # Process voice generation
            self._generate_audio_files(
                request=request,
                lines_data=lines_data,
                cast_dict=cast_dict,
                output_dir=output_dir,
                progress_data=progress_data,
                progress_file=progress_file
            )
            
            # On successful completion
            progress_data.status = "completed"
            
        except Exception as e:
            progress_data.status = "failed"
            progress_data.error = str(e)
            logger.error(f"Error in voice generation: {str(e)}")
        
        # Save final progress
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data.model_dump(), f)

    def _generate_audio_files(self, request: VoiceRequest, lines_data: dict, cast_dict: dict, 
                            output_dir: Path, progress_data: ProgressData, progress_file: Path):
        file_list = []
        subtitle_data = []
        current_time = 0.0
        
        for i, line in tqdm(enumerate(lines_data["lines"]), total=len(lines_data["lines"])):
            character = line["character"]
            if character in cast_dict:
                cast_info = cast_dict[character]
                output_path = output_dir / f"{i:05d}.wav"
                file_list.append(output_path)
                
                instruct_text = line["instruct"]
                if instruct_text != "normal":
                    url = f"http://{request.host}:{request.port}/inference_instruct2"
                    success_flag = generate_audio_instruct(
                        url=url,
                        text=line["line"],
                        instruct_text=instruct_text,
                        prompt_wav=cast_info["prompt_wav"],
                        output_path=output_path
                    )
                else:
                    url = f"http://{request.host}:{request.port}/inference_zero_shot"
                    success_flag = generate_audio(
                        url=url,
                        text=line["line"],
                        prompt_text=cast_info["prompt_text"],
                        prompt_wav=cast_info["prompt_wav"],
                        output_path=output_path
                    )

                current_time = self._update_progress_and_subtitles(
                    success_flag=success_flag,
                    output_path=output_path,
                    character=character,
                    line=line,
                    current_time=current_time,
                    progress_data=progress_data,
                    subtitle_data=subtitle_data,
                    progress_file=progress_file
                )
            else:
                current_time = self._handle_narrator_fallback(
                    request=request,
                    cast_dict=cast_dict,
                    line=line,
                    i=i,
                    output_dir=output_dir,
                    file_list=file_list,
                    current_time=current_time,
                    subtitle_data=subtitle_data,
                    progress_data=progress_data,
                    progress_file=progress_file
                )

        self._create_final_output(
            output_dir=output_dir,
            file_list=file_list,
            subtitle_data=subtitle_data,
            request=request
        )

    def _update_progress_and_subtitles(
        self, 
        success_flag: bool,
        output_path: Path,
        character: str,
        line: dict,
        current_time: float,
        progress_data: ProgressData,
        subtitle_data: list,
        progress_file: Path
    ) -> float:
        """Update progress data and subtitle information after generating an audio file"""
        if success_flag:
            progress_data.success_count += 1
            audio_info = sf.info(output_path)
            duration = audio_info.duration
            subtitle_data.append({
                'index': len(subtitle_data) + 1,
                'start': current_time,
                'end': current_time + duration,
                'character': character,
                'text': line["line"]
            })
            current_time += duration
        else:
            progress_data.failed_count += 1
        
        # Update progress
        progress_data.processed_lines += 1
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data.model_dump(), f)
            
        return current_time

    def _handle_narrator_fallback(
        self,
        request: VoiceRequest,
        cast_dict: dict,
        line: dict,
        i: int,
        output_dir: Path,
        file_list: list,
        current_time: float,
        subtitle_data: list,
        progress_data: ProgressData,
        progress_file: Path
    ) -> float:
        """Handle cases where character is not found in cast_dict by using narrator"""
        logger.warning(f"Character {line['character']} not found in cast_dict. Defaulting to normal instruct by the narrator.")
        cast_info = cast_dict["Narrator"]
        output_path = output_dir / f"{i:05d}.wav"
        file_list.append(output_path)
        instruct_text = line["instruct"]
        
        success_flag = False
        if instruct_text != "normal":
            url = f"http://{request.host}:{request.port}/inference_instruct2"
            success_flag = generate_audio_instruct(
                url=url,
                text=line["line"],
                instruct_text=instruct_text,
                prompt_wav=cast_info["prompt_wav"],
                output_path=output_path
            )
        else:
            url = f"http://{request.host}:{request.port}/inference_zero_shot"
            success_flag = generate_audio(
                url=url,
                text=line["line"],
                prompt_text=cast_info["prompt_text"],
                prompt_wav=cast_info["prompt_wav"],
                output_path=output_path
            )
        
        if success_flag:
            progress_data.narrator_success_count += 1
            audio_info = sf.info(output_path)
            duration = audio_info.duration
            subtitle_data.append({
                'index': len(subtitle_data) + 1,
                'start': current_time,
                'end': current_time + duration,
                'character': "Narrator",
                'text': line["line"]
            })
            current_time += duration
        else:
            progress_data.narrator_failed_count += 1
        
        # Update progress
        progress_data.processed_lines += 1
        with open(progress_file, 'w', encoding='utf-8') as f:

            json.dump(progress_data.model_dump(), f)
            
        return current_time

    def _create_final_output(
        self,
        output_dir: Path,
        file_list: list,
        subtitle_data: list,
        request: VoiceRequest
    ):
        """Create final output files including audio and subtitles"""
        # Create file list for ffmpeg
        with open(output_dir / "files.txt", "w", encoding='utf-8') as f:
            for file_path in file_list:
                if file_path.exists():  # Only include successfully generated files
                    f.write(f"file '{file_path.name}'\n")
        
        # Generate M4A file
        subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", str(output_dir / "files.txt"),
            "-c:a", "aac", "-b:a", "256k",
            str(output_dir / "final_output.m4a")
        ])
        
        # Generate SRT subtitle file
        with open(output_dir / "subtitles.srt", "w", encoding='utf-8') as f:
            for entry in subtitle_data:
                start_time = "{:02d}:{:02d}:{:02d},{:03d}".format(
                    int(entry['start'] // 3600),
                    int((entry['start'] % 3600) // 60),
                    int(entry['start'] % 60),
                    int((entry['start'] * 1000) % 1000)
                )
                end_time = "{:02d}:{:02d}:{:02d},{:03d}".format(
                    int(entry['end'] // 3600),
                    int((entry['end'] % 3600) // 60),
                    int(entry['end'] % 60),
                    int((entry['end'] * 1000) % 1000)
                )
                
                f.write(f"{entry['index']}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{entry['character']}: {entry['text']}\n\n")
        
        # Create MP4 with subtitles if requested
        if request.save_mp4_with_subtitles:
            logger.info("Creating MP4 with embedded subtitles...")
            try:
                duration = get_audio_duration(output_dir / "final_output.m4a")
                
                # Create black video
                subprocess.run([
                    "ffmpeg", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:d={duration}",
                    "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                    str(output_dir / "temp_video.mp4")
                ])
                
                # Add audio and subtitles
                subprocess.run([
                    "ffmpeg", "-i", str(output_dir / "temp_video.mp4"),
                    "-i", str(output_dir / "final_output.m4a"),
                    "-vf", f"subtitles={output_dir / 'subtitles.srt'}",
                    "-c:a", "copy",
                    "-c:v", "libx264", "-crf", "23",
                    str(output_dir / "final_output.mp4")
                ])
                
                # Clean up temporary video file
                (output_dir / "temp_video.mp4").unlink()
                
            except Exception as e:
                logger.error(f"Error creating MP4 with subtitles: {e}")

