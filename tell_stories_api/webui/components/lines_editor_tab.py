import gradio as gr
import json
from pathlib import Path
import pandas as pd
from tell_stories_api.logs import logger

def create_lines_editor_tab(process_id):
    def update_lines_container(pid):
        try:
            file_path = Path(f"data/process/{pid}/lines.json")
            if not file_path.exists():
                logger.error(f"Lines file not found: {file_path}")
                return None, {"error": "Lines file not found"}
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                lines = data.get("lines", [])
            
            # Convert lines to dataframe format
            df_data = []
            for line in lines:
                df_data.append([
                    line.get("character", ""),
                    line.get("instruct", ""),
                    line.get("line", "")
                ])
            
            return df_data, {"status": "success", "message": f"Loaded {len(lines)} lines"}
            
        except Exception as e:
            logger.error(f"Error loading lines: {str(e)}")
            return None, {"error": str(e)}
    
    def save_changes(pid, df_data):
        try:
            if df_data is None or len(df_data) == 0:
                return {"error": "No data to save"}
            
            # Convert DataFrame data to list format
            if isinstance(df_data, str):
                df_data = json.loads(df_data)
            
            # Skip the header row and process actual data
            data = df_data['data'] if isinstance(df_data, dict) else df_data
            logger.info(f"Data: {data}")
            logger.info(f"len(data): {len(data)}")
            df_filtered = data.dropna(how='any').replace('', pd.NA).dropna(how='any')
            records_list = df_filtered.to_dict(orient='records')
            
            lines_data = {"lines": records_list}
            file_path = Path(f"data/process/{pid}/lines.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(lines_data, f, indent=2, ensure_ascii=False)
            return {"status": "success", "message": f"Saved {len(records_list)} lines successfully"}
        except Exception as e:
            logger.error(f"Error saving lines: {str(e)}")
            return {"error": str(e)}

    with gr.Tab("Lines Editor(Advanced with Emotions)"):
        with gr.Row():
            load_btn = gr.Button("Load Lines", variant="primary", scale=3, min_width=120)
            save_btn = gr.Button("Save Changes", variant="primary", scale=3, min_width=120)
        
        # Container for line components
        lines_container = gr.Dataframe(
            headers=["character", "instruct", "line"],
            datatype=["str", "str", "str"],
            interactive=True,
            label="Lines",
            wrap=True,
            max_height=1024
        )
        status_json = gr.JSON(label="Status")
        
        # Wire up all events within the component
        load_btn.click(
            fn=lambda p: update_lines_container(p),
            inputs=[process_id],
            outputs=[lines_container, status_json]
        )
        
        save_btn.click(
            fn=lambda p, d: save_changes(p, d),
            inputs=[process_id, lines_container],
            outputs=[status_json]
        )
        
        return {
            "components": [load_btn, save_btn, lines_container, status_json]
        } 