#  Rizzler AI


Rizzler AI is a content creation tool that analyzes a user's raw photos and audio clips to identify currently trending sounds, filters, and formats on TikTok. It then automatically edits the user's media into a new, polished AI-generated reel that mirrors the viral trend, making it easy for anyone to hop on the bandwagon and create content with high viral potential.



Tech stack used 
Python, FastAPI, Firebase, Google Cloud, ElevenLabs, Nanobanana, FAL APIs, React, Vite 


## Setup Instructions
1. Clone the repository:
   ```bash
   git clone
    ```
2. Navigate to the project directory:
    ```bash     
    cd video_agent
     ```
3. Install the required dependencies:
    ```bash 
    pip install -r requirements.txt
     ```
4. Set up environment variables:
    - Create a `.env` file in the `backend` directory.              
    - Add the necessary environment variables as specified in the `.env.example` file.
5. Run the FastAPI server:
    ```bash
    uvicorn backend.main:app --reload
    ```
6. Access the application:
    - Open your web browser and navigate to `http://localhost:8000` to access the application.          
## Features
- **Automated Trend Analysis**: Analyzes user media to identify trending TikTok sounds and formats.
- **AI-Powered Editing**: Utilizes advanced AI algorithms to edit raw photos and audio clips into polished reels.
- **User-Friendly Interface**: Simple and intuitive interface for easy content creation.
- **High Viral Potential**: Creates content that aligns with current trends to maximize engagement.
## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.


This was produced in a hackathon setting, so please excuse any rough edges or incomplete features. We welcome feedback and suggestions for improvement!


The character_agent folder contains the code for generating character voices using ElevenLabs and Nanobanana APIs. The video_agent folder contains the backend code for processing videos and integrating with the character agent. The frontend folder contains the React application for user interaction. The character_agent and video_agent communicate via RESTful APIs where the character_agent takes input from a user on their desired character voice and generates audio files that are then used by the video_agent to create the final video output.