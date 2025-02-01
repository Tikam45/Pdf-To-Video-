import pdfplumber
from transformers import pipeline
import os
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
from moviepy.editor import concatenate_videoclips, TextClip, AudioFileClip, CompositeVideoClip, ImageClip
from gtts import gTTS
import google.generativeai as genai
import fitz  # PyMuPDF
GOOGLE_API_KEY = ''


user_pdf_path = "C:/Users/91805/Downloads/ternary.pdf"

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):  # Use a correct parameter name
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()  # Extract text from each page
    return text


pdf_path = user_pdf_path
text = extract_text_from_pdf(pdf_path)

def extract_images_from_pdf(pdf_path, output_folder):
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    
    # Make the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    image_paths = []
    
    # Iterate over all the pages in the PDF
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        
        # Extract all images on the page
        image_list = page.get_images(full=True)
        
        for img_index, image in enumerate(image_list):
            xref = image[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Save the image as a JPEG file
            image_filename = f"page_{page_num + 1}_img_{img_index + 1}.jpg"
            image_path = os.path.join(output_folder, image_filename)
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
            image_paths.append(image_path)
            print(f"Image saved at {image_path}")
    
    return image_paths

# Example usage
pdf_path = user_pdf_path  # Your PDF file path
output_folder = "./extracted_images"  # Folder to save the extracted images

# Extract images from the PDF
image_paths = extract_images_from_pdf(pdf_path, output_folder)

# List of image paths saved
print("Images extracted and saved to:")
for image_path in image_paths:
    print(image_path)




# summarise
# Helper function to split text into smaller chunks
# def split_text(text, max_length=1024):
#     # Split text into sentences
#     sentences = text.split(". ")
#     chunks = []
#     current_chunk = ""

#     for sentence in sentences:
#         if len(current_chunk + sentence) < max_length:
#             current_chunk += sentence + ". "
#         else:
#             chunks.append(current_chunk.strip())
#             current_chunk = sentence + ". "

#     if current_chunk:
#         chunks.append(current_chunk.strip())
#     return chunks


# summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
# summaries = []
# chunks = split_text(text)
# print(chunks)
# for chunk in chunks:
#     summary = summarizer(chunk, max_length=50, min_length=1, do_sample=False)
#     print(summary)
#     summaries.append(summary[0]['summary_text'])

# final_summary = " ".join(summaries)
# print("text", final_summary)
# text = final_summary


genai.configure(api_key=GOOGLE_API_KEY)

# Define the summarization function
def summarize_text(text, model="gemini-pro"):
    """
    Sends a request to the Gemini API to summarize the given text.

    Args:
        text (str): The text to be summarized.
        model (str): The model to use (default: "gemini-pro").

    Returns:
        str: The summarized text.
    """
    try:
        response = genai.GenerativeModel(model).generate_content(
            f"Summarize the following text:\n\n{text}"
        )
        return response.text.strip() if response.text else "No summary generated."
    except Exception as e:
        return f"Error: {e}"
    
summary = summarize_text(text)
print("Summary:", summary)
text = summary

# Split the text into meaningful chunks (adjust as needed)
text_parts = [part.strip() for part in text.split(". ") if part.strip()]

# Temporary directory to store audio files
audio_dir = "audio_files"
os.makedirs(audio_dir, exist_ok=True)

# Store clips
text_clips = []
print("text", text)
for i, part in enumerate(text_parts):
    print("part", part)
    audio_path = os.path.join(audio_dir, f"audio_{i}.mp3")
    tts = gTTS(part)
    tts.save(audio_path)
    
    audio_clip = AudioFileClip(audio_path)
    words = part.split()

    word_clips = []
    word_start = 0

    cnt = 0
    rendering_text = ""
    for word in words:
        if cnt >5:
            rendering_text =rendering_text + """\n""" + word
            cnt = 1
        else: 
            rendering_text =rendering_text + " " + word
            cnt+=1
        # Generate each word as an individual frame with more attributes
        word_clip = TextClip(
            rendering_text,
            fontsize=60,                  # Font size (reduced for better fit)
            color='white',                # Text color
            bg_color='black',             # Background color
            size=(1280, 720),             # Frame size (ensure the text fits the screen)
            font="Arial-Bold",            # Font type
            stroke_color="yellow",       # Stroke color (outline)
            stroke_width=2,               # Stroke thickness
            align="center",               # Text alignment
            kerning=5,                    # Space between letters
            interline=10,                 # Space between lines (for multiline text)
            method='caption',             # Text wrapping method (caption handles multi-line)
        ).set_start(word_start).set_duration(0.5)  # 0.5 sec per word

        word_clips.append(word_clip)
        word_start += 0.5  # Next word starts after 0.5 sec

    # Stack the word clips sequentially
    text_clip = CompositeVideoClip(word_clips, size=(1280, 720)).set_duration(audio_clip.duration)


    # Attach audio to the text clip
    # text_clip = text_clip.set_audio(audio_clip)
    print(text_clip)

    # Store the final text clip with audio
    text_clips.append(text_clip)


# Step 3: Concatenate all clips into one video
# print("hello")
video = concatenate_videoclips(text_clips, method="compose")

image_files = [os.path.join("extracted_images", img) for img in os.listdir("extracted_images") if img.endswith(('png', 'jpg', 'jpeg'))]
image_clips = []
for idx, img_path in enumerate(image_files):
    image_clip = ImageClip(img_path)
    image_clip = image_clip.set_duration(5)  # Set duration to 5 seconds
    image_clip = image_clip.set_start(idx * 5)  # The image will appear after 5 seconds intervals
    image_clip = image_clip.set_position("center")  # You can adjust position like ("center", (100, 100), etc.)
    image_clip = image_clip.resize(height=200)  # Optional resize image to fit the video

    # Add the image clip to the list
    image_clips.append(image_clip)

# Combine the video with the image clips
final_video = concatenate_videoclips([video] + image_clips)
output_path = "final_video_with_audio9.mp4"
a_path = os.path.join(audio_dir, f"audio_8.mp3")
tts = gTTS(summary)
tts.save(a_path)
audio = AudioFileClip(a_path)

final_video = final_video.set_audio(audio)
final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

print(f"Video created and saved at: {output_path}")
# Optional: Clean up generated audio files
# for file in os.listdir(audio_dir):
#     os.remove(os.path.join(audio_dir, file))
# os.rmdir(audio_dir)

print(f"Video created and saved at: {output_path}")
