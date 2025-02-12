# TellStories.AI 📖🎭🤖

**Dynamic Voice Actor Assignment and Emotional Narration for Realistic Story Play**

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)


Transform text stories into immersive audio experiences with AI-powered multiple characters and variety of emotions in voice generation. Bring stories to life 🎙️✨

Watch the Demo on YouTube:

[![Watch the Demo](https://img.youtube.com/vi/Du_zH802FIA/hqdefault.jpg)](https://youtu.be/Du_zH802FIA "Watch the Demo")

## Features ✨

- **Automatic Plot Analysis** - LLM-powered story structure decomposition
- **Character-Voice Mapping** - Intelligent voice actor assignment per character
- **Emotional Narration** - Context-aware emotion instructions for each line
- **Multi-Voice Synthesis** - Parallel TTS generation with voice consistency
- **Open Source** - Community-driven improvement of narration quality
- **GUI Interface** - Easy-to-use interface for story annotation and narration

## Installation 🚀

TellStories.AI can generate cast and script with LLM.

TellStories.AI currently relies on CosyVoice 2 service to Generate Voice. If you want to generate voices; it is highly recommended to install CosyVoice 2 first on a separate folder first.


### Install TellStories.AI WebUI

#### 1. Download the repo and install dependencies.

```bash
git clone https://github.com/tell-stories-ai/tell-stories-webui.git
cd tell-stories-webui
```

Suggested: Use a separate conda env.
```bash
conda create -n tellstories -y python=3.10
conda activate tellstories
```

Install dependencies:
```bash
pip install -r requirements.txt
```

#### 2. `.env` configuration:

```bash
cp .env.example .env
```
1. Fill in your Deepseek API token in the `.env` file.
2. Fill in your CosyVoice 2 service port in the `.env` file. 

Example `.env` file:
```bash

# Model Selection and Fallback Configuration
PRIMARY_MODEL="openrouter"  # Options: deepseek, qwen, openrouter
# Comma-separated order of fallback. If primary model is not available, the fallback models will be tried in the order.
MODEL_FALLBACK_ORDER="openrouter,deepseek,qwen"

# Model configuration
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY="your_deepseek_api_key"
# Option: Use OpenRouterAI
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
OPENROUTER_API_KEY="your_openrouter_api_key"
# Option: Use Qwen model
DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_API_KEY="your_dashscope_api_key"

# Voice Generate Service
# CosyVoice 2 service; running locally
COSYVOICE2_HOST="127.0.0.1"
COSYVOICE2_PORT="50000"

MAX_TOKENS_PER_SPLIT=4000
```

#### 3. Run the service:

TellStories.AI WebUI runs on port 8000. If you want to change the port, please also change it in the `.env` file.

```bash
python main.py
```

#### 4. Run TellStories.AI WebUI
- The webUI will run on `http://localhost:8000/ui/`
- The API swagger will run on `http://localhost:8000/docs/`

Now TellStories.AI WebUI is ready and can run script generation. But if want voice generation, you need to install CosyVoice2.

### Install CosyVoice2 for Voice Generation

Prerequisites: ffmpeg is required and should be already in path.

#### 1. Clone the repo.

Here we use fastapi-cosyvoice2 branch in my own fork since the original repo does not support instruct2 yet.

```bash
git clone --single-branch --branch fastapi-cosyvoice2 https://github.com/c4fun/CosyVoice.git
cd CosyVoice
git submodule update --init --recursive
```

#### 2. Create a separate Conda env:

```bash
conda create -n cosyvoice -y python=3.10
conda activate cosyvoice
# pynini is required by WeTextProcessing, use conda to install it as it can be executed on all platform.
conda install -y -c conda-forge pynini==2.1.5
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

# If you encounter sox compatibility issues
# ubuntu
sudo apt-get install sox libsox-dev
# centos
sudo yum install sox sox-devel
```

#### 3. Model download:

TellStories.AI currently only relies on CosyVoice2-0.5B, so this is the only weight that needed.

```bash
# download through SDK
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
```

```bash
# download through git, please ensure git lfs is installed
mkdir -p pretrained_models
git clone https://www.modelscope.cn/iic/CosyVoice2-0.5B.git pretrained_models/CosyVoice2-0.5B
```

#### 4. Install ttsfrd package for better text normalization performance. (Not Applicable for Windows)

Notice that this step is not necessary. If you do not install ttsfrd package, we will use WeTextProcessing by default.

First, download the ttsfrd package.
```bash
# download through SDK
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice-ttsfrd', local_dir='pretrained_models/CosyVoice-ttsfrd')
```

Then, install the dependencies.
```bash
cd pretrained_models/CosyVoice-ttsfrd/
unzip resource.zip -d .
pip install ttsfrd_dependency-0.1-py3-none-any.whl
pip install ttsfrd-0.4.2-cp310-cp310-linux_x86_64.whl
```

#### 5. Run CosyVoice 2 service:

```bash
python runtime/python/fastapi/server.py
```

## Usage 🎬

The process ID is defaultly a UUID which will be generated automatically each time you start the service. It is a **required field** for each step.

It is recommended to input your own process ID to remember better.

### 1. Script Generation

1. Prepare your story in plain text. And click the "Generate Plot" button. Wait for it to finish.
2. Click "Generate Cast" button. Wait for it to finish.
3. Click "Generate Lines" button. And if it's successful, Click on the "Get Lines Progress" to see if it is finished.

### 2. Voice Generation
1. (Optional) Manual Cast Selection. Select you own cast by "Load Cast" -> Click on the "Voice Actor" you want to Change -> Select a new VA -> (Optional) Generate Sample Voice -> "Save Cast".
2. Click "Generate Voice Cast" button, we'll generate a `voice_cast.json` so that to call the next step.
3. Click "Generate Voice" button. And if it's successful, Click on the "Get Voice Progress" to see if it is finished. The progress of current files count vs total files count will be shown.
4. Click "Open Output Folder" button to open the output folder and listen to the voice generated. The final result will be a concated audio called `final_output.m4a`.

### 3. (Advanced) Lines Editor
After the "Generate Lines" in script generation, you can edit the lines by clicking the "Line Editor" tab. This process is optional; and it's usually done before the voice generation.

1. Click "Load Lines" button to load the lines.
2. Edit the lines. Remember that all columns should be filled in order to save this line. On the other hand, you may just ignore a row when saving by ignoring one of its line.
3. Click "Save Changes" button to save the lines.

### 4. (Advanced) Voice Admin

We provide a voice admin page to help you manage your voice actors. 

##### Voice Clone

You may use a 3s-10s voice clip to create a new voice actor/actress. These voices can be used in the voice generation step.

1. Click "Voice Admin" tab to open the voice admin page.
2. Upload the reference voice. It could be your own voice or an existing voice actor's voice.
3. Fill in the correct text for the reference voice.
4. Fill in the corresponding info.
5. Click "Create Voice Action" button to save it.
6. Restart the service to load the new voice actor in the "Voice Generation" step.

## Roadmap 🗺️

Big hairy goal: Generate a full story video with voice, background music, illustrative images, and illustrative video in one click. All with open source technologies.

1. Support for multiple TTS engines (Kokoro TTS, etc.).
2. Better Gradio Interface.
3. Add background music generation based on open source like [YuE](https://github.com/multimodal-art-projection/YuE).

## Acknowledgments 🏆

- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) for the emotion-aware TTS engine.
- [DeepSeek](https://www.deepseek.com/) for the powerful LLM.
- [FastAPI](https://fastapi.tiangolo.com/) for the web service framework.
- [Gradio](https://www.gradio.app/) for the webUI framework.

## Contributing 🤝

We welcome contributions from the community! Please feel free to submit a PR.

---
Bring stories to life 🎙️✨
