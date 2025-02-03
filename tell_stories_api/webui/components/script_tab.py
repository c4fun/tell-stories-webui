import gradio as gr
import requests
import json

def format_status_message(response):
    if "error" in response:
        return f"❌ Error: {response['error']}"
    
    status_emoji = "❌"
    if response["status"] == "success" or response["status"] == "completed":
        status_emoji = "✅"
    elif response["status"] == "splitting_story":
        status_emoji = "🔄"
    elif response["status"] == "processing_lines":
        status_emoji = "⏳"
    else:
        status_emoji = "❌"
    
    message = f"{status_emoji} Status: {response['status']}\n"
    if response.get("output_path"):
        message += f"📁 Output: {response['output_path']}"
    return message

def create_script_tab(api_base_url, process_id):
    def generate_plot(story_path, text_input, input_method, process_id, book_id=None):
        try:
            data = {"story_path": story_path} if input_method == "file" else {"text_input": text_input}
            if book_id:
                data["book_id"] = book_id
            response = requests.post(
                f"{api_base_url}/script/{process_id}/plot",
                json=data
            )
            result = response.json()
            return format_status_message(result), result
        except Exception as e:
            error_result = {"error": str(e)}
            return format_status_message(error_result), error_result

    def generate_cast(process_id, book_id=None):
        try:
            data = {}
            if book_id:
                data["book_id"] = book_id
            response = requests.post(
                f"{api_base_url}/script/{process_id}/cast",
                json=data
            )
            result = response.json()
            return format_status_message(result), result
        except Exception as e:
            error_result = {"error": str(e)}
            return format_status_message(error_result), error_result

    def generate_lines(process_id, split_dialogue=True, all_caps_to_proper=True):
        try:
            response = requests.post(
                f"{api_base_url}/script/{process_id}/lines",
                json={
                    "split_dialogue": split_dialogue,
                    "all_caps_to_proper": all_caps_to_proper
                }
            )
            result = response.json()
            return format_status_message(result), result
        except Exception as e:
            error_result = {"error": str(e)}
            return format_status_message(error_result), error_result

    def get_script_progress(process_id):
        try:
            response = requests.get(f"{api_base_url}/script/{process_id}/lines/progress")
            result = response.json()
            return format_status_message(result), result
        except Exception as e:
            error_result = {"error": str(e)}
            return format_status_message(error_result), error_result

    with gr.Tab("Script Generation"):
        book_id = gr.Textbox(
            label="Book ID",
            placeholder="Optional: Enter book ID if this is a chapter of a book",
            value=""
        )
        with gr.Column():
            # Plot Generation Section
            with gr.Group():
                gr.Markdown("### 1. Plot Generation")
                with gr.Row():
                    input_method = gr.Radio(
                        choices=["file", "text"],
                        value="file",
                        label="Input Method"
                    )
                file_input = gr.Textbox(
                    label="Story Path",
                    value="data/story/short_story/Hills Like White Elephants by Ernest Hemingway.txt",
                    visible=True
                )
                text_input = gr.TextArea(
                    label="Story Text",
                    placeholder="Enter your story here...",
                    lines=10,
                    visible=False
                )
                plot_btn = gr.Button(
                    "Generate Plot",
                    variant="primary",
                    scale=3,
                    min_width=120
                )
                with gr.Group():
                    plot_status_md = gr.Markdown(label="Status", value="")
                    with gr.Accordion("Details", open=True):
                        plot_status = gr.JSON(label="Plot Status")

            # Cast Generation Section
            with gr.Group():
                gr.Markdown("### 2. Cast Generation")
                cast_btn = gr.Button(
                    "Generate Cast",
                    variant="primary",
                    scale=3,
                    min_width=120
                )
                with gr.Group():
                    cast_status_md = gr.Markdown(label="Status", value="")
                    with gr.Accordion("Details", open=True):
                        cast_status = gr.JSON(label="Cast Status")

            # Lines Generation Section
            with gr.Group():
                gr.Markdown("### 3. Lines Generation")
                with gr.Row():
                    with gr.Column(scale=1):
                        lines_btn = gr.Button(
                            "Generate Lines",
                            variant="primary",
                            scale=3,
                            min_width=120
                        )
                        with gr.Group():
                            lines_status_md = gr.Markdown(label="Status", value="")
                            with gr.Accordion("Details", open=True):
                                lines_status = gr.JSON(label="Lines Status")
                        
                    with gr.Column(scale=1, min_width=50):
                        progress_btn = gr.Button(
                            "Get Lines Progress",
                            variant="huggingface",
                            scale=3,
                            min_width=120
                        )
                        with gr.Group():
                            progress_status_md = gr.Markdown(label="Status", value="")
                            with gr.Accordion("Details", open=True):
                                progress_status = gr.JSON(label="Progress Status")

        def update_input_visibility(choice):
            return {
                file_input: gr.update(visible=choice == "file"),
                text_input: gr.update(visible=choice == "text")
            }

        # Wire up all events within the component
        input_method.change(
            fn=update_input_visibility,
            inputs=input_method,
            outputs=[file_input, text_input]
        )

        plot_btn.click(
            fn=lambda s, t, m, p, b: generate_plot(s, t, m, p, b),
            inputs=[file_input, text_input, input_method, process_id, book_id],
            outputs=[plot_status_md, plot_status]
        )

        cast_btn.click(
            fn=lambda p, b: generate_cast(p, b),
            inputs=[process_id, book_id],
            outputs=[cast_status_md, cast_status]
        )

        lines_btn.click(
            fn=lambda p: generate_lines(p),
            inputs=[process_id],
            outputs=[lines_status_md, lines_status]
        )

        progress_btn.click(
            fn=lambda p: get_script_progress(p),
            inputs=[process_id],
            outputs=[progress_status_md, progress_status]
        )

        return {
            "components": [
                plot_btn, cast_btn, lines_btn, progress_btn,
                file_input, text_input, input_method, book_id,
                plot_status_md, plot_status, cast_status_md, cast_status,
                lines_status_md, lines_status, progress_status_md, progress_status
            ]
        } 