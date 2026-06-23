import os
from voice_agent_complete import VoiceAgent, process_voice_command

def main():
    print("Testing VoiceAgent functionality...")
    agent = VoiceAgent()

    # Test real-time microphone input
    print("\n--- Testing real-time microphone input ---")
    result = process_voice_command()
    print(f"Transcription: {result['transcription']}")
    print(f"Intent: {result['intent']}")
    print(f"Response: {result['response']}")
    if result['audio_response_path']:
        print(f"Audio response saved to: {result['audio_response_path']}")
        # You might want to play the audio here for a full demo
        # import pygame
        # pygame.mixer.init()
        # pygame.mixer.music.load(result['audio_response_path'])
        # pygame.mixer.music.play()
        # while pygame.mixer.music.get_busy():
        #     pygame.time.Clock().tick(10)
        # os.remove(result['audio_response_path']) # Clean up temp file
    else:
        print("No audio response generated.")

    # You can add tests for file processing here if you have a sample audio file
    # print("\n--- Testing audio file processing ---")
    # # Create a dummy audio file for testing (requires gTTS to generate)
    # dummy_audio_path = agent.text_to_speech("Hello, this is a test audio file.", output_path="test_audio.mp3")
    # if dummy_audio_path:
    #     print(f"Dummy audio file created at: {dummy_audio_path}")
    #     file_result = process_voice_command(audio_file=dummy_audio_path)
    #     print(f"File Transcription: {file_result['transcription']}")
    #     print(f"File Intent: {file_result['intent']}")
    #     print(f"File Response: {file_result['response']}")
    #     os.remove(dummy_audio_path) # Clean up dummy audio file
    # else:
    #     print("Failed to create dummy audio file for testing.")


if __name__ == "__main__":
    main()
